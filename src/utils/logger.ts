import fs from 'fs';
import path from 'path';
import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
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

const LOG_LEVEL_PRIORITY: Record<LogLevel, number> = {
  [LogLevel.ERROR]: 0,
  [LogLevel.WARN]: 1,
  [LogLevel.INFO]: 2,
  [LogLevel.DEBUG]: 3,
};

function parseLogLevel(level: string): LogLevel {
  const normalized = (level ?? '').toLowerCase();
  if (Object.values(LogLevel).includes(normalized as LogLevel)) {
    return normalized as LogLevel;
  }
  return LogLevel.INFO;
}

function resolveLogDir(): string {
  const candidate = process.env.LOG_DIR || '/app/logs';
  try {
    fs.mkdirSync(candidate, { recursive: true });
    return candidate;
  } catch {
    const fallback = path.join(process.cwd(), 'logs', 'backend');
    fs.mkdirSync(fallback, { recursive: true });
    return fallback;
  }
}

const consoleFormatter = winston.format.printf((info) => {
  const { timestamp, level, message, stack, ...rest } = info;
  const levelUpper = String(level).toUpperCase();
  const base = `[${timestamp}] [${levelUpper}] ${stack ?? message}`;
  const meta = Object.keys(rest).length ? rest : undefined;
  if (!meta) return base;
  if (appConfig.nodeEnv === 'development') {
    return `${base}\n${JSON.stringify(meta, null, 2)}`;
  }
  return JSON.stringify({ timestamp, level, message: stack ?? message, ...rest });
});

const fileFormatter = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json(),
);

const logLevel = parseLogLevel(appConfig.logLevel);
const logDir = resolveLogDir();

const winstonLogger = winston.createLogger({
  level: logLevel,
  levels: LOG_LEVEL_PRIORITY,
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        consoleFormatter,
      ),
    }),
    new DailyRotateFile({
      dirname: logDir,
      filename: 'backend-%DATE%.log',
      datePattern: 'YYYY-MM-DD',
      maxSize: '20m',
      maxFiles: '7d',
      utc: true,
      format: fileFormatter,
    }),
  ],
});

/**
 * Public logger API — preserved from the previous custom implementation so
 * that the ~90 existing call sites (logger.info / .warn / .error / .debug)
 * keep working without changes. Internals now fan out to both the console
 * and a daily-rotated file under /app/logs (bind-mounted to host ./logs/backend
 * so entries survive container rebuilds).
 */
class Logger {
  error(message: string, error?: Error | unknown): void {
    if (error instanceof Error) {
      winstonLogger.error(message, { error: { name: error.name, message: error.message, stack: error.stack, ...(error as any).details } });
    } else if (error !== undefined) {
      winstonLogger.error(message, { error });
    } else {
      winstonLogger.error(message);
    }
  }

  warn(message: string, meta?: unknown): void {
    if (meta !== undefined) winstonLogger.warn(message, meta as object);
    else winstonLogger.warn(message);
  }

  info(message: string, meta?: unknown): void {
    if (meta !== undefined) winstonLogger.info(message, meta as object);
    else winstonLogger.info(message);
  }

  debug(message: string, meta?: unknown): void {
    if (meta !== undefined) winstonLogger.debug(message, meta as object);
    else winstonLogger.debug(message);
  }
}

export const logger = new Logger();
export default logger;
