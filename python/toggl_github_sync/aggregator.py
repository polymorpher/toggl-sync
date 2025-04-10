"""Daily time entry aggregation module."""

import calendar
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pytz

from toggl_github_sync.api.toggl import TogglApiClient
from toggl_github_sync.config import Config

logger = logging.getLogger(__name__)

class TimeEntryAggregator:
    """Aggregates time entries by day."""

    def __init__(self, config: Config, toggl_client: Optional[TogglApiClient] = None):
        """Initialize the time entry aggregator.
        
        Args:
            config: Application configuration
            toggl_client: Toggl API client (optional, will create one if not provided)
        """
        self.config = config
        self.timezone = pytz.timezone(config.timezone)
        self.toggl_client = toggl_client or TogglApiClient(config)
    
    async def aggregate_daily_entries(self, date: Optional[datetime] = None) -> Tuple[str, float, bool]:
        """Aggregate time entries for a specific day.
        
        Args:
            date: Date to aggregate entries for (default: today in configured timezone)
            
        Returns:
            Tuple of (formatted_entry, total_hours, has_running_entry)
        """
        # If date not provided, use current day in configured timezone
        if date is None:
            date = datetime.now(self.timezone)
        
        # Get time entries for the day
        entries = self.toggl_client.get_entries_by_date(date)
        
        # Calculate total hours
        total_hours = self.toggl_client.calculate_daily_hours(entries)
        
        # Check if there's a running entry
        current_entry = self.toggl_client.get_current_time_entry()
        has_running_entry = current_entry is not None
        
        # Get descriptions from entries
        descriptions = self.toggl_client.get_entries_descriptions(entries)
        
        # Format the entry
        formatted_entry = self.format_worklog_entry(date, total_hours, descriptions, has_running_entry)
        
        return formatted_entry, total_hours, has_running_entry
    
    def format_worklog_entry(
        self, 
        date: datetime, 
        hours: float, 
        descriptions: List[str], 
        has_running_entry: bool
    ) -> str:
        """Format a worklog entry.
        
        Args:
            date: Date of the entry
            hours: Total hours worked
            descriptions: List of task descriptions
            has_running_entry: Whether there's a running entry
            
        Returns:
            Formatted worklog entry
        """
        # Format date as YYYY-M-D
        date_str = date.strftime("%Y-%-m-%-d")
        
        # Get day name (Mon, Tue, etc.)
        day_name = calendar.day_name[date.weekday()][:3]
        
        # Format hours as X.Yh or X.Yh+ if there's a running entry
        hours_str = f"{hours}h"
        if has_running_entry:
            hours_str += "+"
        
        # Join descriptions with periods
        description_text = ". ".join(descriptions)
        if description_text and not description_text.endswith("."):
            description_text += "."
        
        # Format the entry
        return f"{date_str} {day_name} ({hours_str}): {description_text}"
