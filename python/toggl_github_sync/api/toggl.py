"""Toggl API client implementation."""

import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any

import pytz
import requests

from toggl_github_sync.config import Config

logger = logging.getLogger(__name__)

class TogglApiClient:
    """Client for interacting with the Toggl API."""

    BASE_URL = "https://api.track.toggl.com/api/v9"
    REPORTS_BASE_URL = "https://api.track.toggl.com/reports/api/v3"
    
    def __init__(self, config: Config):
        """Initialize the Toggl API client.
        
        Args:
            config: Application configuration
        """
        self.api_token = config.toggl_api_token
        self.timezone = pytz.timezone(config.timezone)
        self.workspace_id = getattr(config, "toggl_workspace_id", None)
        
    def get_time_entries(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get time entries from Toggl API, using dynamic pagination based on response.
        
        Args:
            start_date: Start date for time entries (default: start of current day in configured timezone)
            end_date: End date for time entries (default: end of current day in configured timezone)
            
        Returns:
            List of time entries
        """
        # If dates not provided, use current day in configured timezone
        if start_date is None or end_date is None:
            now = datetime.now(self.timezone)
            start_date = datetime.combine(now.date(), time.min).replace(tzinfo=self.timezone)
            end_date = datetime.combine(now.date(), time.max).replace(tzinfo=self.timezone)

        # If the requested start date is older than 90 days from now, use the Detailed Reports API
        cutoff = datetime.now(self.timezone) - timedelta(days=90)
        if start_date < cutoff:
            logger.info("Start date is older than 90 days; using Detailed Reports API for retrieval")
            return self._get_time_entries_via_reports(start_date, end_date)
        
        all_entries = []
        seen_entry_ids = set()
        
        current_end_date = end_date

        while True:
            # Format dates for Toggl API
            start_date_str = start_date.isoformat()
            end_date_str = current_end_date.isoformat()
            
            logger.info(f"Fetching Toggl time entries from {start_date_str} to {end_date_str}")
            
            # Build request URL with parameters
            url = f"{self.BASE_URL}/me/time_entries"
            params = {"start_date": start_date_str, "end_date": end_date_str}
            
            # Make request to Toggl API
            response = requests.get(
                url,
                params=params,
                auth=(self.api_token, "api_token"),
                headers={"Content-Type": "application/json"},
            )
            
            # Check for errors
            response.raise_for_status()
            
            chunk = response.json()
            if not chunk:
                break  # No more entries to fetch

            new_entries_found_in_chunk = False
            for entry in chunk:
                if entry["id"] not in seen_entry_ids:
                    all_entries.append(entry)
                    seen_entry_ids.add(entry["id"])
                    new_entries_found_in_chunk = True

            # If the chunk contained only entries we've already seen, we're done.
            if not new_entries_found_in_chunk:
                break

            # The last entry in the chunk is the oldest. Its start time is the end for the next chunk.
            oldest_entry_in_chunk = chunk[-1]
            current_end_date = datetime.fromisoformat(oldest_entry_in_chunk["start"].replace("Z", "+00:00"))

            # In essence, it's a safety net to guarantee the loop terminates and doesn't accidentally start fetching data from before the originally requested time period. While the other two exit conditions (if not chunk: and if not new_entries_found_in_chunk:) are the ones expected to terminate the loop in normal operation, this extra check provides an additional layer of robustness against the unexpected.
            # It's a harmless check, but I understand that it can be confusing since its condition shouldn't be met. If you find it makes the code harder to understand, I'm happy to remove it.
            # If the next fetch would start before our original start date, we're done.
            if current_end_date < start_date:
                break
        
        logger.info(f"Fetched a total of {len(all_entries)} unique entries.")
        
        # Return time entries
        return all_entries

    def _get_time_entries_via_reports(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Fetch time entries using the Detailed Reports API (supports >90 days).

        Uses pagination via X-Next-ID and X-Next-Row-Number.
        """
        if not self.workspace_id:
            raise ValueError("toggl_workspace_id is required to use Reports API. Set TOGGL_WORKSPACE_ID in environment.")

        # Convert to date-only and time components in the configured timezone
        start_local_dt = start_date.astimezone(self.timezone)
        end_local_dt = end_date.astimezone(self.timezone)
        start_date_local = start_local_dt.date().isoformat()
        end_date_local = end_local_dt.date().isoformat()
        start_time_local = start_local_dt.time().isoformat(timespec="seconds")
        end_time_local = end_local_dt.time().isoformat(timespec="seconds")

        url = f"{self.REPORTS_BASE_URL}/workspace/{self.workspace_id}/search/time_entries"
        headers = {"Content-Type": "application/json"}
        auth = (self.api_token, "api_token")

        accumulated: List[Dict[str, Any]] = []
        seen_ids = set()

        first_id: Optional[int] = None
        first_row_number: Optional[int] = None

        while True:
            body: Dict[str, Any] = {
                "start_date": start_date_local,
                "end_date": end_date_local,
                "startTime": start_local_dt.isoformat(),
                "endTime": end_local_dt.isoformat(),
                "enrich_response": True,
                "page_size": 1000,
                # Keep results ordered from newest to oldest for consistent pagination
                "order_by": "date",
                "order_dir": "desc",
            }
            # logger.info(f"Body: {body}")
            if first_id is not None and first_row_number is not None:
                body["first_id"] = first_id
                body["first_row_number"] = first_row_number

            logger.info(
                f"Fetching Detailed Reports time entries {start_date_local}..{end_date_local}"
                + (f" with first_id={first_id}, first_row_number={first_row_number}" if first_id is not None else "")
            )

            response = requests.post(url, json=body, auth=auth, headers=headers)
            
            logger.info(f"Response: {response.json()}")
            response.raise_for_status()

            # Parse entries from response; tolerate different shapes
            payload = response.json()
            if isinstance(payload, list):
                chunk = payload
            elif isinstance(payload, dict):
                # Common containers
                if "data" in payload and isinstance(payload["data"], list):
                    chunk = payload["data"]
                elif "time_entries" in payload and isinstance(payload["time_entries"], list):
                    chunk = payload["time_entries"]
                else:
                    chunk = []
            else:
                chunk = []

            if not chunk:
                break

            for raw in chunk:
                # Rows can contain a list of time entries under 'time_entries'
                if isinstance(raw, dict) and isinstance(raw.get("time_entries"), list):
                    for te in raw["time_entries"]:
                        entry = self._normalize_reports_time_entry(raw, te)
                        entry_id = entry.get("id")
                        if entry_id is None or entry_id in seen_ids:
                            continue
                        seen_ids.add(entry_id)
                        accumulated.append(entry)
                else:
                    # Fallback to single-entry normalization
                    entry = self._normalize_reports_entry(raw)
                    entry_id = entry.get("id")
                    if entry_id is None or entry_id in seen_ids:
                        continue
                    seen_ids.add(entry_id)
                    accumulated.append(entry)

            # Pagination headers
            next_id = response.headers.get("X-Next-ID")
            next_row = response.headers.get("X-Next-Row-Number")
            if not next_id or not next_row:
                break
            try:
                first_id = int(next_id)
                first_row_number = int(next_row)
            except ValueError:
                break

        logger.info(f"Fetched a total of {len(accumulated)} unique entries via Detailed Reports")
        return accumulated

    def _normalize_reports_time_entry(self, row: Dict[str, Any], te: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a single time entry from a Detailed Reports row that contains 'time_entries'."""
        normalized: Dict[str, Any] = {}

        # ID
        entry_id = te.get("id") or te.get("time_entry_id")
        if entry_id is not None:
            normalized["id"] = entry_id

        # Start/stop
        start_val = te.get("start") or te.get("start_time") or te.get("startTime")
        end_val = te.get("stop") or te.get("end") or te.get("end_time") or te.get("endTime")
        if isinstance(start_val, str):
            normalized["start"] = start_val
        if isinstance(end_val, str):
            normalized["stop"] = end_val

        # Duration
        duration_val = te.get("seconds") or te.get("duration")
        if isinstance(duration_val, (int, float)):
            normalized["duration"] = int(duration_val)

        # Description comes from row grouping (preferred), fallback to te
        desc_val = row.get("description") or te.get("description") or row.get("title")
        if isinstance(desc_val, str):
            normalized["description"] = desc_val

        return normalized

    def _normalize_reports_entry(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a Detailed Reports time entry to match v9 time entry shape.

        Expected output keys: id, start, stop, duration, description
        """
        normalized: Dict[str, Any] = {}

        # If enriched, entries may be under a nested time_entry object
        source = item
        if isinstance(item.get("time_entry"), dict):
            source = item["time_entry"]

        # ID field
        entry_id = source.get("id") or source.get("time_entry_id") or item.get("time_entry_id") or item.get("id")
        if entry_id is not None:
            normalized["id"] = entry_id

        # Timestamps can be in different keys
        start_val = source.get("start") or source.get("start_time") or source.get("startTime") or item.get("start")
        end_val = source.get("stop") or source.get("end") or source.get("end_time") or source.get("endTime") or item.get("stop") or item.get("end")

        if isinstance(start_val, str):
            normalized["start"] = start_val
        if isinstance(end_val, str):
            normalized["stop"] = end_val

        # Duration seconds
        duration_val = source.get("duration") or source.get("seconds") or item.get("seconds") or item.get("duration")
        if isinstance(duration_val, (int, float)):
            normalized["duration"] = int(duration_val)

        # Description or title
        desc_val = source.get("description") or source.get("title") or item.get("description") or item.get("title")
        if isinstance(desc_val, str):
            normalized["description"] = desc_val

        return normalized
    
    def get_current_time_entry(self) -> Optional[Dict[str, Any]]:
        """Get the current running time entry, if any.
        
        Returns:
            Current time entry or None if no time entry is running
        """
        url = f"{self.BASE_URL}/me/time_entries/current"
        
        logger.info("Fetching current Toggl time entry")
        
        response = requests.get(
            url,
            auth=(self.api_token, "api_token"),
            headers={"Content-Type": "application/json"},
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Return current time entry (may be None)
        return response.json()
    
    def calculate_daily_hours(self, entries: List[Dict[str, Any]]) -> float:
        """Calculate total hours from time entries.
        
        Args:
            entries: List of time entries
            
        Returns:
            Total hours as float with one decimal place
        """
        total_seconds = 0
        
        for entry in entries:
            # For completed entries
            if entry.get("duration") and entry["duration"] > 0:
                total_seconds += entry["duration"]
            # For running entries
            elif entry.get("duration") and entry["duration"] < 0:
                # Calculate duration from start time to now
                start_time = datetime.fromisoformat(entry["start"].replace("Z", "+00:00"))
                now = datetime.now(pytz.UTC)
                duration = (now - start_time).total_seconds()
                total_seconds += duration
        
        # Convert to hours with one decimal place
        total_hours = round(total_seconds / 3600, 1)
        
        logger.info(f"Calculated total hours: {total_hours}")
        
        return total_hours
    
    def get_entries_by_date(self, date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get time entries for a specific date.
        
        Args:
            date: Date to get entries for (default: today in configured timezone)
            
        Returns:
            List of time entries for the specified date
        """
        if date is None:
            date = datetime.now(self.timezone)
        
        # Set start and end of day in configured timezone
        start_date = datetime.combine(date.date(), time.min).replace(tzinfo=self.timezone)
        end_date = datetime.combine(date.date(), time.max).replace(tzinfo=self.timezone)
        
        return self.get_time_entries(start_date, end_date)
    
    def get_entries_descriptions(self, entries: List[Dict[str, Any]]) -> List[str]:
        """Extract descriptions from time entries.
        
        Args:
            entries: List of time entries
            
        Returns:
            List of descriptions (non-empty)
        """
        descriptions = []
        
        for entry in entries:
            if entry.get("description") and entry["description"].strip():
                descriptions.append(entry["description"].strip())
        
        return descriptions
