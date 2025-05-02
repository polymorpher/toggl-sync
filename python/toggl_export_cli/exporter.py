import csv
import datetime
import logging
from typing import List, Dict, Any, Optional

import pytz

from toggl_github_sync.api.toggl import TogglApiClient
from toggl_github_sync.config import Config

logger = logging.getLogger(__name__)

def _format_duration(duration_seconds):
    """Formats duration in seconds to hh:mm:ss."""
    if duration_seconds is None or duration_seconds < 0:
        # Handle missing or negative durations (e.g., running timers might have negative duration from API)
        return "00:00:00"
    hours, remainder = divmod(duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def _export_toggl_to_csv(entries: List[Dict[str, Any]], output_filename: str):
    """
    Internal function to write Toggl entries to a CSV file.

    Args:
        entries (list): A list of dictionaries, where each dictionary represents a Toggl time entry.
                        Expected keys: 'start', 'stop', 'duration', 'description'.
                        'start' and 'stop' should be ISO 8601 strings (UTC).
        output_filename (str): The path to the output CSV file.
    """
    sf_timezone = pytz.timezone('America/Los_Angeles') # Requirement: Use SF timezone for export
    processed_entries = []

    for entry in entries:
        try:
            # Toggl API v9 returns start/stop as UTC ISO 8601 strings
            start_dt_utc = datetime.datetime.fromisoformat(entry['start'].replace('Z', '+00:00'))

            stop_dt_utc: Optional[datetime.datetime] = None
            if entry.get('stop'):
                stop_dt_utc = datetime.datetime.fromisoformat(entry['stop'].replace('Z', '+00:00'))
            # Use duration if stop is missing (Toggl API provides duration even for running timers, negative value)
            elif 'duration' in entry:
                 duration = entry['duration']
                 if duration >= 0: # Use duration only if it's non-negative (completed entry)
                     stop_dt_utc = start_dt_utc + datetime.timedelta(seconds=duration)
                 # else: Running timer, stop time is effectively 'now', but we'll skip exporting running timers

            if stop_dt_utc is None:
                logger.warning(f"Skipping entry with no stop time or non-negative duration: {entry.get('description', 'N/A')}")
                continue # Skip entries without a definite end time

            # Convert to San Francisco timezone for output
            start_dt_sf = start_dt_utc.astimezone(sf_timezone)
            stop_dt_sf = stop_dt_utc.astimezone(sf_timezone)

            # Use the duration provided by Toggl API if available and non-negative
            duration_seconds = entry.get('duration')
            if duration_seconds is None or duration_seconds < 0:
                # Recalculate if duration is missing or negative
                duration_seconds = (stop_dt_utc - start_dt_utc).total_seconds()


            processed_entries.append({
                'start_date': start_dt_sf.strftime('%Y-%m-%d'),
                'start_time': start_dt_sf.strftime('%H:%M:%S'),
                'end_date': stop_dt_sf.strftime('%Y-%m-%d'),
                'end_time': stop_dt_sf.strftime('%H:%M:%S'),
                'duration': _format_duration(duration_seconds),
                'description': entry.get('description', ''), # Use .get for safety
                'sort_key': start_dt_utc # Sort by original UTC start time
            })
        except Exception as e:
            logger.error(f"Error processing entry: {entry}. Error: {e}", exc_info=True)
            # Decide whether to skip or raise the error - skipping for now

    # Sort entries by start date and time (UTC)
    processed_entries.sort(key=lambda x: x['sort_key'])

    # Write to CSV
    header = ['Start date', 'Start time', 'End date', 'End time', 'Duration', 'Description']
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            # Map dict keys (lowercase_with_underscores) to CSV header (Title Case With Spaces)
            writer = csv.DictWriter(csvfile, fieldnames=header)
            writer.writeheader()
            for entry_data in processed_entries:
                 row_data = {
                    'Start date': entry_data['start_date'],
                    'Start time': entry_data['start_time'],
                    'End date': entry_data['end_date'],
                    'End time': entry_data['end_time'],
                    'Duration': entry_data['duration'],
                    'Description': entry_data['description']
                 }
                 writer.writerow(row_data)
        logger.info(f"Successfully exported {len(processed_entries)} entries to {output_filename}")
    except IOError as e:
        logger.error(f"Error writing to CSV file {output_filename}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"An unexpected error occurred during CSV writing: {e}", exc_info=True)


def fetch_and_export_toggl_csv(config: Config, output_filename: str, start_date: Optional[datetime.datetime] = None, end_date: Optional[datetime.datetime] = None):
    """
    Fetches Toggl time entries using the API client and exports them to a CSV file.

    Args:
        config: Application configuration.
        output_filename: The path to the output CSV file.
        start_date: Start date for fetching entries (timezone aware, defaults to client logic).
        end_date: End date for fetching entries (timezone aware, defaults to client logic).
    """
    client = TogglApiClient(config)

    try:
        # Get timezone from config
        timezone = pytz.timezone(config.timezone)

        # Ensure dates are timezone-aware, defaulting to today in the configured timezone
        if start_date is None and end_date is None:
            today = datetime.datetime.now(timezone).date()
            start_date = timezone.localize(datetime.datetime.combine(today, datetime.datetime.min.time()))
            end_date = timezone.localize(datetime.datetime.combine(today, datetime.datetime.max.time()))
        else:
            if start_date and start_date.tzinfo is None:
                start_date = timezone.localize(start_date)
            if end_date and end_date.tzinfo is None:
                end_date = timezone.localize(end_date)

        logger.info(f"Fetching Toggl entries for CSV export between {start_date} and {end_date}")
        # The client handles default dates based on its configured timezone if None are provided
        entries = client.get_time_entries(start_date=start_date, end_date=end_date)

        if not entries:
            logger.warning("No Toggl entries found for the specified date range.")
            return

        # Filter out entries that might still be running (duration < 0) before exporting
        # Although _export_toggl_to_csv also has checks, filtering early is cleaner.
        completed_entries = [e for e in entries if e.get('duration', -1) >= 0]

        if not completed_entries:
             logger.warning("No completed Toggl entries found for the specified date range to export.")
             return

        # Calculate total duration in seconds
        total_seconds = sum(entry.get('duration', 0) for entry in completed_entries)
        # Convert to hours
        total_hours = total_seconds / 3600
        # Print total hours
        logger.info(f"Total hours: {total_hours:.2f}")

        _export_toggl_to_csv(completed_entries, output_filename)

    except Exception as e:
        # Default error message
        error_message = f"Failed to fetch or export Toggl entries: {e}"
        # Check if the exception has HTTP response details and log them
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            try:
                # Attempt to get the response body
                response_body = e.response.text
                error_message += f"\nResponse Body: {response_body}"
            except Exception as inner_e:
                # Log if accessing response body fails for some reason
                logger.warning(f"Could not access response body from exception: {inner_e}")
        logger.error(error_message, exc_info=True) 