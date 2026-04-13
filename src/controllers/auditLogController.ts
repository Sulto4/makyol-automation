import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';
import { AuditLogModel, AuditLogFilters, ActionType, EntityType } from '../models/AuditLog';
import { logger } from '../utils/logger';

/**
 * Audit Log controller class
 * Handles HTTP requests for viewing and exporting audit logs
 */
export class AuditLogController {
  private auditLogModel: AuditLogModel;

  constructor(pool: Pool) {
    this.auditLogModel = new AuditLogModel(pool);
  }

  /**
   * List audit logs with filtering and pagination
   *
   * GET /api/audit-logs
   *
   * Query parameters:
   * - user_id: string (filter by user ID)
   * - action_type: ActionType (filter by action type)
   * - entity_type: EntityType (filter by entity type)
   * - entity_id: number (filter by entity ID)
   * - start_date: ISO date string (filter by date range start)
   * - end_date: ISO date string (filter by date range end)
   * - limit: number (pagination limit, default 50, max 1000)
   * - offset: number (pagination offset, default 0)
   *
   * @example
   * GET /api/audit-logs?action_type=document_upload&limit=20&offset=0
   * GET /api/audit-logs?user_id=user123&start_date=2024-01-01
   * GET /api/audit-logs?entity_type=document&entity_id=42
   *
   * Response (200):
   * {
   *   "data": [
   *     { id, timestamp, user_id, action_type, entity_type, entity_id, before_value, after_value, metadata, created_at },
   *     ...
   *   ],
   *   "pagination": {
   *     "total": 150,
   *     "limit": 50,
   *     "offset": 0,
   *     "has_more": true
   *   }
   * }
   */
  async listAuditLogs(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      // Parse and validate query parameters
      const filters: AuditLogFilters = {};

      if (req.query.user_id) {
        filters.user_id = req.query.user_id as string;
      }

      if (req.query.action_type) {
        const actionType = req.query.action_type as string;
        // Validate action type
        if (!Object.values(ActionType).includes(actionType as ActionType)) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: `Invalid action_type. Must be one of: ${Object.values(ActionType).join(', ')}`,
              code: 'INVALID_ACTION_TYPE',
            }
          });
          return;
        }
        filters.action_type = actionType as ActionType;
      }

      if (req.query.entity_type) {
        const entityType = req.query.entity_type as string;
        // Validate entity type
        if (!Object.values(EntityType).includes(entityType as EntityType)) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: `Invalid entity_type. Must be one of: ${Object.values(EntityType).join(', ')}`,
              code: 'INVALID_ENTITY_TYPE',
            }
          });
          return;
        }
        filters.entity_type = entityType as EntityType;
      }

      if (req.query.entity_id) {
        const entityId = parseInt(req.query.entity_id as string, 10);
        if (isNaN(entityId)) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'entity_id must be a valid number',
              code: 'INVALID_ENTITY_ID',
            }
          });
          return;
        }
        filters.entity_id = entityId;
      }

      if (req.query.start_date) {
        const startDate = new Date(req.query.start_date as string);
        if (isNaN(startDate.getTime())) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'start_date must be a valid ISO date string',
              code: 'INVALID_START_DATE',
            }
          });
          return;
        }
        filters.start_date = startDate;
      }

      if (req.query.end_date) {
        const endDate = new Date(req.query.end_date as string);
        if (isNaN(endDate.getTime())) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'end_date must be a valid ISO date string',
              code: 'INVALID_END_DATE',
            }
          });
          return;
        }
        filters.end_date = endDate;
      }

      // Parse pagination parameters
      let limit = 50; // default
      if (req.query.limit) {
        limit = parseInt(req.query.limit as string, 10);
        if (isNaN(limit) || limit <= 0) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'limit must be a positive number',
              code: 'INVALID_LIMIT',
            }
          });
          return;
        }
        // Cap limit at 1000
        if (limit > 1000) {
          limit = 1000;
        }
      }
      filters.limit = limit;

      let offset = 0; // default
      if (req.query.offset) {
        offset = parseInt(req.query.offset as string, 10);
        if (isNaN(offset) || offset < 0) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'offset must be a non-negative number',
              code: 'INVALID_OFFSET',
            }
          });
          return;
        }
      }
      filters.offset = offset;

      // Fetch audit logs with filters
      const auditLogs = await this.auditLogModel.findAll(filters);

      // Get total count for pagination (excluding limit/offset)
      const total = await this.auditLogModel.count({
        user_id: filters.user_id,
        action_type: filters.action_type,
        entity_type: filters.entity_type,
        entity_id: filters.entity_id,
        start_date: filters.start_date,
        end_date: filters.end_date,
      });

      logger.info(`Retrieved ${auditLogs.length} audit logs (total: ${total})`);

      // Return paginated response
      res.status(200).json({
        data: auditLogs,
        pagination: {
          total,
          limit,
          offset,
          has_more: offset + auditLogs.length < total,
        }
      });

    } catch (error) {
      next(error);
    }
  }

  /**
   * Get a single audit log by ID
   *
   * GET /api/audit-logs/:id
   *
   * @example
   * GET /api/audit-logs/123
   *
   * Response (200):
   * {
   *   "id": 123,
   *   "timestamp": "2024-01-15T10:30:00Z",
   *   "user_id": "user123",
   *   "action_type": "document_upload",
   *   "entity_type": "document",
   *   "entity_id": 42,
   *   "before_value": null,
   *   "after_value": { ... },
   *   "metadata": { ... },
   *   "created_at": "2024-01-15T10:30:00Z"
   * }
   *
   * Response (404):
   * {
   *   "error": {
   *     "name": "NotFoundError",
   *     "message": "Audit log not found",
   *     "code": "AUDIT_LOG_NOT_FOUND"
   *   }
   * }
   */
  async getAuditLogById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const id = parseInt(req.params.id, 10);

      if (isNaN(id)) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Invalid audit log ID',
            code: 'INVALID_ID',
          }
        });
        return;
      }

      const auditLog = await this.auditLogModel.findById(id);

      if (!auditLog) {
        res.status(404).json({
          error: {
            name: 'NotFoundError',
            message: 'Audit log not found',
            code: 'AUDIT_LOG_NOT_FOUND',
          }
        });
        return;
      }

      logger.info(`Retrieved audit log ${id}`);
      res.status(200).json(auditLog);

    } catch (error) {
      next(error);
    }
  }

  /**
   * Export audit logs to CSV or JSON
   *
   * GET /api/audit-logs/export
   *
   * Query parameters:
   * - format: 'csv' | 'json' (required, default: 'json')
   * - All filters from listAuditLogs (user_id, action_type, entity_type, entity_id, start_date, end_date)
   * - Note: limit and offset are NOT applied for export (exports all matching records)
   *
   * @example
   * GET /api/audit-logs/export?format=csv&action_type=document_upload
   * GET /api/audit-logs/export?format=json&start_date=2024-01-01&end_date=2024-01-31
   *
   * Response (200):
   * - CSV format: text/csv with Content-Disposition header for download
   * - JSON format: application/json array of audit log objects
   */
  async exportAuditLogs(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const format = (req.query.format as string) || 'json';

      // Validate format
      if (format !== 'csv' && format !== 'json') {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Invalid format. Must be "csv" or "json"',
            code: 'INVALID_FORMAT',
          }
        });
        return;
      }

      // Parse filters (same as listAuditLogs, but without limit/offset)
      const filters: AuditLogFilters = {};

      if (req.query.user_id) {
        filters.user_id = req.query.user_id as string;
      }

      if (req.query.action_type) {
        const actionType = req.query.action_type as string;
        if (!Object.values(ActionType).includes(actionType as ActionType)) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: `Invalid action_type. Must be one of: ${Object.values(ActionType).join(', ')}`,
              code: 'INVALID_ACTION_TYPE',
            }
          });
          return;
        }
        filters.action_type = actionType as ActionType;
      }

      if (req.query.entity_type) {
        const entityType = req.query.entity_type as string;
        if (!Object.values(EntityType).includes(entityType as EntityType)) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: `Invalid entity_type. Must be one of: ${Object.values(EntityType).join(', ')}`,
              code: 'INVALID_ENTITY_TYPE',
            }
          });
          return;
        }
        filters.entity_type = entityType as EntityType;
      }

      if (req.query.entity_id) {
        const entityId = parseInt(req.query.entity_id as string, 10);
        if (isNaN(entityId)) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'entity_id must be a valid number',
              code: 'INVALID_ENTITY_ID',
            }
          });
          return;
        }
        filters.entity_id = entityId;
      }

      if (req.query.start_date) {
        const startDate = new Date(req.query.start_date as string);
        if (isNaN(startDate.getTime())) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'start_date must be a valid ISO date string',
              code: 'INVALID_START_DATE',
            }
          });
          return;
        }
        filters.start_date = startDate;
      }

      if (req.query.end_date) {
        const endDate = new Date(req.query.end_date as string);
        if (isNaN(endDate.getTime())) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'end_date must be a valid ISO date string',
              code: 'INVALID_END_DATE',
            }
          });
          return;
        }
        filters.end_date = endDate;
      }

      // Fetch all audit logs matching filters (no pagination)
      const auditLogs = await this.auditLogModel.findAll(filters);

      logger.info(`Exporting ${auditLogs.length} audit logs in ${format} format`);

      if (format === 'csv') {
        // Generate CSV
        const csv = this.generateCSV(auditLogs);

        // Set headers for CSV download
        res.setHeader('Content-Type', 'text/csv');
        res.setHeader('Content-Disposition', `attachment; filename="audit-logs-${new Date().toISOString()}.csv"`);
        res.status(200).send(csv);

      } else {
        // JSON format
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Content-Disposition', `attachment; filename="audit-logs-${new Date().toISOString()}.json"`);
        res.status(200).json(auditLogs);
      }

    } catch (error) {
      next(error);
    }
  }

  /**
   * Generate CSV from audit logs
   * Format: timestamp, user_id, action_type, entity_type, entity_id, before_value, after_value, metadata
   */
  private generateCSV(auditLogs: any[]): string {
    // CSV header
    const headers = [
      'id',
      'timestamp',
      'user_id',
      'action_type',
      'entity_type',
      'entity_id',
      'before_value',
      'after_value',
      'metadata',
      'created_at'
    ];

    const rows = [headers.join(',')];

    // Add data rows
    for (const log of auditLogs) {
      const row = [
        log.id,
        log.timestamp ? new Date(log.timestamp).toISOString() : '',
        this.escapeCSV(log.user_id || ''),
        this.escapeCSV(log.action_type || ''),
        this.escapeCSV(log.entity_type || ''),
        log.entity_id || '',
        this.escapeCSV(log.before_value ? JSON.stringify(log.before_value) : ''),
        this.escapeCSV(log.after_value ? JSON.stringify(log.after_value) : ''),
        this.escapeCSV(log.metadata ? JSON.stringify(log.metadata) : '{}'),
        log.created_at ? new Date(log.created_at).toISOString() : ''
      ];
      rows.push(row.join(','));
    }

    return rows.join('\n');
  }

  /**
   * Escape CSV field (handle commas, quotes, newlines)
   */
  private escapeCSV(field: string): string {
    if (field.includes(',') || field.includes('"') || field.includes('\n')) {
      return `"${field.replace(/"/g, '""')}"`;
    }
    return field;
  }
}
