import axios from 'axios';
import { format, parseISO } from 'date-fns';
import { zonedTimeToUtc, utcToZonedTime } from 'date-fns-tz';
import { Config } from '../config';

export interface TogglTimeEntry {
  id: number;
  workspace_id: number;
  description?: string;
  start: string;
  stop?: string;
  duration: number;
  tags?: string[];
  project_id?: number;
  project_name?: string;
  billable?: boolean;
}

export class TogglApiClient {
  private readonly baseUrl = 'https://api.track.toggl.com/api/v9';
  private readonly config: Config;
  
  constructor(config: Config) {
    this.config = config;
  }
  
  /**
   * Get time entries from Toggl API
   * @param startDate Start date for time entries (default: start of current day in configured timezone)
   * @param endDate End date for time entries (default: end of current day in configured timezone)
   * @returns List of time entries
   */
  async getTimeEntries(startDate?: Date, endDate?: Date): Promise<TogglTimeEntry[]> {
    const { togglApiToken, timezone, logger } = this.config;
    
    // If dates not provided, use current day in configured timezone
    const now = new Date();
    const zonedNow = utcToZonedTime(now, timezone);
    
    if (!startDate) {
      // Start of day in configured timezone
      startDate = new Date(
        zonedNow.getFullYear(),
        zonedNow.getMonth(),
        zonedNow.getDate(),
        0, 0, 0
      );
      startDate = zonedTimeToUtc(startDate, timezone);
    }
    
    if (!endDate) {
      // End of day in configured timezone
      endDate = new Date(
        zonedNow.getFullYear(),
        zonedNow.getMonth(),
        zonedNow.getDate(),
        23, 59, 59
      );
      endDate = zonedTimeToUtc(endDate, timezone);
    }
    
    // Format dates for Toggl API
    const startDateStr = format(startDate, "yyyy-MM-dd'T'HH:mm:ss'Z'");
    const endDateStr = format(endDate, "yyyy-MM-dd'T'HH:mm:ss'Z'");
    
    logger.info(`Fetching Toggl time entries from ${startDateStr} to ${endDateStr}`);
    
    try {
      const response = await axios.get(`${this.baseUrl}/me/time_entries`, {
        params: {
          start_date: startDateStr,
          end_date: endDateStr,
        },
        auth: {
          username: togglApiToken,
          password: 'api_token',
        },
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      return response.data;
    } catch (error) {
      logger.error('Error fetching time entries from Toggl API:', error);
      throw error;
    }
  }
  
  /**
   * Get the current running time entry, if any
   * @returns Current time entry or null if no time entry is running
   */
  async getCurrentTimeEntry(): Promise<TogglTimeEntry | null> {
    const { togglApiToken, logger } = this.config;
    
    try {
      const response = await axios.get(`${this.baseUrl}/me/time_entries/current`, {
        auth: {
          username: togglApiToken,
          password: 'api_token',
        },
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      return response.data;
    } catch (error) {
      logger.error('Error fetching current time entry from Toggl API:', error);
      throw error;
    }
  }
  
  /**
   * Calculate total hours from time entries
   * @param entries List of time entries
   * @returns Total hours as float with one decimal place
   */
  calculateDailyHours(entries: TogglTimeEntry[]): number {
    let totalSeconds = 0;
    
    for (const entry of entries) {
      // For completed entries
      if (entry.duration && entry.duration > 0) {
        totalSeconds += entry.duration;
      }
      // For running entries
      else if (entry.duration && entry.duration < 0) {
        // Calculate duration from start time to now
        const startTime = parseISO(entry.start);
        const now = new Date();
        const duration = (now.getTime() - startTime.getTime()) / 1000;
        totalSeconds += duration;
      }
    }
    
    // Convert to hours with one decimal place
    const totalHours = Math.round(totalSeconds / 360) / 10;
    
    return totalHours;
  }

  /**
   * Get time entries for a specific date
   * @param date Date to get entries for (default: today in configured timezone)
   * @returns List of time entries for the specified date
   */
  async getEntriesByDate(date?: Date): Promise<TogglTimeEntry[]> {
    const { timezone } = this.config;
    
    if (!date) {
      date = new Date();
    }
    
    const zonedDate = utcToZonedTime(date, timezone);
    
    // Set start and end of day in configured timezone
    const startDate = new Date(
      zonedDate.getFullYear(),
      zonedDate.getMonth(),
      zonedDate.getDate(),
      0, 0, 0
    );
    const endDate = new Date(
      zonedDate.getFullYear(),
      zonedDate.getMonth(),
      zonedDate.getDate(),
      23, 59, 59
    );
    
    return this.getTimeEntries(
      zonedTimeToUtc(startDate, timezone),
      zonedTimeToUtc(endDate, timezone)
    );
  }
  
  /**
   * Extract descriptions from time entries
   * @param entries List of time entries
   * @returns List of descriptions (non-empty)
   */
  getEntriesDescriptions(entries: TogglTimeEntry[]): string[] {
    const descriptions: string[] = [];
    
    for (const entry of entries) {
      if (entry.description && entry.description.trim()) {
        descriptions.push(entry.description.trim());
      }
    }
    
    return descriptions;
  }
}
