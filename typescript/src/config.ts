import * as winston from 'winston';
import * as dotenv from 'dotenv';
import { Logger } from 'winston';
import { setupLogger } from './utils/error-handler';

export interface Config {
  // Toggl API
  togglApiToken: string;
  
  // GitHub API
  githubToken: string;
  githubRepo: string;
  githubWorklogPath: string;
  
  // Time Zone
  timezone: string;
  
  // SendGrid
  sendgridApiKey?: string;
  notificationEmail?: string;
  
  // Scheduling
  syncIntervalMinutes: number;
  
  // Logging
  logLevel?: string;
  logFile?: string;
  logger: Logger;
}

/**
 * Load configuration from environment variables
 * @returns Application configuration
 * @throws Error if required configuration is missing
 */
export function loadConfig(): Config {
  // Load environment variables from .env file if it exists
  dotenv.config();
  
  // Required configuration
  const togglApiToken = process.env.TOGGL_API_TOKEN;
  const githubToken = process.env.GITHUB_TOKEN;
  const githubRepo = process.env.GITHUB_REPO;
  const githubWorklogPath = process.env.GITHUB_WORKLOG_PATH;
  
  // Validate required configuration
  if (!togglApiToken) {
    throw new Error('TOGGL_API_TOKEN environment variable is required');
  }
  if (!githubToken) {
    throw new Error('GITHUB_TOKEN environment variable is required');
  }
  if (!githubRepo) {
    throw new Error('GITHUB_REPO environment variable is required');
  }
  if (!githubWorklogPath) {
    throw new Error('GITHUB_WORKLOG_PATH environment variable is required');
  }
  
  // Optional configuration
  const timezone = process.env.TIMEZONE || 'America/Los_Angeles';
  const sendgridApiKey = process.env.SENDGRID_API_KEY;
  const notificationEmailFrom = process.env.NOTIFICATION_EMAIL_FROM;
  const notificationEmailTo = process.env.NOTIFICATION_EMAIL_TO;
  const logLevel = process.env.LOG_LEVEL;
  const logFile = process.env.LOG_FILE;
  
  // Parse numeric values
  const syncIntervalMinutes = parseInt(process.env.SYNC_INTERVAL_MINUTES || '60', 10);
  
  // Initialize logger
  const logger = setupLogger({
    logLevel,
    logFile,
  });
  
  return {
    togglApiToken,
    githubToken,
    githubRepo,
    githubWorklogPath,
    timezone,
    sendgridApiKey,
    notificationEmailFrom,
    notificationEmailTo,
    syncIntervalMinutes,
    logLevel,
    logFile,
    logger,
  };
}
