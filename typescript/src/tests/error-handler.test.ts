import { ErrorHandler, sendErrorNotification, setupLogger } from '../utils/error-handler';
import { Config } from '../config';

/**
 * Jest tests for the error handler
 */
describe('ErrorHandler', () => {
  // Mock config
  const mockConfig: Config = {
    togglApiToken: 'test_token',
    githubToken: 'test_token',
    githubRepo: 'test/repo',
    githubWorklogPath: 'test/path',
    timezone: 'America/Los_Angeles',
    syncIntervalMinutes: 60,
    sendgridApiKey: 'test_api_key',
    notificationEmail: 'test@example.com',
    logger: {
      info: jest.fn(),
      error: jest.fn(),
      warn: jest.fn(),
      debug: jest.fn(),
    } as any,
  };

  // Mock SendGrid
  jest.mock('@sendgrid/mail', () => ({
    setApiKey: jest.fn(),
    send: jest.fn().mockResolvedValue([{ statusCode: 202 }]),
  }));

  const sgMail = require('@sendgrid/mail');
  
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('setupLogger', () => {
    it('should create a logger with default configuration', () => {
      const logger = setupLogger();
      expect(logger).toBeDefined();
      expect(logger.level).toBe('info');
    });

    it('should use config log level if provided', () => {
      const logger = setupLogger({ logLevel: 'debug' });
      expect(logger.level).toBe('debug');
    });
  });

  describe('sendErrorNotification', () => {
    it('should send error notification email', async () => {
      const mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
      } as any;

      const result = await sendErrorNotification(
        mockConfig,
        'Test Error',
        'This is a test error message',
        mockLogger
      );

      expect(result).toBe(true);
      expect(sgMail.setApiKey).toHaveBeenCalledWith('test_api_key');
      expect(sgMail.send).toHaveBeenCalledWith(expect.objectContaining({
        to: 'test@example.com',
        from: 'test@example.com',
        subject: 'Toggl GitHub Sync Error: Test Error',
      }));
      expect(mockLogger.info).toHaveBeenCalled();
    });

    it('should handle failed email sending', async () => {
      const mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
      } as any;

      // Mock failed response
      sgMail.send.mockResolvedValueOnce([{ statusCode: 400 }]);

      const result = await sendErrorNotification(
        mockConfig,
        'Test Error',
        'This is a test error message',
        mockLogger
      );

      expect(result).toBe(false);
      expect(mockLogger.error).toHaveBeenCalled();
    });

    it('should skip sending if configuration is missing', async () => {
      const mockLogger = {
        info: jest.fn(),
        error: jest.fn(),
        warn: jest.fn(),
      } as any;

      const configWithoutSendGrid = { ...mockConfig, sendgridApiKey: undefined };

      const result = await sendErrorNotification(
        configWithoutSendGrid,
        'Test Error',
        'This is a test error message',
        mockLogger
      );

      expect(result).toBe(false);
      expect(mockLogger.warn).toHaveBeenCalled();
      expect(sgMail.send).not.toHaveBeenCalled();
    });
  });

  describe('ErrorHandler', () => {
    it('should handle errors and send notifications', async () => {
      // Mock sendErrorNotification
      const mockSendErrorNotification = jest.fn().mockResolvedValue(true);
      jest.spyOn(require('../utils/error-handler'), 'sendErrorNotification').mockImplementation(mockSendErrorNotification);

      const handler = new ErrorHandler(mockConfig);
      const testError = new Error('Test error');

      await handler.handleError(testError, 'test_context');

      expect(mockConfig.logger.error).toHaveBeenCalled();
      expect(mockSendErrorNotification).toHaveBeenCalledWith(
        mockConfig,
        'Error in test_context',
        'Error: Test error',
        expect.anything()
      );
    });
  });
});
