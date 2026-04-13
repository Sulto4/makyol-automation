import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';
import { AuditService } from '../services/auditService';
import { ActionType } from '../models/AuditLog';
import { logger } from '../utils/logger';

/**
 * Extended request interface with user context
 * Will be populated by authentication middleware when implemented
 */
export interface AuditableRequest extends Request {
  user?: {
    id: string;
    username?: string;
  };
}

/**
 * Route pattern matching for audit logging
 * Maps route patterns to action types and entity types
 */
interface RoutePattern {
  method: string;
  pattern: RegExp;
  actionType: ActionType;
  extractMetadata: (req: AuditableRequest, res: Response) => Record<string, any>;
}

/**
 * Define route patterns that should be audited
 */
const AUDITABLE_ROUTES: RoutePattern[] = [
  // Document upload
  {
    method: 'POST',
    pattern: /^\/api\/documents\/?$/,
    actionType: ActionType.DOCUMENT_UPLOAD,
    extractMetadata: (req, res) => {
      const file = (req as any).file as Express.Multer.File | undefined;
      return {
        filename: file?.filename,
        original_filename: file?.originalname,
        file_size: file?.size,
        file_path: file?.path,
        supplier_id: req.body?.supplier_id,
        document_type: req.body?.document_type,
        status_code: res.statusCode,
      };
    },
  },
  // Document status change (update)
  {
    method: 'PATCH',
    pattern: /^\/api\/documents\/\d+$/,
    actionType: ActionType.DOCUMENT_STATUS_CHANGE,
    extractMetadata: (req, res) => ({
      document_id: parseInt(req.params.id, 10),
      previous_status: req.body?.previous_status,
      new_status: req.body?.status,
      reason: req.body?.reason,
      status_code: res.statusCode,
    }),
  },
  // Document deletion
  {
    method: 'DELETE',
    pattern: /^\/api\/documents\/\d+$/,
    actionType: ActionType.DOCUMENT_DELETE,
    extractMetadata: (req, res) => ({
      document_id: parseInt(req.params.id, 10),
      status_code: res.statusCode,
    }),
  },
];

/**
 * Find matching route pattern for the current request
 */
function findRoutePattern(req: Request): RoutePattern | null {
  const method = req.method;
  const path = req.path;

  for (const route of AUDITABLE_ROUTES) {
    if (route.method === method && route.pattern.test(path)) {
      return route;
    }
  }

  return null;
}

/**
 * Extract user ID from request
 * Returns null if no authentication is present (for now)
 */
function extractUserId(req: AuditableRequest): string | null {
  // When authentication is implemented, this will extract user from req.user
  return req.user?.id || null;
}

/**
 * Create audit middleware factory
 *
 * This middleware automatically logs auditable HTTP requests after response completion.
 * It captures user context, action type, and relevant metadata based on the route.
 *
 * @param pool - PostgreSQL connection pool
 * @returns Express middleware function
 *
 * @example
 * ```typescript
 * const auditMiddleware = createAuditMiddleware(pool);
 * app.use(auditMiddleware);
 * ```
 */
export function createAuditMiddleware(pool: Pool) {
  const auditService = new AuditService(pool);

  return async (req: AuditableRequest, res: Response, next: NextFunction): Promise<void> => {
    // Check if this route should be audited
    const routePattern = findRoutePattern(req);

    if (!routePattern) {
      // Not an auditable route, skip
      return next();
    }

    // Listen for response finish event to create audit log
    res.on('finish', async () => {
      try {
        // Extract metadata from request/response
        const metadata = routePattern.extractMetadata(req, res);
        const userId = extractUserId(req);

        // Only log successful operations (2xx status codes)
        // Failed operations should be handled by error handler
        if (res.statusCode >= 200 && res.statusCode < 300) {
          // Create audit log based on action type
          switch (routePattern.actionType) {
            case ActionType.DOCUMENT_UPLOAD:
              if (metadata.filename) {
                await auditService.logDocumentUpload(
                  {
                    filename: metadata.filename,
                    original_filename: metadata.original_filename,
                    file_size: metadata.file_size,
                    file_path: metadata.file_path,
                    supplier_id: metadata.supplier_id,
                    document_type: metadata.document_type,
                  },
                  userId
                );
              }
              break;

            case ActionType.DOCUMENT_STATUS_CHANGE:
              if (metadata.document_id && metadata.new_status) {
                await auditService.logDocumentStatusChange(
                  {
                    document_id: metadata.document_id,
                    filename: metadata.filename || 'unknown',
                    previous_status: metadata.previous_status || 'unknown',
                    new_status: metadata.new_status,
                    reason: metadata.reason,
                  },
                  userId
                );
              }
              break;

            case ActionType.DOCUMENT_DELETE:
              if (metadata.document_id) {
                await auditService.logDocumentDelete(
                  {
                    document_id: metadata.document_id,
                    filename: metadata.filename || 'unknown',
                    file_path: metadata.file_path || 'unknown',
                    supplier_id: metadata.supplier_id,
                    processing_status: metadata.processing_status,
                  },
                  userId
                );
              }
              break;

            default:
              logger.warn(`Unhandled audit action type: ${routePattern.actionType}`);
          }
        }
      } catch (error) {
        // Log audit failure but don't affect the response
        logger.error('Failed to create audit log', error as Error);
      }
    });

    next();
  };
}

/**
 * Manual audit logging helper for custom audit events
 *
 * Use this when you need to manually trigger audit logging outside of HTTP middleware,
 * such as for scheduled tasks, background jobs, or complex workflows.
 *
 * @param pool - PostgreSQL connection pool
 * @returns AuditService instance
 *
 * @example
 * ```typescript
 * const auditService = getAuditService(pool);
 * await auditService.logComplianceCheck({ ... }, userId);
 * ```
 */
export function getAuditService(pool: Pool): AuditService {
  return new AuditService(pool);
}
