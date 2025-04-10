import { WorklogFormatter } from '../formatter';
import { Config } from '../config';

/**
 * Jest tests for the WorklogFormatter
 */
describe('WorklogFormatter', () => {
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
      warning: jest.fn(),
      error: jest.fn(),
      debug: jest.fn(),
      warn: jest.fn(),
    } as any,
  };

  let formatter: WorklogFormatter;
  
  beforeEach(() => {
    jest.clearAllMocks();
    formatter = new WorklogFormatter(mockConfig);
  });

  describe('formatEntry', () => {
    it('should format entries correctly', () => {
      // Test with multiple descriptions
      const testDate = new Date('2025-04-09T12:00:00Z');
      const entry = formatter.formatEntry(
        testDate,
        2.5,
        ['Task 1', 'Task 2', 'Task 3'],
        false
      );
      expect(entry).toContain('2025-4-9 Wed (2.5h): Task 1. Task 2. Task 3.');
      
      // Test with running entry
      const entryWithRunning = formatter.formatEntry(
        testDate,
        3.0,
        ['Task 1'],
        true
      );
      expect(entryWithRunning).toContain('2025-4-9 Wed (3.0h+): Task 1.');
      
      // Test with no descriptions
      const emptyEntry = formatter.formatEntry(
        testDate,
        1.0,
        [],
        false
      );
      expect(emptyEntry).toContain('2025-4-9 Wed (1.0h): ');
    });
  });

  describe('parseEntry', () => {
    it('should parse entries correctly', () => {
      // Test parsing a complete entry
      const entry = '2025-4-9 Wed (2.5h): Task 1. Task 2. Task 3.';
      const parsed = formatter.parseEntry(entry);
      
      expect(parsed).not.toBeNull();
      if (parsed) {
        expect(parsed.hours).toBe(2.5);
        expect(parsed.hasRunningEntry).toBe(false);
        expect(parsed.descriptions).toEqual(['Task 1', 'Task 2', 'Task 3']);
      }
      
      // Test parsing an entry with running marker
      const runningEntry = '2025-4-9 Wed (3.0h+): Task 1.';
      const parsedRunning = formatter.parseEntry(runningEntry);
      
      expect(parsedRunning).not.toBeNull();
      if (parsedRunning) {
        expect(parsedRunning.hours).toBe(3.0);
        expect(parsedRunning.hasRunningEntry).toBe(true);
        expect(parsedRunning.descriptions).toEqual(['Task 1']);
      }
      
      // Test parsing an invalid entry
      const invalidEntry = 'Invalid entry format';
      const parsedInvalid = formatter.parseEntry(invalidEntry);
      
      expect(parsedInvalid).toBeNull();
    });
  });

  describe('mergeEntries', () => {
    it('should merge entries correctly', () => {
      // Test merging entries with different hours
      const existing = '2025-4-9 Wed (2.5h): Task 1. Task 2.';
      const newEntry = '2025-4-9 Wed (3.0h): Task 2. Task 3.';
      const merged = formatter.mergeEntries(existing, newEntry);
      
      // Should use the higher hours value and combine descriptions
      expect(merged).toContain('2025-4-9 Wed (3.0h): Task 1. Task 2. Task 3.');
      
      // Test merging with running entry
      const existingBasic = '2025-4-9 Wed (2.5h): Task 1.';
      const newRunning = '2025-4-9 Wed (2.0h+): Task 2.';
      const mergedRunning = formatter.mergeEntries(existingBasic, newRunning);
      
      // Should keep the running marker
      expect(mergedRunning).toContain('2025-4-9 Wed (2.5h+): Task 1. Task 2.');
      
      // Test merging with invalid entry
      const invalidEntry = 'Invalid entry';
      const validEntry = '2025-4-9 Wed (2.0h): Task 1.';
      const mergedInvalid = formatter.mergeEntries(invalidEntry, validEntry);
      
      // Should use the valid entry
      expect(mergedInvalid).toBe(validEntry);
    });
  });
});
