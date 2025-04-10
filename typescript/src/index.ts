import dotenv from 'dotenv';
import yargs from 'yargs';
import { hideBin } from 'yargs/helpers';

import { loadConfig } from './config';
import { startScheduler } from './scheduler';
import { syncTogglToGithub } from './sync';
import { setupLogger } from './utils/logger';

// Load environment variables
dotenv.config();

// Setup logger
const logger = setupLogger();

async function main() {
  try {
    // Parse command line arguments
    const argv = await yargs(hideBin(process.argv))
      .option('schedule', {
        alias: 's',
        type: 'boolean',
        description: 'Run with scheduler (default: run once and exit)',
        default: false,
      })
      .help()
      .alias('help', 'h')
      .parse();

    // Load configuration
    const config = loadConfig();
    
    if (argv.schedule) {
      logger.info('Starting scheduler');
      startScheduler(config);
    } else {
      logger.info('Running sync once');
      await syncTogglToGithub(config);
      logger.info('Sync completed');
    }
  } catch (error) {
    logger.error('Error in main process:', error);
    process.exit(1);
  }
}

// Run the main function
main();
