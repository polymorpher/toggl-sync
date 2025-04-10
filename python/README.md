# Python Implementation Documentation

This document provides detailed information about the Python implementation of the Toggl to GitHub Worklog Sync application.

## Project Structure

```
python/
├── pyproject.toml         # Project metadata and dependencies
├── README.md              # Python-specific documentation
├── .env.example           # Example environment variables
├── toggl_github_sync/     # Main package
│   ├── __init__.py        # Package initialization
│   ├── __main__.py        # Entry point
│   ├── config.py          # Configuration management
│   ├── sync.py            # Main sync logic
│   ├── scheduler.py       # Scheduler for periodic sync
│   ├── formatter.py       # Worklog entry formatting
│   ├── aggregator.py      # Time entry aggregation
│   ├── api/               # API clients
│   │   ├── __init__.py
│   │   ├── toggl.py       # Toggl API client
│   │   └── github.py      # GitHub API client
│   ├── utils/             # Utility modules
│   │   ├── __init__.py
│   │   └── error_handler.py # Error handling and logging
│   └── tests/             # Unit tests
│       ├── __init__.py
│       ├── test_toggl.py
│       ├── test_github.py
│       ├── test_formatter.py
│       ├── test_aggregator.py
│       ├── test_config.py
│       ├── test_error_handler.py
│       └── test_scheduler.py
```

## Dependencies

The Python implementation uses the following main dependencies:

- `requests`: For making HTTP requests to the Toggl API
- `PyGithub`: For interacting with the GitHub API
- `python-dotenv`: For loading environment variables from .env files
- `apscheduler`: For scheduling periodic sync tasks
- `pytz`: For timezone handling
- `sendgrid`: For sending error notification emails

## Modules

### `config.py`

Handles loading and validating configuration from environment variables. Uses a dataclass to represent the application configuration.

### `api/toggl.py`

Client for interacting with the Toggl API. Provides methods for retrieving time entries, calculating daily hours, and extracting descriptions.

### `api/github.py`

Client for interacting with the GitHub API. Provides methods for getting worklog content, updating the worklog, and finding/updating entries for specific dates.

### `formatter.py`

Handles formatting worklog entries according to the required format. Provides methods for formatting entries, parsing existing entries, and merging entries.

### `aggregator.py`

Aggregates time entries by day. Calculates total hours, checks for running entries, and formats the worklog entry.

### `sync.py`

Main sync logic that ties everything together. Retrieves time entries from Toggl, formats them, and updates the GitHub worklog.

### `scheduler.py`

Handles scheduling periodic sync tasks using APScheduler. Runs the sync at specified intervals.

### `utils/error_handler.py`

Provides error handling and logging functionality. Includes SendGrid integration for email notifications.

### `__main__.py`

Entry point for the application. Sets up logging, loads configuration, and starts the scheduler.

## Error Handling

The application includes comprehensive error handling:

1. **Validation**: Validates required configuration before starting
2. **Exception Handling**: Catches and logs exceptions during execution
3. **Email Notifications**: Sends error notifications via SendGrid (if configured)
4. **Logging**: Logs errors to console and/or file

## Testing

The application includes unit tests for all major components. Tests can be run using:

```bash
python -m unittest discover
```

## Extending the Application

### Adding New Features

To add new features to the application:

1. Identify the appropriate module for your feature
2. Implement the feature with proper error handling
3. Add unit tests for the new functionality
4. Update documentation as needed

### Customizing Worklog Format

To customize the worklog entry format:

1. Modify the `format_entry` method in `formatter.py`
2. Update the regex pattern in `find_entry_for_date` in `api/github.py`
3. Update the parsing logic in `parse_entry` in `formatter.py`

## Performance Considerations

- The application is designed to run once per hour by default
- API requests are minimized to avoid rate limiting
- The application uses minimal resources when idle
