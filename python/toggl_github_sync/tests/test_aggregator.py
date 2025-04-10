"""Unit tests for time entry aggregator."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytz

from toggl_github_sync.aggregator import TimeEntryAggregator
from toggl_github_sync.api.toggl import TogglApiClient
from toggl_github_sync.config import Config


class TestTimeEntryAggregator(unittest.TestCase):
    """Test cases for TimeEntryAggregator."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.timezone = "US/Pacific"
        
        self.mock_toggl_client = MagicMock(spec=TogglApiClient)
        self.aggregator = TimeEntryAggregator(self.mock_config, self.mock_toggl_client)

    async def test_aggregate_daily_entries(self):
        """Test aggregating daily entries."""
        # Setup mock responses
        self.mock_toggl_client.get_entries_by_date.return_value = [
            {"id": 1, "description": "Task 1", "duration": 3600},
            {"id": 2, "description": "Task 2", "duration": 1800},
        ]
        self.mock_toggl_client.calculate_daily_hours.return_value = 1.5
        self.mock_toggl_client.get_current_time_entry.return_value = None
        self.mock_toggl_client.get_entries_descriptions.return_value = ["Task 1", "Task 2"]
        
        # Call the method
        test_date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        entry, hours, has_running = await self.aggregator.aggregate_daily_entries(test_date)
        
        # Assertions
        self.assertEqual(hours, 1.5)
        self.assertFalse(has_running)
        self.assertEqual(entry, "2025-4-9 Wed (1.5h): Task 1. Task 2.")
        
        # Verify method calls
        self.mock_toggl_client.get_entries_by_date.assert_called_once_with(test_date)
        self.mock_toggl_client.calculate_daily_hours.assert_called_once()
        self.mock_toggl_client.get_current_time_entry.assert_called_once()
        self.mock_toggl_client.get_entries_descriptions.assert_called_once()

    async def test_aggregate_daily_entries_with_running_entry(self):
        """Test aggregating daily entries with a running entry."""
        # Setup mock responses
        self.mock_toggl_client.get_entries_by_date.return_value = [
            {"id": 1, "description": "Task 1", "duration": 3600},
            {"id": 2, "description": "Running task", "duration": -1},
        ]
        self.mock_toggl_client.calculate_daily_hours.return_value = 1.8
        self.mock_toggl_client.get_current_time_entry.return_value = {"id": 2, "description": "Running task"}
        self.mock_toggl_client.get_entries_descriptions.return_value = ["Task 1", "Running task"]
        
        # Call the method
        test_date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        entry, hours, has_running = await self.aggregator.aggregate_daily_entries(test_date)
        
        # Assertions
        self.assertEqual(hours, 1.8)
        self.assertTrue(has_running)
        self.assertEqual(entry, "2025-4-9 Wed (1.8h+): Task 1. Running task.")

    def test_format_worklog_entry(self):
        """Test formatting worklog entries."""
        # Test with multiple descriptions
        test_date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        entry = self.aggregator.format_worklog_entry(
            test_date, 
            2.5, 
            ["Task 1", "Task 2", "Task 3"], 
            False
        )
        self.assertEqual(entry, "2025-4-9 Wed (2.5h): Task 1. Task 2. Task 3.")
        
        # Test with running entry
        entry = self.aggregator.format_worklog_entry(
            test_date, 
            3.0, 
            ["Task 1"], 
            True
        )
        self.assertEqual(entry, "2025-4-9 Wed (3.0h+): Task 1.")
        
        # Test with no descriptions
        entry = self.aggregator.format_worklog_entry(
            test_date, 
            1.0, 
            [], 
            False
        )
        self.assertEqual(entry, "2025-4-9 Wed (1.0h): ")


if __name__ == "__main__":
    unittest.main()
