import { startScheduler } from '../scheduler';
import { Config } from '../config';
import { syncTogglToGithub } from '../sync';

// Mock dependencies
jest.mock('../sync', () => ({
  syncTogglToGithub: jest.fn().mockResolvedValue(true),
}));

jest.mock('node-cron', () => ({
  schedule: jest.fn().mockReturnValue({
    start: jest.fn(),
    stop: jest.fn(),
  }),
  validate: jest.fn().mockReturnValue(true),
}));

/**
 * Jest tests for the scheduler
 */
describe('Scheduler', () => {
  // Mock config
  const mockConfig: Config = {
    togglApiToken: 'test_token',
    githubToken: 'test_token',
    githubRepo: 'test/repo',
    githubWorklogPath: 'test/path',
    timezone: 'America/Los_Angeles',
    syncIntervalMinutes: 60,
    logger: {
      info: jest.fn(),
      error: jest.fn(),
      debug: jest.fn(),
      warn: jest.fn(),
    } as any,
  };

  // Import node-cron after mocking
  const nodeCron = require('node-cron');
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should start the scheduler with correct interval', () => {
    // Call the function
    startScheduler(mockConfig);
    
    // Verify cron expression was validated
    expect(nodeCron.validate).toHaveBeenCalledWith('0 */60 * * * *');
    
    // Verify scheduler was created with correct parameters
    expect(nodeCron.schedule).toHaveBeenCalledWith(
      '0 */60 * * * *',
      expect.any(Function)
    );
    
    // Verify scheduler was started
    expect(nodeCron.schedule().start).toHaveBeenCalled();
    
    // Verify sync was called immediately
    expect(syncTogglToGithub).toHaveBeenCalledWith(mockConfig);
  });

  it('should handle process termination signals', () => {
    // Store original process.on
    const originalProcessOn = process.on;
    
    // Mock process.on
    const mockProcessOn = jest.fn();
    process.on = mockProcessOn;
    
    // Call the function
    startScheduler(mockConfig);
    
    // Verify process.on was called for SIGINT and SIGTERM
    expect(mockProcessOn).toHaveBeenCalledWith('SIGINT', expect.any(Function));
    expect(mockProcessOn).toHaveBeenCalledWith('SIGTERM', expect.any(Function));
    
    // Restore original process.on
    process.on = originalProcessOn;
  });

  it('should throw error for invalid cron expression', () => {
    // Mock validate to return false
    nodeCron.validate.mockReturnValueOnce(false);
    
    // Call the function and expect error
    expect(() => startScheduler(mockConfig)).toThrow('Invalid cron expression');
  });
});
