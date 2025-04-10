import { Octokit } from '@octokit/rest';
import { format } from 'date-fns';
import { utcToZonedTime } from 'date-fns-tz';
import { Config } from '../config';

export interface WorklogEntry {
  content: string;
  startIndex: number;
  endIndex: number;
}

export class GitHubApiClient {
  private readonly octokit: Octokit;
  private readonly config: Config;
  
  constructor(config: Config) {
    this.config = config;
    this.octokit = new Octokit({
      auth: config.githubToken,
    });
  }
  
  /**
   * Get the current content of the worklog file
   * @returns Tuple of [content, sha]
   */
  async getWorklogContent(): Promise<[string, string]> {
    const { githubRepo, githubWorklogPath, logger } = this.config;
    
    // Split repo into owner and repo
    const [owner, repo] = githubRepo.split('/');
    
    if (!owner || !repo) {
      throw new Error(`Invalid GitHub repository format: ${githubRepo}. Expected format: owner/repo`);
    }
    
    logger.info(`Fetching worklog content from ${githubRepo}/${githubWorklogPath}`);
    
    try {
      const response = await this.octokit.repos.getContent({
        owner,
        repo,
        path: githubWorklogPath,
      });
      
      // Check if response is a file (not a directory)
      if (Array.isArray(response.data)) {
        throw new Error(`Expected a file, but ${githubWorklogPath} is a directory`);
      }
      
      if (!('content' in response.data) || !('sha' in response.data)) {
        throw new Error('GitHub API response does not contain content or sha');
      }
      
      // Decode base64 content
      const content = Buffer.from(response.data.content, 'base64').toString('utf-8');
      const sha = response.data.sha;
      
      return [content, sha];
    } catch (error) {
      logger.error('Error fetching worklog content from GitHub:', error);
      throw error;
    }
  }
  
  /**
   * Update the worklog file with new content
   * @param newContent New content for the worklog file
   * @param sha SHA of the current file content
   * @returns True if update was successful
   */
  async updateWorklog(newContent: string, sha: string): Promise<boolean> {
    const { githubRepo, githubWorklogPath, logger } = this.config;
    
    // Split repo into owner and repo
    const [owner, repo] = githubRepo.split('/');
    
    if (!owner || !repo) {
      throw new Error(`Invalid GitHub repository format: ${githubRepo}. Expected format: owner/repo`);
    }
    
    logger.info(`Updating worklog content in ${githubRepo}/${githubWorklogPath}`);
    
    try {
      await this.octokit.repos.createOrUpdateFileContents({
        owner,
        repo,
        path: githubWorklogPath,
        message: 'Update worklog with Toggl time entries',
        content: Buffer.from(newContent).toString('base64'),
        sha,
      });
      
      logger.info('Worklog updated successfully');
      return true;
    } catch (error) {
      logger.error('Error updating worklog content on GitHub:', error);
      throw error;
    }
  }
  
  /**
   * Find an existing entry for the given date in the worklog content
   * @param content Worklog content
   * @param date Date to find
   * @returns Entry details if found, null otherwise
   */
  findEntryForDate(content: string, date: Date): WorklogEntry | null {
    const { timezone, logger } = this.config;
    
    // Convert to timezone
    const zonedDate = utcToZonedTime(date, timezone);
    
    // Format date as YYYY-M-D
    const dateStr = `${zonedDate.getFullYear()}-${zonedDate.getMonth() + 1}-${zonedDate.getDate()}`;
    
    // Look for an entry starting with the date
    const pattern = new RegExp(`(${dateStr} [A-Za-z]+ \\(\\d+\\.?\\d*h\\+?\\): .+?)(\\n\\n|\\n\\*|\\Z)`, 's');
    const match = content.match(pattern);
    
    if (match && match.index !== undefined) {
      const entry = {
        content: match[1],
        startIndex: match.index,
        endIndex: match.index + match[1].length,
      };
      
      logger.info(`Found existing entry for ${dateStr}: ${entry.content.substring(0, 50)}...`);
      return entry;
    }
    
    logger.info(`No existing entry found for ${dateStr}`);
    return null;
  }
  
  /**
   * Update an existing entry or create a new one
   * @param content Current worklog content
   * @param newEntry New entry to add or update
   * @param date Date of the entry
   * @returns Updated worklog content
   */
  updateOrCreateEntry(content: string, newEntry: string, date: Date): string {
    const { timezone, logger } = this.config;
    const zonedDate = utcToZonedTime(date, timezone);
    const dateStr = format(zonedDate, 'yyyy-M-d');
    
    // Check if there's already an entry for the date
    const existingEntry = this.findEntryForDate(content, date);
    
    let updatedContent: string;
    
    if (existingEntry) {
      // Update existing entry
      updatedContent = (
        content.substring(0, existingEntry.startIndex) + 
        newEntry + 
        content.substring(existingEntry.endIndex)
      );
      logger.info(`Updated existing entry for ${dateStr}`);
    } else {
      // Add new entry at the top
      if (content.startsWith('# ')) {
        // If the file starts with a title, add after the title
        const titleEnd = content.indexOf('\n') + 1;
        updatedContent = (
          content.substring(0, titleEnd) + 
          '\n' + newEntry + '\n\n' + 
          content.substring(titleEnd)
        );
      } else {
        // Otherwise, add at the very top
        updatedContent = newEntry + '\n\n' + content;
      }
      logger.info(`Added new entry for ${dateStr}`);
    }
    
    return updatedContent;
  }
}
