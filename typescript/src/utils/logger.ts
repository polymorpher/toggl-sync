import * as winston from 'winston';

export function setupLogger(): winston.Logger {
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
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
}
