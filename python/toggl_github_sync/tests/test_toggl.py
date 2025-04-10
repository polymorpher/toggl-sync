"""Unit tests for Toggl API client."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytz

from toggl_github_sync.api.toggl import TogglApiClient
from toggl_github_sync.config import Config


class TestTogglApiClient(unittest.TestCase):
    """Test cases for TogglApiClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.toggl_api_token = "test_token"
        self.mock_config.timezone = "US/Pacific"
        self.client = TogglApiClient(self.mock_config)

    @patch("toggl_github_sync.api.toggl.requests.get")
    def test_get_time_entries(self, mock_get):
        """Test getting time entries."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": 1, "description": "Test entry 1", "duration": 3600},
            {"id": 2, "description": "Test entry 2", "duration": 1800},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call the method
        entries = self.client.get_time_entries()

        # Assertions
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["description"], "Test entry 1")
        self.assertEqual(entries[1]["description"], "Test entry 2")
        mock_get.assert_called_once()

    @patch("toggl_github_sync.api.toggl.requests.get")
    def test_get_current_time_entry(self, mock_get):
        """Test getting current time entry."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": 3,
            "description": "Current entry",
            "duration": -1,
            "start": "2025-04-09T08:00:00Z",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Call the method
        entry = self.client.get_current_time_entry()

        # Assertions
        self.assertIsNotNone(entry)
        self.assertEqual(entry["description"], "Current entry")
        mock_get.assert_called_once()

    def test_calculate_daily_hours(self):
        """Test calculating daily hours."""
        # Test data
        entries = [
            {"id": 1, "description": "Test entry 1", "duration": 3600},  # 1 hour
            {"id": 2, "description": "Test entry 2", "duration": 1800},  # 30 minutes
        ]

        # Call the method
        hours = self.client.calculate_daily_hours(entries)

        # Assertions
        self.assertEqual(hours, 1.5)

    def test_calculate_daily_hours_with_running_entry(self):
        """Test calculating daily hours with a running entry."""
        # Current time for the test
        now = datetime.now(timezone.utc)

        # Start time 30 minutes ago
        start_time = now - timedelta(minutes=30)
        start_time_str = start_time.isoformat().replace("+00:00", "Z")

        # Test data with a running entry
        entries = [
            {"id": 1, "description": "Test entry 1", "duration": 3600},  # 1 hour
            {
                "id": 2,
                "description": "Running entry",
                "duration": -1,
                "start": start_time_str,
            },
        ]

        # Call the method
        hours = self.client.calculate_daily_hours(entries)

        # Assertions - should be approximately 1.5 hours (1 hour + ~30 minutes)
        self.assertGreaterEqual(hours, 1.4)
        self.assertLessEqual(hours, 1.6)

    def test_get_entries_descriptions(self):
        """Test extracting descriptions from entries."""
        # Test data
        entries = [
            {"id": 1, "description": "Test entry 1", "duration": 3600},
            {"id": 2, "description": "Test entry 2", "duration": 1800},
            {"id": 3, "description": "", "duration": 900},  # Empty description
            {
                "id": 4,
                "description": "  Test entry 4  ",
                "duration": 1200,
            },  # With whitespace
        ]

        # Call the method
        descriptions = self.client.get_entries_descriptions(entries)

        # Assertions
        self.assertEqual(len(descriptions), 3)
        self.assertEqual(descriptions[0], "Test entry 1")
        self.assertEqual(descriptions[1], "Test entry 2")
        self.assertEqual(descriptions[2], "Test entry 4")  # Whitespace trimmed


if __name__ == "__main__":
    unittest.main()
