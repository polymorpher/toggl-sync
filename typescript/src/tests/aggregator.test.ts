import { TimeEntryAggregator } from '../aggregator';
import { TogglApiClient } from '../api/toggl';
import { Config } from '../config';

/**
 * Jest tests for the TimeEntryAggregator
 */
describe('TimeEntryAggregator', () => {
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

  // Mock TogglApiClient
  const mockTogglClient = {
    getEntriesByDate: jest.fn(),
    calculateDailyHours: jest.fn(),
    getCurrentTimeEntry: jest.fn(),
    getEntriesDescriptions: jest.fn(),
  } as unknown as TogglApiClient;

  let aggregator: TimeEntryAggregator;
  
  beforeEach(() => {
    jest.clearAllMocks();
    aggregator = new TimeEntryAggregator(mockConfig, mockTogglClient as TogglApiClient);
  });

  describe('aggregateDailyEntries', () => {
    it('should aggregate entries for a day', async () => {
      // Setup mock responses
      mockTogglClient.getEntriesByDate.mockResolvedValue([
        { id: 1, workspace_id: 1, start: '2025-04-09T08:00:00Z', duration: 3600, description: 'Task 1' },
        { id: 2, workspace_id: 1, start: '2025-04-09T09:00:00Z', duration: 1800, description: 'Task 2' },
      ]);
      mockTogglClient.calculateDailyHours.mockReturnValue(1.5);
      mockTogglClient.getCurrentTimeEntry.mockResolvedValue(null);
      mockTogglClient.getEntriesDescriptions.mockReturnValue(['Task 1', 'Task 2']);
      
      // Call the method
      const testDate = new Date('2025-04-09T12:00:00Z');
      const [entry, hours, hasRunning] = await aggregator.aggregateDailyEntries(testDate);
      
      // Assertions
      expect(hours).toEqual(1.5);
      expect(hasRunning).toBe(false);
      expect(entry).toContain('2025-4-9 Wed (1.5h): Task 1. Task 2.');
      
      // Verify method calls
      expect(mockTogglClient.getEntriesByDate).toHaveBeenCalledWith(testDate);
      expect(mockTogglClient.calculateDailyHours).toHaveBeenCalled();
      expect(mockTogglClient.getCurrentTimeEntry).toHaveBeenCalled();
      expect(mockTogglClient.getEntriesDescriptions).toHaveBeenCalled();
    });

    it('should handle running entries', async () => {
      // Setup mock responses
      mockTogglClient.getEntriesByDate.mockResolvedValue([
        { id: 1, workspace_id: 1, start: '2025-04-09T08:00:00Z', duration: 3600, description: 'Task 1' },
        { id: 2, workspace_id: 1, start: '2025-04-09T10:00:00Z', duration: -1, description: 'Running task' },
      ]);
      mockTogglClient.calculateDailyHours.mockReturnValue(1.8);
      mockTogglClient.getCurrentTimeEntry.mockResolvedValue({
        id: 2, workspace_id: 1, start: '2025-04-09T10:00:00Z', duration: -1, description: 'Running task'
      });
      mockTogglClient.getEntriesDescriptions.mockReturnValue(['Task 1', 'Running task']);
      
      // Call the method
      const testDate = new Date('2025-04-09T12:00:00Z');
      const [entry, hours, hasRunning] = await aggregator.aggregateDailyEntries(testDate);
      
      // Assertions
      expect(hours).toEqual(1.8);
      expect(hasRunning).toBe(true);
      expect(entry).toContain('2025-4-9 Wed (1.8h+): Task 1. Running task.');
    });
  });

  describe('formatWorklogEntry', () => {
    it('should format entries correctly', () => {
      // Test with multiple descriptions
      const testDate = new Date('2025-04-09T12:00:00Z');
      const entry = aggregator.formatWorklogEntry(
        testDate,
        2.5,
        ['Task 1', 'Task 2', 'Task 3'],
        false
      );
      expect(entry).toContain('2025-4-9 Wed (2.5h): Task 1. Task 2. Task 3.');
      
      // Test with running entry
      const entryWithRunning = aggregator.formatWorklogEntry(
        testDate,
        3.0,
        ['Task 1'],
        true
      );
      expect(entryWithRunning).toContain('2025-4-9 Wed (3.0h+): Task 1.');
      
      // Test with no descriptions
      const emptyEntry = aggregator.formatWorklogEntry(
        testDate,
        1.0,
        [],
        false
      );
      expect(emptyEntry).toContain('2025-4-9 Wed (1.0h): ');
    });
  });
});
