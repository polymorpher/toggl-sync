import { format } from 'date-fns';
import { utcToZonedTime } from 'date-fns-tz';
import { Config } from '../config';
import { TogglApiClient, TogglTimeEntry } from '../api/toggl';

export class TimeEntryAggregator {
  private readonly config: Config;
  private readonly togglClient: TogglApiClient;
  
  constructor(config: Config, togglClient?: TogglApiClient) {
    this.config = config;
    this.togglClient = togglClient || new TogglApiClient(config);
  }
  
  /**
   * Aggregate time entries for a specific day
   * @param date Date to aggregate entries for (default: today in configured timezone)
   * @returns Tuple of [formatted_entry, total_hours, has_running_entry]
   */
  async aggregateDailyEntries(date?: Date): Promise<[string, number, boolean]> {
    const { timezone, logger } = this.config;
    
    // If date not provided, use current day in configured timezone
    if (!date) {
      date = new Date();
    }
    
    // Get time entries for the day
    const entries = await this.togglClient.getEntriesByDate(date);
    
    // Calculate total hours
    const totalHours = this.togglClient.calculateDailyHours(entries);
    
    // Check if there's a running entry
    const currentEntry = await this.togglClient.getCurrentTimeEntry();
    const hasRunningEntry = currentEntry !== null;
    
    // Get descriptions from entries
    const descriptions = this.togglClient.getEntriesDescriptions(entries);
    
    // Format the entry
    const formattedEntry = this.formatWorklogEntry(date, totalHours, descriptions, hasRunningEntry);
    
    logger.info(`Aggregated ${entries.length} time entries for ${date.toISOString().split('T')[0]}`);
    logger.info(`Total hours: ${totalHours}${hasRunningEntry ? '+' : ''}`);
    
    return [formattedEntry, totalHours, hasRunningEntry];
  }
  
  /**
   * Format a worklog entry
   * @param date Date of the entry
   * @param hours Total hours worked
   * @param descriptions List of task descriptions
   * @param hasRunningEntry Whether there's a running entry
   * @returns Formatted worklog entry
   */
  formatWorklogEntry(
    date: Date,
    hours: number,
    descriptions: string[],
    hasRunningEntry: boolean
  ): string {
    const { timezone } = this.config;
    
    // Convert to timezone
    const zonedDate = utcToZonedTime(date, timezone);
    
    // Format date as YYYY-M-D
    const dateStr = `${zonedDate.getFullYear()}-${zonedDate.getMonth() + 1}-${zonedDate.getDate()}`;
    
    // Get day name (Mon, Tue, etc.)
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dayName = dayNames[zonedDate.getDay()];
    
    // Format hours as X.Yh or X.Yh+ if there's a running entry
    const hoursStr = `${hours}h${hasRunningEntry ? '+' : ''}`;
    
    // Join descriptions with periods
    let descriptionText = descriptions.join('. ');
    if (descriptionText && !descriptionText.endsWith('.')) {
      descriptionText += '.';
    }
    
    // Format the entry
    return `${dateStr} ${dayName} (${hoursStr}): ${descriptionText}`;
  }
}
