import { GitHubApiClient, WorklogEntry } from '../api/github';
import { Config } from '../config';

/**
 * Jest tests for the GitHub API client
 */
describe('GitHubApiClient', () => {
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

  // Mock Octokit
  jest.mock('@octokit/rest', () => {
    return {
      Octokit: jest.fn().mockImplementation(() => {
        return {
          repos: {
            getContent: jest.fn(),
            createOrUpdateFileContents: jest.fn(),
          },
        };
      }),
    };
  });

  let client: GitHubApiClient;
  
  beforeEach(() => {
    jest.clearAllMocks();
    client = new GitHubApiClient(mockConfig);
  });

  describe('findEntryForDate', () => {
    it('should find an existing entry for a date', () => {
      // Test content
      const content = `# Worklog
      
2025-4-9 Wed (1.5h): Task 1. Task 2.

2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
`;
      
      // Test finding an existing entry
      const date = new Date('2025-04-09T12:00:00Z');
      const result = client.findEntryForDate(content, date);
      
      // Assertions
      expect(result).not.toBeNull();
      if (result) {
        expect(result.content).toBe('2025-4-9 Wed (1.5h): Task 1. Task 2.');
      }
    });

    it('should return null for non-existent entry', () => {
      // Test content
      const content = `# Worklog
      
2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
`;
      
      // Test finding a non-existent entry
      const date = new Date('2025-04-09T12:00:00Z');
      const result = client.findEntryForDate(content, date);
      
      // Assertions
      expect(result).toBeNull();
    });
  });

  describe('updateOrCreateEntry', () => {
    it('should update an existing entry', () => {
      // Test content
      const content = `# Worklog
      
2025-4-9 Wed (1.5h): Task 1. Task 2.

2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
`;
      
      // Mock findEntryForDate
      jest.spyOn(client, 'findEntryForDate').mockReturnValue({
        content: '2025-4-9 Wed (1.5h): Task 1. Task 2.',
        startIndex: content.indexOf('2025-4-9'),
        endIndex: content.indexOf('2025-4-9') + '2025-4-9 Wed (1.5h): Task 1. Task 2.'.length,
      });
      
      // New entry
      const newEntry = '2025-4-9 Wed (2.0h): Task 1. Task 2. Task 5.';
      const date = new Date('2025-04-09T12:00:00Z');
      
      // Call the method
      const updatedContent = client.updateOrCreateEntry(content, newEntry, date);
      
      // Assertions
      expect(updatedContent).toContain(newEntry);
      expect(updatedContent).not.toContain('2025-4-9 Wed (1.5h): Task 1. Task 2.');
    });

    it('should create a new entry', () => {
      // Test content
      const content = `# Worklog
      
2025-4-8 Tue (2.0h+): Task 3.

* * *

2025-4-7 Mon (3.0h): Task 4.
`;
      
      // Mock findEntryForDate
      jest.spyOn(client, 'findEntryForDate').mockReturnValue(null);
      
      // New entry
      const newEntry = '2025-4-9 Wed (1.5h): Task 1. Task 2.';
      const date = new Date('2025-04-09T12:00:00Z');
      
      // Call the method
      const updatedContent = client.updateOrCreateEntry(content, newEntry, date);
      
      // Assertions
      expect(updatedContent).toContain(newEntry);
      expect(updatedContent.indexOf(newEntry)).toBeLessThan(updatedContent.indexOf('2025-4-8'));
    });

    it('should add entry after title if content starts with title', () => {
      // Test content with title
      const content = `# Worklog

2025-4-8 Tue (2.0h+): Task 3.`;
      
      // Mock findEntryForDate
      jest.spyOn(client, 'findEntryForDate').mockReturnValue(null);
      
      // New entry
      const newEntry = '2025-4-9 Wed (1.5h): Task 1. Task 2.';
      const date = new Date('2025-04-09T12:00:00Z');
      
      // Call the method
      const updatedContent = client.updateOrCreateEntry(content, newEntry, date);
      
      // Assertions
      expect(updatedContent).toContain(newEntry);
      expect(updatedContent.indexOf('# Worklog')).toBeLessThan(updatedContent.indexOf(newEntry));
      expect(updatedContent.indexOf(newEntry)).toBeLessThan(updatedContent.indexOf('2025-4-8'));
    });
  });
});
