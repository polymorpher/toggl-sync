import { loadConfig } from '../config';
import * as dotenv from 'dotenv';
import * as winston from 'winston';

/**
 * Jest tests for the configuration module
 */
describe('Config', () => {
  // Store original process.env
  const originalEnv = process.env;
  
  // Mock winston
  jest.mock('winston', () => ({
    createLogger: jest.fn().mockReturnValue({
      info: jest.fn(),
      error: jest.fn(),
      warn: jest.fn(),
      debug: jest.fn(),
    }),
    format: {
      combine: jest.fn(),
      timestamp: jest.fn(),
      printf: jest.fn(),
      json: jest.fn(),
    },
    transports: {
      Console: jest.fn(),
      File: jest.fn(),
    },
  }));
  
  beforeEach(() => {
    // Reset process.env before each test
    process.env = { ...originalEnv };
    jest.clearAllMocks();
  });
  
  afterAll(() => {
    // Restore process.env
    process.env = originalEnv;
  });

  it('should load configuration from environment variables', () => {
    // Set environment variables
    process.env.TOGGL_API_TOKEN = 'test_toggl_token';
    process.env.GITHUB_TOKEN = 'test_github_token';
    process.env.GITHUB_REPO = 'test/repo';
    process.env.GITHUB_WORKLOG_PATH = 'progress/test.md';
    process.env.TIMEZONE = 'US/Pacific';
    process.env.SENDGRID_API_KEY = 'test_sendgrid_key';
    process.env.NOTIFICATION_EMAIL_FROM = 'from@example.com';
    process.env.NOTIFICATION_EMAIL_TO = 'to@example.com';
    process.env.SYNC_INTERVAL_MINUTES = '30';
    process.env.LOG_LEVEL = 'debug';
    process.env.LOG_FILE = '/tmp/test.log';
    
    // Load configuration
    const config = loadConfig();
    
    // Verify required configuration
    expect(config.togglApiToken).toBe('test_toggl_token');
    expect(config.githubToken).toBe('test_github_token');
    expect(config.githubRepo).toBe('test/repo');
    expect(config.githubWorklogPath).toBe('progress/test.md');
    
    // Verify optional configuration
    expect(config.timezone).toBe('US/Pacific');
    expect(config.sendgridApiKey).toBe('test_sendgrid_key');
    expect(config.notificationEmail).toBe('test@example.com');
    expect(config.syncIntervalMinutes).toBe(30);
    expect(config.logLevel).toBe('debug');
    expect(config.logFile).toBe('/tmp/test.log');
    expect(config.logger).toBeDefined();
  });

  it('should use default values when optional configuration is missing', () => {
    // Set only required environment variables
    process.env.TOGGL_API_TOKEN = 'test_toggl_token';
    process.env.GITHUB_TOKEN = 'test_github_token';
    process.env.GITHUB_REPO = 'test/repo';
    process.env.GITHUB_WORKLOG_PATH = 'progress/test.md';
    
    // Load configuration
    const config = loadConfig();
    
    // Verify default values
    expect(config.timezone).toBe('America/Los_Angeles');
    expect(config.sendgridApiKey).toBeUndefined();
    expect(config.notificationEmail).toBeUndefined();
    expect(config.syncIntervalMinutes).toBe(60);
    expect(config.logLevel).toBeUndefined();
    expect(config.logFile).toBeUndefined();
    expect(config.logger).toBeDefined();
  });

  it('should throw error when required configuration is missing', () => {
    // No environment variables set
    expect(() => loadConfig()).toThrow('TOGGL_API_TOKEN environment variable is required');
    
    // Set only some required variables
    process.env.TOGGL_API_TOKEN = 'test_toggl_token';
    expect(() => loadConfig()).toThrow('GITHUB_TOKEN environment variable is required');
    
    process.env.GITHUB_TOKEN = 'test_github_token';
    expect(() => loadConfig()).toThrow('GITHUB_REPO environment variable is required');
    
    process.env.GITHUB_REPO = 'test/repo';
    expect(() => loadConfig()).toThrow('GITHUB_WORKLOG_PATH environment variable is required');
  });

  it('should handle invalid numeric values', () => {
    // Set required environment variables
    process.env.TOGGL_API_TOKEN = 'test_toggl_token';
    process.env.GITHUB_TOKEN = 'test_github_token';
    process.env.GITHUB_REPO = 'test/repo';
    process.env.GITHUB_WORKLOG_PATH = 'progress/test.md';
    
    // Set invalid numeric value
    process.env.SYNC_INTERVAL_MINUTES = 'invalid';
    
    // Load configuration
    const config = loadConfig();
    
    // Should use default value for invalid numeric input
    expect(config.syncIntervalMinutes).toBe(60);
  });
});
