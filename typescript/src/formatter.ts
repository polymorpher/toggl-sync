import { format } from 'date-fns';
import { utcToZonedTime } from 'date-fns-tz';
import { Config } from './config';

export class WorklogFormatter {
  private readonly config: Config;
  
  constructor(config: Config) {
    this.config = config;
  }
  
  /**
   * Format a worklog entry
   * @param date Date of the entry
   * @param hours Total hours worked
   * @param descriptions List of task descriptions
   * @param hasRunningEntry Whether there's a running entry
   * @returns Formatted worklog entry
   */
  formatEntry(
    date: Date,
    hours: number,
    descriptions: string[],
    hasRunningEntry: boolean
  ): string {
    const { timezone, logger } = this.config;
    
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
  
  /**
   * Parse a worklog entry
   * @param entry Worklog entry string
   * @returns Object with parsed components or null if parsing failed
   */
  parseEntry(entry: string): {
    date: Date;
    dayName: string;
    hours: number;
    hasRunningEntry: boolean;
    descriptions: string[];
    descriptionText: string;
  } | null {
    const { timezone, logger } = this.config;
    
    // Pattern to match worklog entries
    const pattern = /(\d{4}-\d{1,2}-\d{1,2}) ([A-Za-z]{3}) \((\d+\.?\d*)h(\+?)\): (.*)/;
    const match = entry.match(pattern);
    
    if (!match) {
      logger.warning(`Failed to parse worklog entry: ${entry}`);
      return null;
    }
    
    const [, dateStr, dayName, hoursStr, runningMarker, description] = match;
    
    try {
      // Parse date
      const [year, month, day] = dateStr.split('-').map(Number);
      const date = new Date(year, month - 1, day);
      
      // Parse hours
      const hours = parseFloat(hoursStr);
      
      // Parse running status
      const hasRunningEntry = runningMarker === '+';
      
      // Parse descriptions
      const descriptions = description
        .split('.')
        .map(d => d.trim())
        .filter(d => d.length > 0);
      
      return {
        date,
        dayName,
        hours,
        hasRunningEntry,
        descriptions,
        descriptionText: description,
      };
    } catch (error) {
      logger.warning(`Error parsing worklog entry: ${error}`);
      return null;
    }
  }
  
  /**
   * Merge an existing entry with a new entry
   * @param existingEntry Existing worklog entry
   * @param newEntry New worklog entry
   * @returns Merged worklog entry
   */
  mergeEntries(existingEntry: string, newEntry: string): string {
    const { logger } = this.config;
    
    const existingParsed = this.parseEntry(existingEntry);
    const newParsed = this.parseEntry(newEntry);
    
    if (!existingParsed || !newParsed) {
      logger.warning('Failed to parse entries for merging, using new entry');
      return newEntry;
    }
    
    // Use the higher hours value
    const hours = Math.max(existingParsed.hours, newParsed.hours);
    
    // Combine running status (if either is running, result is running)
    const hasRunningEntry = existingParsed.hasRunningEntry || newParsed.hasRunningEntry;
    
    // Combine descriptions (unique only)
    const allDescriptions = [...existingParsed.descriptions, ...newParsed.descriptions];
    const uniqueDescriptions = Array.from(new Set(allDescriptions));
    
    // Format the merged entry
    return this.formatEntry(
      existingParsed.date,
      hours,
      uniqueDescriptions,
      hasRunningEntry
    );
  }
}
