# Testing Instructions

This document provides instructions for testing the Toggl to GitHub sync application to ensure it works correctly before deployment.

## Prerequisites

Before testing, you'll need:

1. A Toggl account with some time entries
2. A GitHub repository where you have write access
3. A test worklog file in your GitHub repository

## Setting Up Test Environment

### 1. Create Test Environment Variables

Create a `.env.test` file in either the Python or TypeScript directory with your test credentials:

```
TOGGL_API_TOKEN=your_toggl_api_token
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=your_username/your_test_repo
GITHUB_WORKLOG_PATH=path/to/test_worklog.md
TIMEZONE=America/Los_Angeles
SYNC_INTERVAL_MINUTES=60
```

### 2. Create a Test Worklog File

If you don't already have a worklog file in your test repository, create one with some sample content:

```markdown
# Test Worklog

2025-4-8 Tue (2.0h): Initial test entry.
```

## Running Tests

### Python Implementation

1. Navigate to the Python directory:
   ```bash
   cd python
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Run the unit tests:
   ```bash
   python -m unittest discover
   ```

5. Run a manual sync with test environment:
   ```bash
   # Load test environment variables
   export $(cat .env.test | xargs)
   
   # Run the sync
   python -m toggl_github_sync
   ```

### TypeScript Implementation

1. Navigate to the TypeScript directory:
   ```bash
   cd typescript
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the unit tests:
   ```bash
   npm test
   ```

4. Build the application:
   ```bash
   npm run build
   ```

5. Run a manual sync with test environment:
   ```bash
   # Load test environment variables
   export $(cat .env.test | xargs)
   
   # Run the sync
   node dist/index.js
   ```

## Verification Steps

After running the sync, verify that:

1. The application ran without errors
2. Your GitHub worklog file was updated with your Toggl time entries for today
3. The format matches the expected pattern: `YYYY-M-D Day (Xh): Description`
4. If you had a running time entry, it should be marked with a plus sign: `(Xh+)`

## Testing Error Handling

To test error handling and notifications:

1. Set up SendGrid credentials in your test environment:
   ```
   SENDGRID_API_KEY=your_sendgrid_api_key
   NOTIFICATION_EMAIL_FROM=your_email@example.com
   NOTIFICATION_EMAIL_TO=your_email@example.com
   ```

2. Introduce an error by providing an invalid token:
   ```
   TOGGL_API_TOKEN=invalid_token
   ```

3. Run the sync and verify that:
   - The application logs the error
   - You receive an email notification about the error

## Testing Scheduler

To test the scheduler functionality:

1. Set a short interval for testing:
   ```
   SYNC_INTERVAL_MINUTES=2
   ```

2. Run the application and let it run for at least 5 minutes:
   ```bash
   # Python
   python -m toggl_github_sync
   
   # TypeScript
   node dist/index.js
   ```

3. Verify that the sync runs multiple times at the specified interval

## Common Issues and Solutions

- **Authentication errors**: Verify that your API tokens are correct and have the necessary permissions
- **Rate limiting**: If you hit rate limits, increase the sync interval
- **Format mismatches**: Check that your worklog file follows the expected format
- **Timezone issues**: Verify that your timezone setting matches your Toggl account timezone

## Next Steps

Once you've verified that the application works correctly in your test environment, you can proceed to deploy it using either the server deployment or GitHub Actions methods described in the deployment documentation.
