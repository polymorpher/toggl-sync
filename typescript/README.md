# TypeScript Implementation Documentation

This document provides detailed information about the TypeScript implementation of the Toggl to GitHub Worklog Sync application.

## Project Structure

```
typescript/
├── package.json         # Project metadata and dependencies
├── tsconfig.json        # TypeScript configuration
├── README.md            # TypeScript-specific documentation
├── .env.example         # Example environment variables
├── src/                 # Source code
│   ├── index.ts         # Entry point
│   ├── config.ts        # Configuration management
│   ├── sync.ts          # Main sync logic
│   ├── scheduler.ts     # Scheduler for periodic sync
│   ├── formatter.ts     # Worklog entry formatting
│   ├── aggregator.ts    # Time entry aggregation
│   ├── api/             # API clients
│   │   ├── toggl.ts     # Toggl API client
│   │   └── github.ts    # GitHub API client
│   ├── utils/           # Utility modules
│   │   └── error-handler.ts # Error handling and logging
│   └── tests/           # Unit tests
│       ├── toggl.test.ts
│       ├── github.test.ts
│       ├── formatter.test.ts
│       ├── aggregator.test.ts
│       ├── config.test.ts
│       ├── error-handler.test.ts
│       └── scheduler.test.ts
```

## Dependencies

The TypeScript implementation uses the following main dependencies:

- `axios`: For making HTTP requests to the Toggl API
- `@octokit/rest`: For interacting with the GitHub API
- `dotenv`: For loading environment variables from .env files
- `node-cron`: For scheduling periodic sync tasks
- `date-fns` and `date-fns-tz`: For date and timezone handling
- `winston`: For logging
- `@sendgrid/mail`: For sending error notification emails

## Modules

### `config.ts`

Handles loading and validating configuration from environment variables. Uses an interface to define the application configuration structure.

### `api/toggl.ts`

Client for interacting with the Toggl API. Provides methods for retrieving time entries, calculating daily hours, and extracting descriptions.

### `api/github.ts`

Client for interacting with the GitHub API. Provides methods for getting worklog content, updating the worklog, and finding/updating entries for specific dates.

### `formatter.ts`

Handles formatting worklog entries according to the required format. Provides methods for formatting entries, parsing existing entries, and merging entries.

### `aggregator.ts`

Aggregates time entries by day. Calculates total hours, checks for running entries, and formats the worklog entry.

### `sync.ts`

Main sync logic that ties everything together. Retrieves time entries from Toggl, formats them, and updates the GitHub worklog.

### `scheduler.ts`

Handles scheduling periodic sync tasks using node-cron. Runs the sync at specified intervals.

### `utils/error-handler.ts`

Provides error handling and logging functionality. Includes SendGrid integration for email notifications.

### `index.ts`

Entry point for the application. Sets up logging, loads configuration, and starts the scheduler.

## Error Handling

The application includes comprehensive error handling:

1. **Validation**: Validates required configuration before starting
2. **Exception Handling**: Catches and logs exceptions during execution
3. **Email Notifications**: Sends error notifications via SendGrid (if configured)
4. **Logging**: Logs errors to console and/or file using Winston

## Testing

The application includes Jest unit tests for all major components. Tests can be run using:

```bash
npm test
```

## Building

The TypeScript code needs to be compiled to JavaScript before running. This can be done using:

```bash
npm run build
```

This will create a `dist/` directory with the compiled JavaScript files.

## Extending the Application

### Adding New Features

To add new features to the application:

1. Identify the appropriate module for your feature
2. Implement the feature with proper error handling and TypeScript typing
3. Add unit tests for the new functionality
4. Update documentation as needed

### Customizing Worklog Format

To customize the worklog entry format:

1. Modify the `formatEntry` method in `formatter.ts`
2. Update the regex pattern in `findEntryForDate` in `api/github.ts`
3. Update the parsing logic in `parseEntry` in `formatter.ts`

## Performance Considerations

- The application is designed to run once per hour by default
- API requests are minimized to avoid rate limiting
- The application uses minimal resources when idle
- TypeScript provides type safety to prevent runtime errors
