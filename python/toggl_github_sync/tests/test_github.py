"""Unit tests for GitHub API client."""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytz

from toggl_github_sync.api.github import GitHubApiClient
from toggl_github_sync.config import Config


class TestGitHubApiClient(unittest.TestCase):
    """Test cases for GitHubApiClient."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.github_token = "test_token"
        self.mock_config.github_repo = "test/repo"
        self.mock_config.worklog_path = "progress/test.md"
        self.mock_config.timezone = "US/Pacific"
        
        self.client = GitHubApiClient(self.mock_config)
        
        # Mock the Github client
        self.mock_github = MagicMock()
        self.client.github = self.mock_github
        
        # Mock repository
        self.mock_repo = MagicMock()
        self.mock_github.get_repo.return_value = self.mock_repo

    @patch("toggl_github_sync.api.github.base64")
    def test_get_worklog_content(self, mock_base64):
        """Test getting worklog content."""
        # Setup mock response
        mock_file_content = MagicMock()
        mock_file_content.content = "encoded_content"
        mock_file_content.sha = "test_sha"
        self.mock_repo.get_contents.return_value = mock_file_content
        
        mock_base64.b64decode.return_value = b"decoded_content"
        
        # Call the method
        content, sha = self.client.get_worklog_content()
        
        # Assertions
        self.assertEqual(content, "decoded_content")
        self.assertEqual(sha, "test_sha")
        self.mock_repo.get_contents.assert_called_once_with("progress/test.md")
        mock_base64.b64decode.assert_called_once_with("encoded_content")

    def test_update_worklog(self):
        """Test updating worklog content."""
        # Call the method
        result = self.client.update_worklog("new content", "test_sha")
        
        # Assertions
        self.assertTrue(result)
        self.mock_repo.update_file.assert_called_once_with(
            path="progress/test.md",
            message="Update worklog with Toggl time entries",
            content="new content",
            sha="test_sha",
        )

    def test_find_entry_for_date(self):
        """Test finding an entry for a specific date."""
        # Test content
        content = """# Worklog
        
2025-4-9 Wed (1.5h): Task 1. Task 2.

2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
"""
        
        # Test finding an existing entry
        date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        result = self.client.find_entry_for_date(content, date)
        
        # Assertions
        self.assertIsNotNone(result)
        entry, start_index, end_index = result
        self.assertEqual(entry, "2025-4-9 Wed (1.5h): Task 1. Task 2.")
        
        # Test finding a non-existent entry
        date = datetime(2025, 4, 10, tzinfo=pytz.timezone("US/Pacific"))
        result = self.client.find_entry_for_date(content, date)
        
        # Assertions
        self.assertIsNone(result)

    def test_update_or_create_entry_update(self):
        """Test updating an existing entry."""
        # Test content
        content = """# Worklog
        
2025-4-9 Wed (1.5h): Task 1. Task 2.

2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
"""
        
        # New entry
        new_entry = "2025-4-9 Wed (2.0h): Task 1. Task 2. Task 5."
        date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        
        # Call the method
        updated_content = self.client.update_or_create_entry(content, new_entry, date)
        
        # Assertions
        self.assertIn(new_entry, updated_content)
        self.assertNotIn("2025-4-9 Wed (1.5h): Task 1. Task 2.", updated_content)

    def test_update_or_create_entry_create(self):
        """Test creating a new entry."""
        # Test content
        content = """# Worklog
        
2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
"""
        
        # New entry
        new_entry = "2025-4-9 Wed (1.5h): Task 1. Task 2."
        date = datetime(2025, 4, 9, tzinfo=pytz.timezone("US/Pacific"))
        
        # Call the method
        updated_content = self.client.update_or_create_entry(content, new_entry, date)
        
        # Assertions
        self.assertIn(new_entry, updated_content)
        self.assertTrue(updated_content.index(new_entry) < updated_content.index("2025-4-8"))


if __name__ == "__main__":
    unittest.main()
