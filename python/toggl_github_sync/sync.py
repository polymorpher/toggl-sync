"""Sync module for toggl_github_sync."""

import calendar
import logging
import ssl
import re
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

        # Get all time entries for the entire range at once
        all_entries = toggl_client.get_time_entries(start_date, end_date)

        # Process each day in the range
        current_date = end_date.date()
        start_date_date = start_date.date()
        success = True

        while current_date >= start_date_date:
            # Get start and end of day in configured timezone
            day_start = timezone.localize(datetime.combine(current_date, datetime.min.time()))
            day_end = timezone.localize(datetime.combine(current_date, datetime.max.time()))

            # Filter entries for the current day from the full list
            entries_for_day = [
                e for e in all_entries 
                if day_start <= datetime.fromisoformat(e["start"].replace("Z", "+00:00")).astimezone(timezone) <= day_end
            ]

            # Calculate total hours
            total_hours = toggl_client.calculate_daily_hours(entries_for_day)

            # Skip days with 0 hours
            if total_hours == 0:
                logger.info(f"Skipping {current_date} as no hours were tracked")
                current_date -= timedelta(days=1)
                continue

            # Format as "X.Yh" or "X.Yh+" if there's a running entry for today
            hours_str = f"{total_hours}h"
            current_entry = toggl_client.get_current_time_entry()
            if current_entry:
                # Check if the current entry is for today
                entry_start = datetime.fromisoformat(current_entry["start"])
                entry_start = entry_start.astimezone(timezone)
                if entry_start.date() == current_date:
                    hours_str += "+"

            # Get descriptions from entries and join with periods
            descriptions = []
            for entry in entries_for_day:
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
            if not description_text.strip():
                description_text = "[To be updated]"
            elif not description_text.endswith("."):
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
                # Add new entry at the top, after any title
                if worklog_content.startswith("# "):
                    # If the file starts with a title, add after the title
                    title_end = worklog_content.find("\n") + 1
                    worklog_content = (
                        worklog_content[:title_end]
                        + "\n"
                        + new_entry
                        + "\n"
                        + worklog_content[title_end:]
                    )
                else:
                    # Otherwise, add at the very top
                    worklog_content = new_entry + "\n" + worklog_content

            logger.info(f"Processed entry for {date_str}: {new_entry}")

            # Move to previous day
            current_date -= timedelta(days=1)

        # Check if there are any changes before updating
        if worklog_content == original_worklog_content:
            logger.info("No changes detected, skipping GitHub update")
            return True

        # --- New parsing, sorting, and reconstruction logic ---
        parsed_log_entries = []
        title_prefix_for_reconstruction = ""
        content_to_parse = worklog_content

        if content_to_parse.startswith("# "):
            first_newline_idx = content_to_parse.find("\n")
            if first_newline_idx != -1:
                title_prefix_for_reconstruction = content_to_parse[:first_newline_idx + 1]  # e.g., "# Title\n"
                content_to_parse = content_to_parse[first_newline_idx + 1:]
            else:  # Title without a newline (edge case)
                title_prefix_for_reconstruction = content_to_parse
                content_to_parse = ""
        
        # Remove leading blank lines from content_to_parse (e.g., the one often after a title)
        content_to_parse = content_to_parse.lstrip('\n')

        # Clean up all horizontal rule separators, letting the script re-create them.
        content_to_parse = re.sub(r'^\s*---\s*$', '', content_to_parse, flags=re.MULTILINE)

        if content_to_parse.strip():  # If there's anything left to parse
            # Regex to identify the header of any log entry
            generic_header_regex_str = r"\d{4}-\d{1,2}-\d{1,2}\s+[A-Za-z]+\s*\(\d+\.?\d*h\+?\):"
            
            # Split by separator, keeping the separator
            parts = re.split(r'(\n\s*---\s*\n)', content_to_parse)

            for part in parts:
                if re.match(r'\n\s*---\s*\n', part):
                    if parsed_log_entries and parsed_log_entries[-1] != "---":
                        parsed_log_entries.append("---")
                    continue

                # Regex to find individual, complete entries (including multi-line descriptions)
                # It matches an entry starting with a header, followed by its description lines.
                # The negative lookahead `(?!{generic_header_regex_str})` ensures description lines
                # are not mistaken for new entry headers.
                individual_entry_pattern = rf"^({generic_header_regex_str}[^\n]*(?:\n(?!{generic_header_regex_str})[^\n]*)*)"

                for match in re.finditer(individual_entry_pattern, part, re.MULTILINE):
                    parsed_log_entries.append(match.group(0).strip()) # Add the clean entry text

        # Sort entries in reverse chronological order, keeping separators in place
        def get_entry_date_from_string(entry_text: str) -> datetime:
            if entry_text == "---":
                return datetime.max # Keep separators at the top for now
            try:
                # Extract date string from the start of entry_text
                match = re.match(r"(\d{4}-\d{1,2}-\d{1,2})", entry_text)
                if match:
                    date_str = match.group(1)
                    # Use %m and %d for robust parsing of month and day
                    return datetime.strptime(date_str, "%Y-%m-%d")  
                return datetime.min # Fallback for malformed entries
            except (ValueError, IndexError):
                return datetime.min # Fallback for errors
        
        parsed_log_entries.sort(key=get_entry_date_from_string, reverse=True)

        # Reconstruct the final worklog content dynamically with week separators
        final_content_parts = []
        previous_entry_date_obj = None

        for i, entry_text in enumerate(parsed_log_entries):
            if entry_text == "---":
                continue # We will add separators based on date logic

            current_entry_date_obj = get_entry_date_from_string(entry_text)
            # logger.info(f"Processing entry for sorting: Date: {current_entry_date_obj.strftime('%Y-%m-%d') if current_entry_date_obj != datetime.min else 'Invalid Date'}, Entry: '{entry_text[:70]}...'")
            if i > 0:  # If not the first entry, decide on the separator to prepend
                # Find previous real entry to compare dates
                prev_entry_text = ""
                for j in range(i - 1, -1, -1):
                    if parsed_log_entries[j] != "---":
                        prev_entry_text = parsed_log_entries[j]
                        break
                
                if prev_entry_text:
                    previous_entry_date_obj = get_entry_date_from_string(prev_entry_text)
                    separator_due_to_week_change = False
                    if previous_entry_date_obj != datetime.min and current_entry_date_obj != datetime.min and previous_entry_date_obj != datetime.max:
                        # Calculate the Monday of the week for the previous entry
                        prev_monday_date = previous_entry_date_obj.date() - timedelta(days=previous_entry_date_obj.weekday())
                        # Calculate the Monday of the week for the current entry
                        curr_monday_date = current_entry_date_obj.date() - timedelta(days=current_entry_date_obj.weekday())
                        # logger.info(f"Comparing weeks: Prev Monday: {prev_monday_date} (from {previous_entry_date_obj.date()}), Curr Monday: {curr_monday_date} (from {current_entry_date_obj.date()})")
                        if prev_monday_date != curr_monday_date:
                            separator_due_to_week_change = True
                    
                    if separator_due_to_week_change:
                        final_content_parts.append("\n\n---\n\n")  # Separator includes its own empty lines
                    else:
                        final_content_parts.append("\n\n")  # Standard one empty line
                else: # No previous entry, this is the first one
                     pass # No separator needed
            
            final_content_parts.append(entry_text)
            previous_entry_date_obj = current_entry_date_obj
            
        final_entries_section = "".join(final_content_parts)

        if title_prefix_for_reconstruction:  # If there was a title (e.g., "# Title\n")
            title_base = title_prefix_for_reconstruction.rstrip('\n') # Get "# Title"
            if final_entries_section:
                # Title, one empty line, then entries, then a final newline
                worklog_content = title_base + "\n\n" + final_entries_section + "\n"
            else:  # Title, but no entries
                worklog_content = title_base + "\n"  # e.g., "# Title\n"
        else:  # No title
            if final_entries_section:
                worklog_content = final_entries_section + "\n"
            else:  # No title, no entries
                worklog_content = "\n"  # Represent an empty worklog as a single newline
        # --- End of new parsing and reconstruction logic ---

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
