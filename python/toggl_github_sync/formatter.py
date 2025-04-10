"""Worklog formatting module."""

import calendar
import logging
import re
from datetime import datetime
from typing import List, Optional

import pytz

from toggl_github_sync.config import Config

logger = logging.getLogger(__name__)

class WorklogFormatter:
    """Formats worklog entries according to the required format."""

    def __init__(self, config: Config):
        """Initialize the worklog formatter.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.timezone = pytz.timezone(config.timezone)
    
    def format_entry(
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
    
    def parse_entry(self, entry: str) -> Optional[dict]:
        """Parse a worklog entry.
        
        Args:
            entry: Worklog entry string
            
        Returns:
            Dictionary with parsed components or None if parsing failed
        """
        # Pattern to match worklog entries
        pattern = r"(\d{4}-\d{1,2}-\d{1,2}) ([A-Za-z]{3}) \((\d+\.?\d*)h(\+?)\): (.*)"
        match = re.match(pattern, entry)
        
        if not match:
            logger.warning(f"Failed to parse worklog entry: {entry}")
            return None
        
        date_str, day_name, hours_str, running_marker, description = match.groups()
        
        try:
            # Parse date
            year, month, day = map(int, date_str.split("-"))
            date = datetime(year, month, day, tzinfo=self.timezone)
            
            # Parse hours
            hours = float(hours_str)
            
            # Parse running status
            has_running_entry = running_marker == "+"
            
            # Parse descriptions
            descriptions = [d.strip() for d in description.split(".") if d.strip()]
            
            return {
                "date": date,
                "day_name": day_name,
                "hours": hours,
                "has_running_entry": has_running_entry,
                "descriptions": descriptions,
                "description_text": description,
            }
        except (ValueError, IndexError) as e:
            logger.warning(f"Error parsing worklog entry: {e}")
            return None
    
    def merge_entries(self, existing_entry: str, new_entry: str) -> str:
        """Merge an existing entry with a new entry.
        
        Args:
            existing_entry: Existing worklog entry
            new_entry: New worklog entry
            
        Returns:
            Merged worklog entry
        """
        existing_parsed = self.parse_entry(existing_entry)
        new_parsed = self.parse_entry(new_entry)
        
        if not existing_parsed or not new_parsed:
            logger.warning("Failed to parse entries for merging, using new entry")
            return new_entry
        
        # Use the higher hours value
        hours = max(existing_parsed["hours"], new_parsed["hours"])
        
        # Combine running status (if either is running, result is running)
        has_running_entry = existing_parsed["has_running_entry"] or new_parsed["has_running_entry"]
        
        # Combine descriptions (unique only)
        all_descriptions = existing_parsed["descriptions"] + new_parsed["descriptions"]
        unique_descriptions = []
        for desc in all_descriptions:
            if desc not in unique_descriptions:
                unique_descriptions.append(desc)
        
        # Format the merged entry
        return self.format_entry(
            existing_parsed["date"],
            hours,
            unique_descriptions,
            has_running_entry
        )
