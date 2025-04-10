import cron from 'node-cron';
import { Config } from '../config';
import { syncTogglToGithub } from '../sync';

export function startScheduler(config: Config): void {
  const { syncIntervalMinutes, logger } = config;
  
  // Create cron expression for the specified interval
  // Format: second minute hour day month day-of-week
  const cronExpression = `0 */${syncIntervalMinutes} * * * *`;
  
  // Validate cron expression
  if (!cron.validate(cronExpression)) {
    throw new Error(`Invalid cron expression: ${cronExpression}`);
  }
  
  // Schedule the sync task
  const task = cron.schedule(cronExpression, async () => {
    logger.info(`Running scheduled sync (every ${syncIntervalMinutes} minutes)`);
    try {
      await syncTogglToGithub(config);
      logger.info('Scheduled sync completed successfully');
    } catch (error) {
      logger.error('Error in scheduled sync:', error);
    }
  });
  
  // Start the scheduler
  task.start();
  logger.info(`Scheduler started. Will sync every ${syncIntervalMinutes} minutes.`);
  
  // Run once immediately
  syncTogglToGithub(config)
    .then(() => logger.info('Initial sync completed successfully'))
    .catch((error) => logger.error('Error in initial sync:', error));
  
  // Handle process termination
  process.on('SIGINT', () => {
    logger.info('Stopping scheduler...');
    task.stop();
    process.exit(0);
  });
  
  process.on('SIGTERM', () => {
    logger.info('Stopping scheduler...');
    task.stop();
    process.exit(0);
  });
}
