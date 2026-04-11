import { appConfig } from '../config/app';

/**
 * Log levels in order of severity
 */
export enum LogLevel {
  ERROR = 'error',
  WARN = 'warn',
  INFO = 'info',
  DEBUG = 'debug',
}

/**
 * Log level priority mapping
 */
const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  [LogLevel.ERROR]: 0,
  [LogLevel.WARN]: 1,
  [LogLevel.INFO]: 2,
  [LogLevel.DEBUG]: 3,
};

/**
 * Logger service for structured application logging
 */
class Logger {
  private logLevel: LogLevel;
  private isDevelopment: boolean;

  constructor() {
    this.logLevel = this.parseLogLevel(appConfig.logLevel);
    this.isDevelopment = appConfig.nodeEnv === 'development';
  }

  /**
   * Parse log level from string configuration
   */
  private parseLogLevel(level: string): LogLevel {
    const normalized = level.toLowerCase();
    if (Object.values(LogLevel).includes(normalized as LogLevel)) {
      return normalized as LogLevel;
    }
    return LogLevel.INFO;
  }

  /**
   * Check if a log level should be emitted based on configured log level
   */
  private shouldLog(level: LogLevel): boolean {
    return LOG_LEVEL_PRIORITY[level] <= LOG_LEVEL_PRIORITY[this.logLevel];
  }

  /**
   * Format log message with timestamp and level
   */
  private formatMessage(level: LogLevel, message: string, meta?: any): string {
    const timestamp = new Date().toISOString();
    const baseMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;

    if (meta) {
      if (this.isDevelopment) {
        // Pretty print in development
        return `${baseMessage}\n${JSON.stringify(meta, null, 2)}`;
      } else {
        // Single line JSON in production
        return JSON.stringify({
          timestamp,
          level,
          message,
          ...meta,
        });
      }
    }

    return this.isDevelopment ? baseMessage : JSON.stringify({
      timestamp,
      level,
      message,
    });
  }

  /**
   * Log error message
   */
  error(message: string, error?: Error | any): void {
    if (!this.shouldLog(LogLevel.ERROR)) return;

    const meta = error ? {
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
        ...(error as any).details,
      } : error,
    } : undefined;

    // eslint-disable-next-line no-console
    console.error(this.formatMessage(LogLevel.ERROR, message, meta));
  }

  /**
   * Log warning message
   */
  warn(message: string, meta?: any): void {
    if (!this.shouldLog(LogLevel.WARN)) return;
    // eslint-disable-next-line no-console
    console.warn(this.formatMessage(LogLevel.WARN, message, meta));
  }

  /**
   * Log info message
   */
  info(message: string, meta?: any): void {
    if (!this.shouldLog(LogLevel.INFO)) return;
    // eslint-disable-next-line no-console
    console.log(this.formatMessage(LogLevel.INFO, message, meta));
  }

  /**
   * Log debug message
   */
  debug(message: string, meta?: any): void {
    if (!this.shouldLog(LogLevel.DEBUG)) return;
    // eslint-disable-next-line no-console
    console.debug(this.formatMessage(LogLevel.DEBUG, message, meta));
  }
}

// Export singleton instance
export const logger = new Logger();
export default logger;
