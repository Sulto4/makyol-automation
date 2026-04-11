import { config } from 'dotenv';
import { PoolConfig } from 'pg';

// Load environment variables from .env file
config();

export interface DatabaseConfig extends PoolConfig {
  host: string;
  port: number;
  user: string;
  password: string;
  database: string;
  min: number;
  max: number;
  idleTimeoutMillis: number;
  connectionTimeoutMillis: number;
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

export const databaseConfig: DatabaseConfig = {
  host: getEnvVar('DB_HOST', 'localhost'),
  port: getEnvVarAsNumber('DB_PORT', 5432),
  user: getEnvVar('DB_USER', 'postgres'),
  password: getEnvVar('DB_PASSWORD', 'postgres'),
  database: getEnvVar('DB_NAME', 'pdfextractor'),
  min: getEnvVarAsNumber('DB_POOL_MIN', 2),
  max: getEnvVarAsNumber('DB_POOL_MAX', 10),
  idleTimeoutMillis: 30000, // 30 seconds
  connectionTimeoutMillis: 2000, // 2 seconds
};

export default databaseConfig;
