# GitHub Actions Deployment Setup

This document provides instructions for setting up GitHub Actions to automatically run the Toggl to GitHub sync application. This approach is useful if you want to run the sync process directly within GitHub's infrastructure without maintaining a separate server.

## Overview

GitHub Actions allows you to run workflows in response to various events. For this application, we'll set up a workflow that:

1. Runs on a schedule (hourly by default)
2. Retrieves your Toggl time entries
3. Updates your GitHub worklog file

## Setup Instructions

### 1. Create GitHub Actions Workflow File

Create a new file in your repository at `.github/workflows/toggl-sync.yml` with the following content:

#### For Python Implementation

```yaml
name: Toggl to GitHub Sync

on:
  schedule:
    # Run every hour at minute 0
    - cron: '0 * * * *'
  # Optional: Allow manual triggering
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          cd python
          pip install -e .
          
      - name: Run sync
        env:
          TOGGL_API_TOKEN: ${{ secrets.TOGGL_API_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.TOGGL_GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          GITHUB_WORKLOG_PATH: 'progress/aaron-li.md'
          TIMEZONE: 'America/Los_Angeles'
          SYNC_INTERVAL_MINUTES: '60'
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          NOTIFICATION_EMAIL_FROM: ${{ secrets.NOTIFICATION_EMAIL_FROM }}
          NOTIFICATION_EMAIL_TO: ${{ secrets.NOTIFICATION_EMAIL_TO }}
        run: |
          cd python
          python -m toggl_github_sync
```

#### For TypeScript Implementation

```yaml
name: Toggl to GitHub Sync

on:
  schedule:
    # Run every hour at minute 0
    - cron: '0 * * * *'
  # Optional: Allow manual triggering
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
        
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '16'
          
      - name: Install dependencies
        run: |
          cd typescript
          npm install
          
      - name: Build application
        run: |
          cd typescript
          npm run build
          
      - name: Run sync
        env:
          TOGGL_API_TOKEN: ${{ secrets.TOGGL_API_TOKEN }}
          GITHUB_TOKEN: ${{ secrets.TOGGL_GITHUB_TOKEN }}
          GITHUB_REPO: ${{ github.repository }}
          GITHUB_WORKLOG_PATH: 'progress/aaron-li.md'
          TIMEZONE: 'America/Los_Angeles'
          SYNC_INTERVAL_MINUTES: '60'
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          NOTIFICATION_EMAIL_FROM: ${{ secrets.NOTIFICATION_EMAIL_FROM }}
          NOTIFICATION_EMAIL_TO: ${{ secrets.NOTIFICATION_EMAIL_TO }}
        run: |
          cd typescript
          node dist/index.js
```

### 2. Set Up GitHub Secrets

You need to add the following secrets to your GitHub repository:

1. Go to your repository on GitHub
2. Navigate to Settings > Secrets and variables > Actions
3. Add the following secrets:
   - `TOGGL_API_TOKEN`: Your Toggl API token
   - `TOGGL_GITHUB_TOKEN`: A GitHub personal access token with repo scope
   - `SENDGRID_API_KEY`: (Optional) Your SendGrid API key for error notifications
   - `NOTIFICATION_EMAIL_FROM`: (Optional) Email address for sending error notifications
   - `NOTIFICATION_EMAIL_TO`: (Optional) Email address for receiving error notifications

> **Important Note**: We use `TOGGL_GITHUB_TOKEN` instead of the default `GITHUB_TOKEN` because the default token provided by GitHub Actions doesn't trigger workflows when used to make commits. This prevents infinite loops of workflow runs.

### 3. Customize the Workflow

You may want to customize the workflow file:

- **Schedule**: Modify the cron expression to change when the sync runs
- **Worklog Path**: Update `GITHUB_WORKLOG_PATH` to point to your worklog file
- **Timezone**: Change `TIMEZONE` to match your preferred timezone
- **Sync Interval**: Adjust `SYNC_INTERVAL_MINUTES` if needed

### 4. Commit and Push

Commit the workflow file to your repository and push it to GitHub:

```bash
git add .github/workflows/toggl-sync.yml
git commit -m "Add Toggl to GitHub sync workflow"
git push
```

### 5. Verify the Workflow

1. Go to your repository on GitHub
2. Navigate to the "Actions" tab
3. You should see your workflow listed
4. You can manually trigger the workflow by clicking on "Toggl to GitHub Sync" and then "Run workflow"

## Troubleshooting

- **Workflow not running**: Check if the workflow is enabled in the Actions tab
- **Authentication errors**: Verify that your secrets are set correctly
- **Commit errors**: Ensure that the `TOGGL_GITHUB_TOKEN` has the necessary permissions
- **Workflow logs**: Check the workflow run logs for detailed error messages

## Limitations

- GitHub Actions workflows that are triggered by the `schedule` event may be delayed during periods of high GitHub usage
- There is a limit to the number of GitHub Actions minutes you can use per month, depending on your account type
- The workflow will not run if the repository is archived

## Security Considerations

- The `TOGGL_GITHUB_TOKEN` should have the minimum necessary permissions (repo scope)
- Consider using repository environments with protection rules for production deployments
- Regularly rotate your API tokens and secrets
