import { Request, Response, NextFunction } from 'express';
import { PDFExtractionError } from '../utils/errors';
import { logger } from '../utils/logger';

/**
 * Error response structure
 */
interface ErrorResponse {
  error: {
    name: string;
    message: string;
    code?: string;
    details?: any;
    stack?: string;
  };
}

/**
 * Map error codes to HTTP status codes
 */
const ERROR_STATUS_MAP: Record<string, number> = {
  PDF_NOT_FOUND: 404,
  PDF_PERMISSION_DENIED: 403,
  PDF_CORRUPTED: 400,
  PDF_ENCRYPTED: 400,
  PDF_SCANNED: 400,
  PDF_INVALID_FORMAT: 400,
  PDF_INVALID_INPUT: 400,
  PDF_PARSING_FAILED: 422,
  PDF_FILESYSTEM_ERROR: 500,
};

/**
 * Get HTTP status code for error
 */
function getStatusCode(error: any): number {
  // Check if error is a PDFExtractionError with a code
  if (error instanceof PDFExtractionError && error.code) {
    return ERROR_STATUS_MAP[error.code] || 500;
  }

  // Handle common HTTP errors
  if (error.status) {
    return error.status;
  }

  if (error.statusCode) {
    return error.statusCode;
  }

  // Default to 500 for unknown errors
  return 500;
}

/**
 * Build error response object
 */
function buildErrorResponse(error: any, includeStack: boolean): ErrorResponse {
  const response: ErrorResponse = {
    error: {
      name: error.name || 'Error',
      message: error.message || 'An unexpected error occurred',
    },
  };

  // Add error code if available
  if (error.code) {
    response.error.code = error.code;
  }

  // Add error details if available
  if (error.details) {
    response.error.details = error.details;
  }

  // Include stack trace in development
  if (includeStack && error.stack) {
    response.error.stack = error.stack;
  }

  return response;
}

/**
 * Express error handling middleware
 *
 * Catches all errors thrown in request handlers and formats them
 * as JSON responses with appropriate HTTP status codes.
 *
 * @example
 * ```typescript
 * app.use(errorHandler);
 * ```
 */
export function errorHandler(
  error: any,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // If headers already sent, delegate to default Express error handler
  if (res.headersSent) {
    return next(error);
  }

  const statusCode = getStatusCode(error);
  const isDevelopment = process.env.NODE_ENV === 'development';

  // Log the error
  logger.error(
    `${req.method} ${req.path} - ${error.message}`,
    error
  );

  // Build and send error response
  const errorResponse = buildErrorResponse(error, isDevelopment);
  res.status(statusCode).json(errorResponse);
}

/**
 * Catch-all middleware for 404 Not Found errors
 *
 * Should be registered after all routes.
 *
 * @example
 * ```typescript
 * app.use(notFoundHandler);
 * ```
 */
export function notFoundHandler(
  req: Request,
  _res: Response,
  next: NextFunction
): void {
  const error = {
    name: 'NotFoundError',
    message: `Route ${req.method} ${req.path} not found`,
    code: 'ROUTE_NOT_FOUND',
    status: 404,
  };

  next(error);
}
