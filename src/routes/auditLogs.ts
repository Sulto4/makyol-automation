import { Router } from 'express';
import { Pool } from 'pg';
import { AuditLogController } from '../controllers/auditLogController';

/**
 * Create and configure audit log routes
 *
 * @param pool - PostgreSQL connection pool
 * @returns Configured Express router
 */
export function createAuditLogRoutes(pool: Pool): Router {
  const router = Router();
  const controller = new AuditLogController(pool);

  /**
   * GET /api/audit-logs/export
   * Export audit logs to CSV or JSON format
   *
   * @query format - Export format: 'csv' or 'json' (default: 'json')
   * @query user_id - Filter by user ID (optional)
   * @query action_type - Filter by action type (optional)
   * @query entity_type - Filter by entity type (optional)
   * @query entity_id - Filter by entity ID (optional)
   * @query start_date - Filter by date range start (ISO date string, optional)
   * @query end_date - Filter by date range end (ISO date string, optional)
   * @returns 200 - Audit logs exported (CSV or JSON)
   * @returns 400 - Invalid query parameters
   * @returns 500 - Server error
   */
  router.get('/export', (req, res, next) => controller.exportAuditLogs(req, res, next));

  /**
   * GET /api/audit-logs
   * List all audit logs with optional filtering and pagination
   *
   * @query user_id - Filter by user ID (optional)
   * @query action_type - Filter by action type (optional)
   * @query entity_type - Filter by entity type (optional)
   * @query entity_id - Filter by entity ID (optional)
   * @query start_date - Filter by date range start (ISO date string, optional)
   * @query end_date - Filter by date range end (ISO date string, optional)
   * @query limit - Maximum number of logs to return (default: 50, max: 1000)
   * @query offset - Number of logs to skip (default: 0)
   * @returns 200 - List of audit logs with pagination metadata
   * @returns 400 - Invalid query parameters
   * @returns 500 - Server error
   */
  router.get('/', (req, res, next) => controller.listAuditLogs(req, res, next));

  /**
   * GET /api/audit-logs/:id
   * Retrieve a single audit log entry by ID
   *
   * @param id - Audit log ID
   * @returns 200 - Audit log found
   * @returns 400 - Invalid audit log ID
   * @returns 404 - Audit log not found
   * @returns 500 - Server error
   */
  router.get('/:id', (req, res, next) => controller.getAuditLogById(req, res, next));

  return router;
}

export default createAuditLogRoutes;
