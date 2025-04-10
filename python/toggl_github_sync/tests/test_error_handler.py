"""Unit tests for error handling and logging module."""

import unittest
from unittest.mock import MagicMock, patch

import logging
import sendgrid

from toggl_github_sync.config import Config
from toggl_github_sync.utils.error_handler import (
    setup_logging,
    send_error_notification,
    ErrorHandler,
)


class TestErrorHandler(unittest.TestCase):
    """Test cases for error handling and logging module."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = MagicMock(spec=Config)
        self.mock_config.log_level = logging.INFO
        self.mock_config.log_file = None
        self.mock_config.sendgrid_api_key = "test_api_key"
        self.mock_config.notification_email_from = "from@example.com"
        self.mock_config.notification_email_to = "to@example.com"

    @patch("toggl_github_sync.utils.error_handler.logging")
    def test_setup_logging(self, mock_logging):
        """Test setting up logging."""
        # Setup mock logger
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger
        
        # Setup mock handlers
        mock_console_handler = MagicMock()
        mock_logging.StreamHandler.return_value = mock_console_handler
        
        # Call the function
        logger = setup_logging(self.mock_config)
        
        # Assertions
        self.assertEqual(logger, mock_logger)
        mock_logger.setLevel.assert_called_once_with(logging.INFO)
        mock_logger.addHandler.assert_called_once_with(mock_console_handler)
        
        # Test with log file
        mock_logger.reset_mock()
        mock_file_handler = MagicMock()
        mock_logging.FileHandler.return_value = mock_file_handler
        
        self.mock_config.log_file = "/tmp/test.log"
        logger = setup_logging(self.mock_config)
        
        # Should add both console and file handlers
        self.assertEqual(mock_logger.addHandler.call_count, 2)
        mock_logging.FileHandler.assert_called_once_with("/tmp/test.log")

    @patch("toggl_github_sync.utils.error_handler.sendgrid.SendGridAPIClient")
    def test_send_error_notification(self, mock_sendgrid_client):
        """Test sending error notification."""
        # Setup mock SendGrid client
        mock_client = MagicMock()
        mock_sendgrid_client.return_value = mock_client
        
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 202  # Accepted
        mock_client.client.mail.send.post.return_value = mock_response
        
        # Setup mock logger
        mock_logger = MagicMock()
        
        # Call the function
        result = send_error_notification(
            self.mock_config,
            "Test Error",
            "This is a test error message",
            mock_logger
        )
        
        # Assertions
        self.assertTrue(result)
        mock_sendgrid_client.assert_called_once_with(api_key="test_api_key")
        mock_client.client.mail.send.post.assert_called_once()
        mock_logger.info.assert_called_once()
        
        # Test with failed response
        mock_response.status_code = 400  # Bad Request
        mock_logger.reset_mock()
        
        result = send_error_notification(
            self.mock_config,
            "Test Error",
            "This is a test error message",
            mock_logger
        )
        
        # Assertions
        self.assertFalse(result)
        mock_logger.error.assert_called_once()
        
        # Test with missing configuration
        self.mock_config.sendgrid_api_key = None
        mock_logger.reset_mock()
        
        result = send_error_notification(
            self.mock_config,
            "Test Error",
            "This is a test error message",
            mock_logger
        )
        
        # Assertions
        self.assertFalse(result)
        mock_logger.warning.assert_called_once()

    @patch("toggl_github_sync.utils.error_handler.send_error_notification")
    def test_error_handler(self, mock_send_notification):
        """Test error handler."""
        # Setup mock logger
        mock_logger = MagicMock()
        
        # Create error handler
        handler = ErrorHandler(self.mock_config, mock_logger)
        
        # Test handling an error
        test_error = ValueError("Test error")
        handler.handle_error(test_error, "test_context")
        
        # Assertions
        mock_logger.error.assert_called_once()
        mock_send_notification.assert_called_once_with(
            self.mock_config,
            "Error in test_context",
            "ValueError: Test error",
            mock_logger
        )


if __name__ == "__main__":
    unittest.main()
