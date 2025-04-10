"""Unit tests for worklog formatter."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock

import pytz

from toggl_github_sync.config import Config
from toggl_github_sync.formatter import WorklogFormatter


class TestWorklogFormatter(unittest.TestCase):
    """Test cases for WorklogFormatter."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.timezone = "US/Pacific"
        self.formatter = WorklogFormatter(self.mock_config)

    def test_format_entry(self):
        """Test formatting worklog entries."""
        # Test with multiple descriptions
        test_date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        entry = self.formatter.format_entry(
            test_date, 
            2.5, 
            ["Task 1", "Task 2", "Task 3"], 
            False
        )
        self.assertEqual(entry, "2025-4-9 Wed (2.5h): Task 1. Task 2. Task 3.")
        
        # Test with running entry
        entry = self.formatter.format_entry(
            test_date, 
            3.0, 
            ["Task 1"], 
            True
        )
        self.assertEqual(entry, "2025-4-9 Wed (3.0h+): Task 1.")
        
        # Test with no descriptions
        entry = self.formatter.format_entry(
            test_date, 
            1.0, 
            [], 
            False
        )
        self.assertEqual(entry, "2025-4-9 Wed (1.0h): ")

    def test_parse_entry(self):
        """Test parsing worklog entries."""
        # Test parsing a complete entry
        entry = "2025-4-9 Wed (2.5h): Task 1. Task 2. Task 3."
        parsed = self.formatter.parse_entry(entry)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["hours"], 2.5)
        self.assertFalse(parsed["has_running_entry"])
        self.assertEqual(parsed["descriptions"], ["Task 1", "Task 2", "Task 3"])
        
        # Test parsing an entry with running marker
        entry = "2025-4-9 Wed (3.0h+): Task 1."
        parsed = self.formatter.parse_entry(entry)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["hours"], 3.0)
        self.assertTrue(parsed["has_running_entry"])
        self.assertEqual(parsed["descriptions"], ["Task 1"])
        
        # Test parsing an invalid entry
        entry = "Invalid entry format"
        parsed = self.formatter.parse_entry(entry)
        
        self.assertIsNone(parsed)

    def test_merge_entries(self):
        """Test merging worklog entries."""
        # Test merging entries with different hours
        existing = "2025-4-9 Wed (2.5h): Task 1. Task 2."
        new = "2025-4-9 Wed (3.0h): Task 2. Task 3."
        merged = self.formatter.merge_entries(existing, new)
        
        # Should use the higher hours value and combine descriptions
        self.assertEqual(merged, "2025-4-9 Wed (3.0h): Task 1. Task 2. Task 3.")
        
        # Test merging with running entry
        existing = "2025-4-9 Wed (2.5h): Task 1."
        new = "2025-4-9 Wed (2.0h+): Task 2."
        merged = self.formatter.merge_entries(existing, new)
        
        # Should keep the running marker
        self.assertEqual(merged, "2025-4-9 Wed (2.5h+): Task 1. Task 2.")
        
        # Test merging with invalid entry
        existing = "Invalid entry"
        new = "2025-4-9 Wed (2.0h): Task 1."
        merged = self.formatter.merge_entries(existing, new)
        
        # Should use the new entry
        self.assertEqual(merged, new)


if __name__ == "__main__":
    unittest.main()
