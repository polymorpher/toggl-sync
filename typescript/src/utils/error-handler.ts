import * as winston from 'winston';
import * as sgMail from '@sendgrid/mail';
import { Config } from '../config';

/**
 * Set up logging configuration
 * @param config Application configuration
 * @returns Configured logger
 */
export function setupLogger(config?: Partial<Config>): winston.Logger {
  // Create logger with default configuration
  const logger = winston.createLogger({
    level: config?.logLevel || process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.printf(({ timestamp, level, message, ...rest }) => {
        return `${timestamp} [${level.toUpperCase()}]: ${message} ${
          Object.keys(rest).length ? JSON.stringify(rest) : ''
        }`;
      })
    ),
    transports: [
      new winston.transports.Console(),
    ],
  });
  
  // Add file transport if log file is specified
  const logFile = config?.logFile || process.env.LOG_FILE;
  if (logFile) {
    logger.add(new winston.transports.File({ 
      filename: logFile,
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
      )
    }));
  }
  
  return logger;
}

/**
 * Send error notification email using SendGrid
 * @param config Application configuration
 * @param subject Email subject
 * @param errorMessage Error message to send
 * @param logger Logger to use (optional)
 * @returns True if email was sent successfully, False otherwise
 */
export async function sendErrorNotification(
  config: Config,
  subject: string,
  errorMessage: string,
  logger?: winston.Logger
): Promise<boolean> {
  const { sendgridApiKey, notificationEmail } = config;
  
  if (!sendgridApiKey || !notificationEmail) {
    if (logger) {
      logger.warn('SendGrid API key or notification email not configured, skipping error notification');
    }
    return false;
  }
  
  try {
    sgMail.setApiKey(sendgridApiKey);
    
    const message = {
      to: notificationEmail,
      from: notificationEmail,
      subject: `Toggl GitHub Sync Error: ${subject}`,
      html: `
        <h2>Toggl GitHub Sync Error</h2>
        <p>An error occurred while syncing Toggl time entries to GitHub:</p>
        <pre>${errorMessage}</pre>
        <p>Please check the logs for more details.</p>
        <hr>
        <p><small>This is an automated message from the Toggl GitHub Sync application.</small></p>
      `,
    };
    
    const response = await sgMail.send(message);
    
    if (logger) {
      if (response[0].statusCode >= 200 && response[0].statusCode < 300) {
        logger.info(`Error notification sent to ${notificationEmail}`);
        return true;
      } else {
        logger.error(`Failed to send error notification: ${response[0].statusCode}`);
        return false;
      }
    }
    
    return response[0].statusCode >= 200 && response[0].statusCode < 300;
  } catch (error) {
    if (logger) {
      logger.error('Error sending notification email:', error);
    }
    return false;
  }
}

/**
 * Error handler for toggl-github-sync
 */
export class ErrorHandler {
  private readonly config: Config;
  private readonly logger: winston.Logger;
  
  constructor(config: Config, logger?: winston.Logger) {
    this.config = config;
    this.logger = logger || config.logger || setupLogger();
  }
  
  /**
   * Handle an error
   * @param error Exception to handle
   * @param context Context where the error occurred
   */
  async handleError(error: Error, context: string = 'Unknown'): Promise<void> {
    const errorMessage = `${error.name}: ${error.message}`;
    this.logger.error(`Error in ${context}: ${errorMessage}`);
    
    // Send email notification if configured
    if (this.config.sendgridApiKey && this.config.notificationEmail) {
      await sendErrorNotification(
        this.config,
        `Error in ${context}`,
        errorMessage,
        this.logger
      );
    }
  }
}
