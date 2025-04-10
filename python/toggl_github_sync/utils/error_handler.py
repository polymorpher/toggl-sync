"""Error handling and logging module."""

import logging
import os
import sys
from typing import Optional

import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content

from toggl_github_sync.config import Config

def setup_logging(config: Config) -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured logger
    """
    # Create logger
    logger = logging.getLogger("toggl_github_sync")
    logger.setLevel(config.log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if log file is specified
    if config.log_file:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(config.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(config.log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def send_error_notification(
    config: Config, 
    subject: str, 
    error_message: str,
    logger: Optional[logging.Logger] = None
) -> bool:
    """Send error notification email using SendGrid.
    
    Args:
        config: Application configuration
        subject: Email subject
        error_message: Error message to send
        logger: Logger to use (optional)
        
    Returns:
        True if email was sent successfully, False otherwise
    """
    if not config.sendgrid_api_key or not config.notification_email_from or not config.notification_email_to:
        if logger:
            logger.warning("SendGrid API key or notification email not configured, skipping error notification")
        return False
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=config.sendgrid_api_key)
        
        from_email = Email(config.notification_email_from)
        to_email = To(config.notification_email_to)
        subject = f"Toggl GitHub Sync Error: {subject}"
        
        # Create email content with error details
        html_content = f"""
        <h2>Toggl GitHub Sync Error</h2>
        <p>An error occurred while syncing Toggl time entries to GitHub:</p>
        <pre>{error_message}</pre>
        <p>Please check the logs for more details.</p>
        <hr>
        <p><small>This is an automated message from the Toggl GitHub Sync application.</small></p>
        """
        
        content = Content("text/html", html_content)
        mail = Mail(from_email, to_email, subject, content)
        
        # Send email
        response = sg.client.mail.send.post(request_body=mail.get())
        
        if logger:
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Error notification sent to {config.notification_email_to}")
                return True
            else:
                logger.error(f"Failed to send error notification: {response.status_code} {response.body}")
                return False
        
        return response.status_code >= 200 and response.status_code < 300
        
    except Exception as e:
        if logger:
            logger.error(f"Error sending notification email: {e}")
        return False

class ErrorHandler:
    """Error handler for toggl_github_sync."""
    
    def __init__(self, config: Config, logger: Optional[logging.Logger] = None):
        """Initialize the error handler.
        
        Args:
            config: Application configuration
            logger: Logger to use (optional)
        """
        self.config = config
        self.logger = logger or logging.getLogger("toggl_github_sync")
    
    def handle_error(self, error: Exception, context: str = "Unknown") -> None:
        """Handle an error.
        
        Args:
            error: Exception to handle
            context: Context where the error occurred
        """
        error_message = f"{type(error).__name__}: {str(error)}"
        self.logger.error(f"Error in {context}: {error_message}")
        
        # Send email notification if configured
        if self.config.sendgrid_api_key and self.config.notification_email_from and self.config.notification_email_to:
            send_error_notification(
                self.config,
                f"Error in {context}",
                error_message,
                self.logger
            )
