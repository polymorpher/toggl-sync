"""Scheduler module for toggl_github_sync."""

import logging
import time
from typing import NoReturn

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from toggl_github_sync.config import Config
from toggl_github_sync.sync import sync_toggl_to_github

logger = logging.getLogger(__name__)


def start_scheduler(config: Config) -> NoReturn:
    """Start the scheduler to run sync at specified intervals.
    
    Args:
        config: Application configuration
        
    Returns:
        This function does not return (runs indefinitely)
    """
    scheduler = BackgroundScheduler()
    
    # Add job to run at specified interval
    scheduler.add_job(
        sync_toggl_to_github,
        trigger=IntervalTrigger(minutes=config.sync_interval_minutes),
        args=[config],
        id="toggl_github_sync",
        name="Sync Toggl to GitHub",
        replace_existing=True,
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info(
        f"Scheduler started. Will sync every {config.sync_interval_minutes} minutes."
    )
    
    # Run once immediately
    sync_toggl_to_github(config)
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler stopped")
        
    # This point is never reached during normal operation
    return
