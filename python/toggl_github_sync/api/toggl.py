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
    
    def __init__(self, config: Config):
        """Initialize the Toggl API client.
        
        Args:
            config: Application configuration
        """
        self.api_token = config.toggl_api_token
        self.timezone = pytz.timezone(config.timezone)
        
    def get_time_entries(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get time entries from Toggl API.
        
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
        
        # Format dates for Toggl API
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()
        
        logger.info(f"Fetching Toggl time entries from {start_date_str} to {end_date_str}")
        
        # Build request URL with parameters
        url = f"{self.BASE_URL}/me/time_entries"
        params = {
            "start_date": start_date_str,
            "end_date": end_date_str,
        }
        
        # Make request to Toggl API
        response = requests.get(
            url,
            params=params,
            auth=(self.api_token, "api_token"),
            headers={"Content-Type": "application/json"},
        )
        
        # Check for errors
        response.raise_for_status()
        
        # Return time entries
        return response.json()
    
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
