import express, { Express } from 'express';
import { Pool } from 'pg';
import { appConfig } from './config/app';
import { databaseConfig } from './config/database';
import { errorHandler, notFoundHandler } from './middleware/errorHandler';
import { logger } from './utils/logger';
import { createDocumentRoutes } from './routes/documents';
import { createAuditLogRoutes } from './routes/auditLogs';
import { createSettingsRoutes } from './routes/settings';

/**
 * Create and configure Express application
 *
 * @param pool - PostgreSQL connection pool for dependency injection
 */
function createApp(pool: Pool): Express {
  const app = express();

  // Body parsing middleware
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Request logging middleware
  app.use((req, res, next) => {
    const start = Date.now();

    res.on('finish', () => {
      const duration = Date.now() - start;
      logger.info(`${req.method} ${req.path}`, {
        statusCode: res.statusCode,
        duration: `${duration}ms`,
      });
    });

    next();
  });

  // Health check endpoint
  app.get('/health', (_req, res) => {
    res.json({
      status: 'ok',
      timestamp: new Date().toISOString(),
      environment: appConfig.nodeEnv,
    });
  });

  // API routes
  app.use(`${appConfig.api.prefix}/documents`, createDocumentRoutes(pool));
  app.use(`${appConfig.api.prefix}/audit-logs`, createAuditLogRoutes(pool));
  app.use(`${appConfig.api.prefix}/settings`, createSettingsRoutes(pool));

  // 404 handler (must be after all routes)
  app.use(notFoundHandler);

  // Error handler (must be last)
  app.use(errorHandler);

  return app;
}

/**
 * Initialize database connection pool
 */
function createDatabasePool(): Pool {
  const pool = new Pool(databaseConfig);

  pool.on('error', (err) => {
    logger.error('Unexpected database pool error', err);
  });

  pool.on('connect', () => {
    logger.debug('New database connection established');
  });

  return pool;
}

/**
 * Start the Express server
 */
async function startServer(): Promise<void> {
  try {
    // Initialize database connection
    const pool = createDatabasePool();

    // Create Express app with database pool
    const app = createApp(pool);

    // Test database connection
    try {
      const client = await pool.connect();
      logger.info('Database connection successful');
      client.release();
    } catch (error) {
      logger.error('Database connection failed', error as Error);
      throw error;
    }

    // Start listening
    const port = appConfig.port;
    app.listen(port, () => {
      logger.info(`Server started on port ${port}`, {
        environment: appConfig.nodeEnv,
        apiPrefix: appConfig.api.prefix,
      });
    });

    // Graceful shutdown
    const shutdown = async (signal: string) => {
      logger.info(`${signal} received, shutting down gracefully...`);

      try {
        await pool.end();
        logger.info('Database pool closed');
        process.exit(0);
      } catch (error) {
        logger.error('Error during shutdown', error as Error);
        process.exit(1);
      }
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));

  } catch (error) {
    logger.error('Failed to start server', error as Error);
    process.exit(1);
  }
}

// Start server if this file is run directly
if (require.main === module) {
  startServer();
}

export { createApp, createDatabasePool, startServer };
