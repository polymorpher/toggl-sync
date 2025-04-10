"""Unit tests for configuration module."""

import os
import unittest
from unittest.mock import patch

import logging

from toggl_github_sync.config import Config, load_config


class TestConfig(unittest.TestCase):
    """Test cases for configuration module."""

    @patch.dict(os.environ, {
        "TOGGL_API_TOKEN": "test_toggl_token",
        "GITHUB_TOKEN": "test_github_token",
        "GITHUB_REPO": "test/repo",
        "GITHUB_WORKLOG_PATH": "progress/test.md",
        "TIMEZONE": "US/Pacific",
        "SENDGRID_API_KEY": "test_sendgrid_key",
        "NOTIFICATION_EMAIL_FROM": "from@example.com",
        "NOTIFICATION_EMAIL_TO": "to@example.com",
        "SYNC_INTERVAL_MINUTES": "30",
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": "/tmp/test.log",
    })
    def test_load_config(self):
        """Test loading configuration from environment variables."""
        config = load_config()
        
        # Verify required configuration
        self.assertEqual(config.toggl_api_token, "test_toggl_token")
        self.assertEqual(config.github_token, "test_github_token")
        self.assertEqual(config.github_repo, "test/repo")
        self.assertEqual(config.github_worklog_path, "progress/test.md")
        
        # Verify optional configuration
        self.assertEqual(config.timezone, "US/Pacific")
        self.assertEqual(config.sendgrid_api_key, "test_sendgrid_key")
        self.assertEqual(config.notification_email_from, "from@example.com")
        self.assertEqual(config.notification_email_to, "to@example.com")
        self.assertEqual(config.sync_interval_minutes, 30)
        self.assertEqual(config.log_level, logging.DEBUG)
        self.assertEqual(config.log_file, "/tmp/test.log")

    @patch.dict(os.environ, {
        "TOGGL_API_TOKEN": "test_toggl_token",
        "GITHUB_TOKEN": "test_github_token",
        "GITHUB_REPO": "test/repo",
        "GITHUB_WORKLOG_PATH": "progress/test.md",
    })
    def test_load_config_with_defaults(self):
        """Test loading configuration with default values."""
        config = load_config()
        
        # Verify default values
        self.assertEqual(config.timezone, "America/Los_Angeles")
        self.assertIsNone(config.sendgrid_api_key)
        self.assertIsNone(config.notification_email_from)
        self.assertIsNone(config.notification_email_to)
        self.assertEqual(config.sync_interval_minutes, 60)
        self.assertEqual(config.log_level, logging.INFO)
        self.assertIsNone(config.log_file)

    @patch.dict(os.environ, {})
    def test_load_config_missing_required(self):
        """Test loading configuration with missing required values."""
        with self.assertRaises(ValueError):
            load_config()

    @patch.dict(os.environ, {
        "TOGGL_API_TOKEN": "test_toggl_token",
    })
    def test_load_config_partial_required(self):
        """Test loading configuration with some required values missing."""
        with self.assertRaises(ValueError):
            load_config()

    @patch.dict(os.environ, {
        "TOGGL_API_TOKEN": "test_toggl_token",
        "GITHUB_TOKEN": "test_github_token",
        "GITHUB_REPO": "test/repo",
        "GITHUB_WORKLOG_PATH": "progress/test.md",
        "SYNC_INTERVAL_MINUTES": "invalid",
    })
    def test_load_config_invalid_numeric(self):
        """Test loading configuration with invalid numeric values."""
        config = load_config()
        
        # Should use default value for invalid numeric input
        self.assertEqual(config.sync_interval_minutes, 60)


if __name__ == "__main__":
    unittest.main()
