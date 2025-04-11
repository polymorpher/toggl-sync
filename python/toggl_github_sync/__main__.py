"""Main module for toggl_github_sync package."""

import argparse
import logging
import sys
from datetime import datetime
from typing import NoReturn

from toggl_github_sync.config import load_config
from toggl_github_sync.scheduler import start_scheduler
from toggl_github_sync.sync import sync_toggl_to_github

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> datetime:
    """Parse a date string in YYYY-MM-DD format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        datetime object
        
    Raises:
        ValueError: If date string is invalid
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format")


def main() -> NoReturn:
    """Run the main application."""
    parser = argparse.ArgumentParser(description="Sync Toggl time entries to GitHub worklog")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run with scheduler (default: run once and exit)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date for sync in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date for sync in YYYY-MM-DD format (default: today)",
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    # Parse dates if provided
    start_date = parse_date(args.start_date) if args.start_date else None
    end_date = parse_date(args.end_date) if args.end_date else None
    
    if args.schedule:
        logger.info("Starting scheduler")
        start_scheduler(config)
    else:
        logger.info("Running sync once")
        if start_date or end_date:
            logger.info(f"Syncing date range: {start_date or 'today'} to {end_date or 'today'}")
        sync_toggl_to_github(config, start_date=start_date, end_date=end_date)
        logger.info("Sync completed")


if __name__ == "__main__":
    main()
