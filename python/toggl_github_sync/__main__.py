"""Main module for toggl_github_sync package."""

import argparse
import logging
import sys
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


def main() -> NoReturn:
    """Run the main application."""
    parser = argparse.ArgumentParser(description="Sync Toggl time entries to GitHub worklog")
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run with scheduler (default: run once and exit)",
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    
    if args.schedule:
        logger.info("Starting scheduler")
        start_scheduler(config)
    else:
        logger.info("Running sync once")
        sync_toggl_to_github(config)
        logger.info("Sync completed")


if __name__ == "__main__":
    main()
