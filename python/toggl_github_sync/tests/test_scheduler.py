"""Unit tests for scheduler module."""

import unittest
from unittest.mock import MagicMock, patch

from apscheduler.schedulers.background import BackgroundScheduler

from toggl_github_sync.config import Config
from toggl_github_sync.scheduler import start_scheduler


class TestScheduler(unittest.TestCase):
    """Test cases for scheduler module."""

    @patch("toggl_github_sync.scheduler.BackgroundScheduler")
    @patch("toggl_github_sync.scheduler.sync_toggl_to_github")
    @patch("toggl_github_sync.scheduler.time.sleep", side_effect=KeyboardInterrupt)
    def test_start_scheduler(self, mock_sleep, mock_sync, mock_scheduler_class):
        """Test starting the scheduler."""
        # Setup mock scheduler
        mock_scheduler = MagicMock(spec=BackgroundScheduler)
        mock_scheduler_class.return_value = mock_scheduler
        
        # Setup mock config
        mock_config = MagicMock(spec=Config)
        mock_config.sync_interval_minutes = 60
        
        # Call the function (will exit due to KeyboardInterrupt from mocked sleep)
        start_scheduler(mock_config)
        
        # Verify scheduler was started
        mock_scheduler.start.assert_called_once()
        
        # Verify job was added with correct parameters
        mock_scheduler.add_job.assert_called_once()
        args, kwargs = mock_scheduler.add_job.call_args
        self.assertEqual(args[0], mock_sync)  # First arg should be the sync function
        self.assertEqual(kwargs["args"], [mock_config])
        
        # Verify sync was called immediately
        mock_sync.assert_called_once_with(mock_config)
        
        # Verify scheduler was shutdown on exit
        mock_scheduler.shutdown.assert_called_once()


if __name__ == "__main__":
    unittest.main()
