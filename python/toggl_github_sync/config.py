"""Configuration management module."""

import logging
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for toggl_github_sync."""
    
    # Toggl API
    toggl_api_token: str
    
    # GitHub API
    github_token: str
    github_repo: str
    github_worklog_path: str
    
    # Time Zone
    timezone: str = "America/Los_Angeles"  # Default to US Pacific Time
    
    # SendGrid
    sendgrid_api_key: Optional[str] = None
    notification_email_from: Optional[str] = None
    notification_email_to: Optional[str] = None
    
    # Scheduling
    sync_interval_minutes: int = 60  # Default to hourly
    
    # Logging
    log_level: int = logging.INFO
    log_file: Optional[str] = None


def load_config() -> Config:
    """Load configuration from environment variables.
    
    Returns:
        Application configuration
    
    Raises:
        ValueError: If required configuration is missing
    """
    # Load environment variables from .env file if it exists
    load_dotenv()
    
    # Required configuration
    toggl_api_token = os.getenv("TOGGL_API_TOKEN")
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")
    github_worklog_path = os.getenv("GITHUB_WORKLOG_PATH")
    
    # Validate required configuration
    if not toggl_api_token:
        raise ValueError("TOGGL_API_TOKEN environment variable is required")
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is required")
    if not github_repo:
        raise ValueError("GITHUB_REPO environment variable is required")
    if not github_worklog_path:
        raise ValueError("GITHUB_WORKLOG_PATH environment variable is required")
    
    # Optional configuration
    timezone = os.getenv("TIMEZONE", "America/Los_Angeles")
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    notification_email_from = os.getenv("NOTIFICATION_EMAIL_FROM")
    notification_email_to = os.getenv("NOTIFICATION_EMAIL_TO")
    
    # Parse numeric values
    try:
        sync_interval_minutes = int(os.getenv("SYNC_INTERVAL_MINUTES", "60"))
    except ValueError:
        sync_interval_minutes = 60
        
    # Parse log level
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Log file
    log_file = os.getenv("LOG_FILE")
    
    return Config(
        toggl_api_token=toggl_api_token,
        github_token=github_token,
        github_repo=github_repo,
        github_worklog_path=github_worklog_path,
        timezone=timezone,
        sendgrid_api_key=sendgrid_api_key,
        notification_email_from=notification_email_from,
        notification_email_to=notification_email_to,
        sync_interval_minutes=sync_interval_minutes,
        log_level=log_level,
        log_file=log_file,
    )
