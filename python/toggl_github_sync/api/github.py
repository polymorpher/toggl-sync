"""GitHub API client implementation."""

import base64
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import pytz
from github import Github, GithubException
from github.ContentFile import ContentFile
from github.Repository import Repository

from toggl_github_sync.config import Config

logger = logging.getLogger(__name__)

class GitHubApiClient:
    """Client for interacting with the GitHub API."""

    def __init__(self, config: Config):
        """Initialize the GitHub API client.
        
        Args:
            config: Application configuration
        """
        self.github = Github(config.github_token)
        self.repo_name = config.github_repo
        self.worklog_path = config.github_worklog_path
        self.timezone = pytz.timezone(config.timezone)
        
    def get_worklog_content(self) -> Tuple[str, str]:
        """Get the current content of the worklog file.
        
        Returns:
            Tuple of (content, sha)
        """
        logger.info(f"Fetching worklog content from {self.repo_name}/{self.worklog_path}")
        
        repo = self.github.get_repo(self.repo_name)
        try:
            file_content = repo.get_contents(self.worklog_path)
            if isinstance(file_content, List):
                raise ValueError(f"Expected a file, but {self.worklog_path} is a directory")
            
            content = base64.b64decode(file_content.content).decode('utf-8')
            return content, file_content.sha
        except GithubException as e:
            logger.error(f"Error getting worklog content: {e}")
            raise
    
    def update_worklog(self, new_content: str, sha: str) -> bool:
        """Update the worklog file with new content.
        
        Args:
            new_content: New content for the worklog file
            sha: SHA of the current file content
            
        Returns:
            True if update was successful
        """
        logger.info(f"Updating worklog content in {self.repo_name}/{self.worklog_path}")
        
        repo = self.github.get_repo(self.repo_name)
        try:
            repo.update_file(
                path=self.worklog_path,
                message="Update worklog with Toggl time entries",
                content=new_content,
                sha=sha,
            )
            logger.info("Worklog updated successfully")
            return True
        except GithubException as e:
            logger.error(f"Error updating worklog: {e}")
            raise
    
    def find_entry_for_date(self, content: str, date: datetime) -> Optional[Tuple[str, int, int]]:
        """Find an existing entry for the given date in the worklog content.
        
        Args:
            content: Worklog content
            date: Date to find
            
        Returns:
            Tuple of (entry, start_index, end_index) if found, None otherwise
        """
        # Format date as YYYY-M-D
        date_str = date.strftime("%Y-%-m-%-d")
        
        # Look for an entry starting with the date
        # More robust pattern that handles:
        # - Optional spaces after date
        # - Any day name (not just English)
        # - Various hour formats
        # - Multi-line descriptions
        pattern = rf"({date_str}\s+[A-Za-z]+\s*\(\d+\.?\d*h\+?\):\s*.+?)(?=\n\n|\n\*|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
        
        if match:
            entry = match.group(1)
            start_index = match.start()
            end_index = match.end()
            logger.info(f"Found existing entry for {date_str}: {entry[:50]}...")
            return entry, start_index, end_index
        else:
            logger.warning(f"No existing entry found for {date_str}")
            return None
    
    def update_or_create_entry(self, content: str, new_entry: str, date: datetime) -> str:
        """Update an existing entry or create a new one.
        
        Args:
            content: Current worklog content
            new_entry: New entry to add or update
            date: Date of the entry
            
        Returns:
            Updated worklog content
        """
        # Check if there's already an entry for the date
        existing_entry = self.find_entry_for_date(content, date)
        
        if existing_entry:
            # Update existing entry
            entry, start_index, end_index = existing_entry
            updated_content = (
                content[:start_index] + 
                new_entry + 
                content[end_index:]
            )
            logger.info(f"Updated existing entry for {date.strftime('%Y-%-m-%-d')}")
        else:
            # Add new entry at the top
            if content.startswith("# "):
                # If the file starts with a title, add after the title
                title_end = content.find("\n") + 1
                updated_content = (
                    content[:title_end] + 
                    "\n" + new_entry + "\n\n" + 
                    content[title_end:]
                )
            else:
                # Otherwise, add at the very top
                updated_content = new_entry + "\n\n" + content
            logger.info(f"Added new entry for {date.strftime('%Y-%-m-%-d')}")
        
        return updated_content
