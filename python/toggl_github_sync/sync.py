"""Sync module for toggl_github_sync."""

import calendar
import logging
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import difflib

import pytz
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from toggl_github_sync.api.github import GitHubApiClient
from toggl_github_sync.api.toggl import TogglApiClient
from toggl_github_sync.config import Config

logger = logging.getLogger(__name__)


def sync_toggl_to_github(config: Config, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> bool:
    """Sync Toggl time entries to GitHub worklog.

    Args:
        config: Application configuration
        start_date: Start date for time entries (default: start of current day in configured timezone)
        end_date: End date for time entries (default: end of current day in configured timezone)

    Returns:
        True if sync was successful
    """
    try:
        # Initialize API clients
        toggl_client = TogglApiClient(config)
        github_client = GitHubApiClient(config)

        # Get timezone
        timezone = pytz.timezone(config.timezone)

        # If no dates provided, use today
        if start_date is None and end_date is None:
            start_date = datetime.now(timezone)
            end_date = start_date

        # Ensure dates are in the configured timezone
        if start_date.tzinfo is None:
            start_date = timezone.localize(start_date)
        if end_date.tzinfo is None:
            end_date = timezone.localize(end_date)

        # Get current worklog content
        worklog_content, sha = github_client.get_worklog_content()
        original_worklog_content = worklog_content

        # Process each day in the range
        current_date = start_date.date()
        end_date_date = end_date.date()
        success = True

        while current_date <= end_date_date:
            # Get start and end of day in configured timezone
            day_start = timezone.localize(datetime.combine(current_date, datetime.min.time()))
            day_end = timezone.localize(datetime.combine(current_date, datetime.max.time()))

            # Get time entries for this day
            entries = toggl_client.get_time_entries(day_start, day_end)

            # Calculate total hours
            total_hours = toggl_client.calculate_daily_hours(entries)

            # Format as "X.Yh" or "X.Yh+" if there's a running entry for today
            hours_str = f"{total_hours}h"
            current_entry = toggl_client.get_current_time_entry()
            if current_entry:
                # Check if the current entry is for today
                entry_start = datetime.fromisoformat(current_entry["start"].replace("Z", "+00:00"))
                entry_start = entry_start.astimezone(timezone)
                if entry_start.date() == current_date:
                    hours_str += "+"

            # Get descriptions from entries and join with periods
            descriptions = []
            for entry in entries:
                if entry.get("description"):
                    desc = entry["description"].strip()
                    if desc:
                        descriptions.append(desc)
                    else:
                        descriptions.append("[REDACTED - to be updated soon]")
                else:
                    descriptions.append("[REDACTED - to be updated soon]")
            
            # Deduplicate descriptions while preserving order
            unique_descriptions = []
            for desc in descriptions:
                # Check if this description is similar to any existing one
                is_similar = False
                for existing in unique_descriptions:
                    # Calculate similarity ratio (0.0 to 1.0)
                    similarity = difflib.SequenceMatcher(None, desc, existing).ratio()
                    # If similarity is above threshold, consider it a duplicate
                    if similarity > 0.85:  # 85% similarity threshold
                        is_similar = True
                        break
                
                if not is_similar:
                    unique_descriptions.append(desc)
            
            description_text = ". ".join(unique_descriptions)
            if description_text and not description_text.endswith("."):
                description_text += "."

            # Format the worklog entry
            day_name = calendar.day_name[current_date.weekday()][:3]  # Mon, Tue, etc.
            date_str = current_date.strftime("%Y-%-m-%-d")  # 2025-4-9 format

            new_entry = f"{date_str} {day_name} ({hours_str}): {description_text}"

            # Check if there's already an entry for this date
            existing_entry = github_client.find_entry_for_date(worklog_content, day_start)

            if existing_entry:
                # Update existing entry
                entry, start_index, end_index = existing_entry
                worklog_content = (
                    worklog_content[:start_index] + new_entry + worklog_content[end_index:]
                )
            else:
                # Add new entry at the top
                if worklog_content.startswith("# "):
                    # If the file starts with a title, add after the title
                    title_end = worklog_content.find("\n") + 1
                    worklog_content = (
                        worklog_content[:title_end]
                        + "\n"
                        + new_entry
                        + "\n\n"
                        + worklog_content[title_end:]
                    )
                else:
                    # Otherwise, add at the very top
                    worklog_content = new_entry + "\n\n" + worklog_content

            logger.info(f"Processed entry for {date_str}: {new_entry}")

            # Move to next day
            current_date += timedelta(days=1)

        # Check if there are any changes before updating
        if worklog_content == original_worklog_content:
            logger.info("No changes detected, skipping GitHub update")
            return True

        # Update the worklog file with all changes
        success = github_client.update_worklog(worklog_content, sha)

        logger.info("Sync completed successfully")
        return success

    except Exception as e:
        logger.error(f"Error syncing Toggl to GitHub: {e}")

        # Send email notification if configured
        if (
            config.sendgrid_api_key
            and config.notification_email_from
            and config.notification_email_to
        ):
            send_error_notification(config, str(e))

        return False


def send_error_notification(config: Config, error_message: str) -> None:
    """Send error notification email.

    Args:
        config: Application configuration
        error_message: Error message to include in the email
    """
    try:
        message = Mail(
            from_email=config.notification_email_from,
            to_emails=config.notification_email_to,
            subject="Toggl GitHub Sync Error",
            html_content=f"""
            <p>An error occurred while syncing Toggl time entries to GitHub:</p>
            <pre>{error_message}</pre>
            <p>Please check the logs for more details.</p>
            """,
        )

        sg = SendGridAPIClient(api_key=config.sendgrid_api_key)
        sg.send(message)

        logger.info(f"Error notification sent to {config.notification_email_to}")

    except Exception as e:
        logger.error(f"Error sending notification email: {e}")
