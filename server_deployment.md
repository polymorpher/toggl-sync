# Server Deployment Instructions

This document provides instructions for deploying the Toggl to GitHub sync application on a server. The application is available in both Python and TypeScript implementations, and you can choose the one that best fits your environment.

## Prerequisites

- A server with SSH access
- Git installed
- For Python implementation:
  - Python 3.8+ installed
  - pip installed
- For TypeScript implementation:
  - Node.js 14+ installed
  - npm installed

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/toggl-github-sync.git
cd toggl-github-sync
```

### 2. Choose Implementation

#### Python Implementation

1. Navigate to the Python directory:
   ```bash
   cd python
   ```

2. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .
   ```

4. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. Test the application:
   ```bash
   python -m toggl_github_sync
   ```

6. Set up as a service (systemd on Linux):
   
   Create a systemd service file at `/etc/systemd/system/toggl-github-sync.service`:
   ```
   [Unit]
   Description=Toggl to GitHub Sync Service
   After=network.target

   [Service]
   User=your-username
   WorkingDirectory=/path/to/toggl-github-sync/python
   ExecStart=/path/to/toggl-github-sync/python/venv/bin/python -m toggl_github_sync --schedule
   Restart=on-failure
   RestartSec=5
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```

7. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable toggl-github-sync
   sudo systemctl start toggl-github-sync
   ```

8. Check the service status:
   ```bash
   sudo systemctl status toggl-github-sync
   ```

#### TypeScript Implementation

1. Navigate to the TypeScript directory:
   ```bash
   cd typescript
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the application:
   ```bash
   npm run build
   ```

4. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. Test the application:
   ```bash
   npm start
   ```

6. Set up as a service (systemd on Linux):
   
   Create a systemd service file at `/etc/systemd/system/toggl-github-sync.service`:
   ```
   [Unit]
   Description=Toggl to GitHub Sync Service
   After=network.target

   [Service]
   User=your-username
   WorkingDirectory=/path/to/toggl-github-sync/typescript
   ExecStart=/usr/bin/node /path/to/toggl-github-sync/typescript/dist/index.js
   Restart=always
   RestartSec=10
   Environment=NODE_ENV=production

   [Install]
   WantedBy=multi-user.target
   ```

7. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable toggl-github-sync
   sudo systemctl start toggl-github-sync
   ```

8. Check the service status:
   ```bash
   sudo systemctl status toggl-github-sync
   ```

### 3. Set Up Environment Variables

Both implementations require the following environment variables:

- `TOGGL_API_TOKEN`: Your Toggl API token
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_REPO`: GitHub repository in format `owner/repo`
- `GITHUB_WORKLOG_PATH`: Path to your worklog file in the repository

Optional environment variables:

- `TIMEZONE`: Timezone for date calculations (default: America/Los_Angeles)
- `SYNC_INTERVAL_MINUTES`: Sync interval in minutes (default: 60)
- `SENDGRID_API_KEY`: SendGrid API key for error notifications
- `NOTIFICATION_EMAIL_FROM`: Email address for sending error notifications
- `NOTIFICATION_EMAIL_TO`: Email address for receiving error notifications
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Path to log file (if not specified, logs to console only)

### 4. Monitoring and Maintenance

- Check the logs:
  - If using systemd: `sudo journalctl -u toggl-github-sync`
  - If using a log file: Check the file specified in `LOG_FILE`

- Restart the service after configuration changes:
  ```bash
  sudo systemctl restart toggl-github-sync
  ```

- Update the application:
  ```bash
  cd /path/to/toggl-github-sync
  git pull
  
  # For Python:
  cd python
  source venv/bin/activate
  pip install -e .
  
  # For TypeScript:
  cd typescript
  npm install
  npm run build
  
  # Restart the service
  sudo systemctl restart toggl-github-sync
  ```

## Troubleshooting

- If the service fails to start, check the logs:
  ```bash
  sudo journalctl -u toggl-github-sync -n 50
  ```

- Verify that all required environment variables are set correctly in the `.env` file

- Ensure that the GitHub token has the necessary permissions to update the repository

- Test the application manually to verify it can connect to both Toggl and GitHub:
  ```bash
  # For Python:
  cd /path/to/toggl-github-sync/python
  source venv/bin/activate
  python -m toggl_github_sync
  
  # For TypeScript:
  cd /path/to/toggl-github-sync/typescript
  npm start
  ```

- If using SendGrid for error notifications, verify that the API key is valid and the email address is correct
