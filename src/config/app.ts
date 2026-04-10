import { config } from 'dotenv';
import path from 'path';

// Load environment variables from .env file
config();

export interface AppConfig {
  nodeEnv: string;
  port: number;
  logLevel: string;
  upload: {
    maxFileSize: number;
    uploadDir: string;
  };
  api: {
    prefix: string;
    corsOrigin: string;
  };
}

const getEnvVar = (key: string, defaultValue?: string): string => {
  const value = process.env[key];
  if (value === undefined) {
    if (defaultValue !== undefined) {
      return defaultValue;
    }
    throw new Error(`Environment variable ${key} is not defined`);
  }
  return value;
};

const getEnvVarAsNumber = (key: string, defaultValue?: number): number => {
  const value = process.env[key];
  if (value === undefined) {
    if (defaultValue !== undefined) {
      return defaultValue;
    }
    throw new Error(`Environment variable ${key} is not defined`);
  }
  const parsed = parseInt(value, 10);
  if (isNaN(parsed)) {
    throw new Error(`Environment variable ${key} must be a valid number`);
  }
  return parsed;
};

export const appConfig: AppConfig = {
  nodeEnv: getEnvVar('NODE_ENV', 'development'),
  port: getEnvVarAsNumber('PORT', 3000),
  logLevel: getEnvVar('LOG_LEVEL', 'info'),
  upload: {
    maxFileSize: getEnvVarAsNumber('MAX_FILE_SIZE', 10485760), // 10MB default
    uploadDir: getEnvVar('UPLOAD_DIR', path.join(process.cwd(), 'uploads')),
  },
  api: {
    prefix: getEnvVar('API_PREFIX', '/api'),
    corsOrigin: getEnvVar('CORS_ORIGIN', 'http://localhost:3000'),
  },
};

export default appConfig;
