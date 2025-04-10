import { TogglApiClient, TogglTimeEntry } from '../api/toggl';
import { Config } from '../config';

/**
 * Jest tests for the Toggl API client
 */
describe('TogglApiClient', () => {
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

  // Mock axios
  jest.mock('axios', () => ({
    get: jest.fn(),
  }));

  let client: TogglApiClient;
  
  beforeEach(() => {
    client = new TogglApiClient(mockConfig);
    jest.clearAllMocks();
  });

  describe('calculateDailyHours', () => {
    it('should calculate hours from completed entries', () => {
      const entries: TogglTimeEntry[] = [
        { id: 1, workspace_id: 1, start: '2025-04-09T08:00:00Z', duration: 3600 },
        { id: 2, workspace_id: 1, start: '2025-04-09T09:00:00Z', duration: 1800 },
      ];

      const hours = client.calculateDailyHours(entries);
      expect(hours).toEqual(1.5);
    });

    it('should handle running entries', () => {
      // Mock Date.now
      const realDate = Date;
      global.Date = class extends Date {
        constructor() {
          super();
        }
        getTime() {
          return new realDate('2025-04-09T10:30:00Z').getTime();
        }
      } as any;

      const entries: TogglTimeEntry[] = [
        { id: 1, workspace_id: 1, start: '2025-04-09T08:00:00Z', duration: 3600 },
        { id: 2, workspace_id: 1, start: '2025-04-09T10:00:00Z', duration: -1 },
      ];

      const hours = client.calculateDailyHours(entries);
      
      // Reset Date
      global.Date = realDate;
      
      // Should be 1 hour completed + 30 minutes running = 1.5 hours
      expect(hours).toBeCloseTo(1.5, 1);
    });
  });

  describe('getEntriesDescriptions', () => {
    it('should extract descriptions from entries', () => {
      const entries: TogglTimeEntry[] = [
        { id: 1, workspace_id: 1, start: '2025-04-09T08:00:00Z', duration: 3600, description: 'Task 1' },
        { id: 2, workspace_id: 1, start: '2025-04-09T09:00:00Z', duration: 1800, description: 'Task 2' },
        { id: 3, workspace_id: 1, start: '2025-04-09T10:00:00Z', duration: 1800, description: '' },
        { id: 4, workspace_id: 1, start: '2025-04-09T10:30:00Z', duration: 1800, description: '  Task 4  ' },
      ];

      const descriptions = client.getEntriesDescriptions(entries);
      expect(descriptions).toEqual(['Task 1', 'Task 2', 'Task 4']);
    });

    it('should handle entries without descriptions', () => {
      const entries: TogglTimeEntry[] = [
        { id: 1, workspace_id: 1, start: '2025-04-09T08:00:00Z', duration: 3600 },
        { id: 2, workspace_id: 1, start: '2025-04-09T09:00:00Z', duration: 1800 },
      ];

      const descriptions = client.getEntriesDescriptions(entries);
      expect(descriptions).toEqual([]);
    });
  });
});
