# Toggl to GitHub Worklog Sync

This application automatically retrieves your time entries from Toggl, aggregates them by day, and synchronizes them to your GitHub worklog file. It runs on a schedule (hourly by default) to keep your worklog up-to-date with minimal effort.

## Features

- Retrieves time entries from Toggl API
- Aggregates entries by day with total hours
- Formats entries according to your existing worklog pattern
- Updates your GitHub worklog file
- Runs on a schedule (hourly by default)
- Handles running time entries (marked with "+")
- Supports timezone configuration (US Pacific Time by default)
- Provides error notifications via email (using SendGrid)
- Available in both Python and TypeScript implementations

## Implementations

This repository contains two independent implementations of the same functionality:

- **Python**: Located in the `python/` directory
- **TypeScript**: Located in the `typescript/` directory

You can choose the implementation that best fits your environment and preferences.

## Prerequisites

### Python Implementation
- Python 3.8 or higher
- pip (Python package manager)

### TypeScript Implementation
- Node.js 14 or higher
- npm (Node.js package manager)

## Configuration

Both implementations use the following environment variables for configuration:

### Required
- `TOGGL_API_TOKEN`: Your Toggl API token
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_REPO`: GitHub repository in format `owner/repo`
- `GITHUB_WORKLOG_PATH`: Path to your worklog file in the repository

### Optional
- `TIMEZONE`: Timezone for date calculations (default: America/Los_Angeles)
- `SYNC_INTERVAL_MINUTES`: Sync interval in minutes (default: 60)
- `SENDGRID_API_KEY`: SendGrid API key for error notifications
- `NOTIFICATION_EMAIL_FROM`: Email address for sending error notifications
- `NOTIFICATION_EMAIL_TO`: Email address for receiving error notifications
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Path to log file (if not specified, logs to console only)

## Installation and Usage

See the following documents for detailed instructions:

- [Testing Instructions](testing_instructions.md)
- [Server Deployment](server_deployment.md)
- [GitHub Actions Deployment](github_actions_deployment.md)

## Development

### Python Implementation

```bash
# Clone the repository
git clone https://github.com/your-username/toggl-github-sync.git
cd toggl-github-sync/python

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Run tests
python -m unittest discover

# Run the application
python -m toggl_github_sync
```

### TypeScript Implementation

```bash
# Clone the repository
git clone https://github.com/your-username/toggl-github-sync.git
cd toggl-github-sync/typescript

# Install dependencies
npm install

# Run tests
npm test

# Build the application
npm run build

# Run the application
npm start
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
