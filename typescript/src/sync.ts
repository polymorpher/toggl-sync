import { format } from 'date-fns';
import { utcToZonedTime } from 'date-fns-tz';
import sgMail from '@sendgrid/mail';
import { Config } from './config';
import { TogglApiClient, TogglTimeEntry } from './api/toggl';
import { GitHubApiClient } from './api/github';

export async function syncTogglToGithub(config: Config): Promise<boolean> {
  const { timezone, sendgridApiKey, notificationEmail, logger } = config;
  
  try {
    // Initialize API clients
    const togglClient = new TogglApiClient(config);
    const githubClient = new GitHubApiClient(config);
    
    // Get today's date in configured timezone
    const now = new Date();
    const zonedNow = utcToZonedTime(now, timezone);
    
    // Get time entries for today
    const entries = await togglClient.getTimeEntries();
    
    // Calculate total hours
    const totalHours = togglClient.calculateDailyHours(entries);
    
    // Format as "X.Yh" or "X.Yh+" if there's a running entry
    const currentEntry = await togglClient.getCurrentTimeEntry();
    let hoursStr = `${totalHours}h`;
    if (currentEntry) {
      hoursStr += '+';
    }
    
    // Get descriptions from entries and join with periods
    const descriptions: string[] = [];
    for (const entry of entries) {
      if (entry.description && entry.description.trim()) {
        descriptions.push(entry.description.trim());
      }
    }
    
    let descriptionText = descriptions.join('. ');
    if (descriptionText && !descriptionText.endsWith('.')) {
      descriptionText += '.';
    }
    
    // Format the worklog entry
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const dayName = dayNames[zonedNow.getDay()];
    const dateStr = `${zonedNow.getFullYear()}-${zonedNow.getMonth() + 1}-${zonedNow.getDate()}`;
    
    const newEntry = `${dateStr} ${dayName} (${hoursStr}): ${descriptionText}`;
    
    // Get current worklog content
    const [worklogContent, sha] = await githubClient.getWorklogContent();
    
    // Check if there's already an entry for today
    const existingEntry = githubClient.findEntryForDate(worklogContent, zonedNow);
    
    let updatedContent: string;
    
    if (existingEntry) {
      // Update existing entry
      updatedContent = (
        worklogContent.substring(0, existingEntry.startIndex) + 
        newEntry + 
        worklogContent.substring(existingEntry.endIndex)
      );
    } else {
      // Add new entry at the top
      if (worklogContent.startsWith('# ')) {
        // If the file starts with a title, add after the title
        const titleEnd = worklogContent.indexOf('\n') + 1;
        updatedContent = (
          worklogContent.substring(0, titleEnd) + 
          '\n' + newEntry + '\n\n' + 
          worklogContent.substring(titleEnd)
        );
      } else {
        // Otherwise, add at the very top
        updatedContent = newEntry + '\n\n' + worklogContent;
      }
    }
    
    // Update the worklog file
    const success = await githubClient.updateWorklog(updatedContent, sha);
    
    logger.info(`Sync completed successfully: ${newEntry}`);
    return success;
  } catch (error) {
    logger.error('Error syncing Toggl to GitHub:', error);
    
    // Send email notification if configured
    if (sendgridApiKey && notificationEmail) {
      await sendErrorNotification(config, error instanceof Error ? error.message : String(error));
    }
    
    return false;
  }
}

async function sendErrorNotification(config: Config, errorMessage: string): Promise<void> {
  const { sendgridApiKey, notificationEmail, logger } = config;
  
  if (!sendgridApiKey || !notificationEmail) {
    return;
  }
  
  try {
    sgMail.setApiKey(sendgridApiKey);
    
    const message = {
      to: notificationEmail,
      from: notificationEmail,
      subject: 'Toggl GitHub Sync Error',
      html: `
        <p>An error occurred while syncing Toggl time entries to GitHub:</p>
        <pre>${errorMessage}</pre>
        <p>Please check the logs for more details.</p>
      `,
    };
    
    await sgMail.send(message);
    
    logger.info(`Error notification sent to ${notificationEmail}`);
  } catch (error) {
    logger.error('Error sending notification email:', error);
  }
}
