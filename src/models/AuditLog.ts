import { Pool, QueryResult } from 'pg';

/**
 * Action type enum for audit logs
 */
export enum ActionType {
  DOCUMENT_UPLOAD = 'document_upload',
  DOCUMENT_STATUS_CHANGE = 'document_status_change',
  DOCUMENT_DELETE = 'document_delete',
  COMPLIANCE_CHECK_EXECUTION = 'compliance_check_execution',
  REPORT_GENERATION = 'report_generation',
  USER_LOGIN = 'user_login',
  CONFIG_CHANGE = 'config_change',
}

/**
 * Entity type enum for audit logs
 */
export enum EntityType {
  DOCUMENT = 'document',
  EXTRACTION_RESULT = 'extraction_result',
  COMPLIANCE_CHECK = 'compliance_check',
  REPORT = 'report',
  USER = 'user',
  CONFIG = 'config',
}

/**
 * AuditLog interface matching the audit_logs table schema
 */
export interface AuditLog {
  id: number;
  timestamp: Date;
  user_id: string | null;
  action_type: ActionType;
  entity_type: EntityType;
  entity_id: number | null;
  before_value: Record<string, any> | null;
  after_value: Record<string, any> | null;
  metadata: Record<string, any>;
  created_at: Date;
}

/**
 * Input type for creating a new audit log
 */
export interface CreateAuditLogInput {
  user_id?: string | null;
  action_type: ActionType;
  entity_type: EntityType;
  entity_id?: number | null;
  before_value?: Record<string, any> | null;
  after_value?: Record<string, any> | null;
  metadata?: Record<string, any>;
  timestamp?: Date;
}

/**
 * Filter options for querying audit logs
 */
export interface AuditLogFilters {
  user_id?: string;
  action_type?: ActionType;
  entity_type?: EntityType;
  entity_id?: number;
  start_date?: Date;
  end_date?: Date;
  limit?: number;
  offset?: number;
}

/**
 * AuditLog model class for database operations
 * Note: This model does NOT include update() or delete() methods
 * as audit logs are immutable per system requirements
 */
export class AuditLogModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Create a new audit log entry
   */
  async create(input: CreateAuditLogInput): Promise<AuditLog> {
    const query = `
      INSERT INTO audit_logs (
        timestamp,
        user_id,
        action_type,
        entity_type,
        entity_id,
        before_value,
        after_value,
        metadata
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      RETURNING *
    `;

    const values = [
      input.timestamp || new Date(),
      input.user_id || null,
      input.action_type,
      input.entity_type,
      input.entity_id || null,
      input.before_value ? JSON.stringify(input.before_value) : null,
      input.after_value ? JSON.stringify(input.after_value) : null,
      JSON.stringify(input.metadata || {}),
    ];

    const result: QueryResult<AuditLog> = await this.pool.query(query, values);
    return result.rows[0];
  }

  /**
   * Find an audit log by ID
   */
  async findById(id: number): Promise<AuditLog | null> {
    const query = 'SELECT * FROM audit_logs WHERE id = $1';
    const result: QueryResult<AuditLog> = await this.pool.query(query, [id]);
    return result.rows[0] || null;
  }

  /**
   * Find audit logs by entity type and ID
   */
  async findByEntity(
    entityType: EntityType,
    entityId: number,
    limit?: number,
    offset?: number
  ): Promise<AuditLog[]> {
    let query = 'SELECT * FROM audit_logs WHERE entity_type = $1 AND entity_id = $2';
    const values: any[] = [entityType, entityId];
    let paramIndex = 3;

    query += ' ORDER BY timestamp DESC';

    if (limit) {
      query += ` LIMIT $${paramIndex}`;
      values.push(limit);
      paramIndex++;
    }

    if (offset) {
      query += ` OFFSET $${paramIndex}`;
      values.push(offset);
    }

    const result: QueryResult<AuditLog> = await this.pool.query(query, values);
    return result.rows;
  }

  /**
   * Find audit logs by user ID
   */
  async findByUser(
    userId: string,
    limit?: number,
    offset?: number
  ): Promise<AuditLog[]> {
    let query = 'SELECT * FROM audit_logs WHERE user_id = $1';
    const values: any[] = [userId];
    let paramIndex = 2;

    query += ' ORDER BY timestamp DESC';

    if (limit) {
      query += ` LIMIT $${paramIndex}`;
      values.push(limit);
      paramIndex++;
    }

    if (offset) {
      query += ` OFFSET $${paramIndex}`;
      values.push(offset);
    }

    const result: QueryResult<AuditLog> = await this.pool.query(query, values);
    return result.rows;
  }

  /**
   * Find all audit logs with optional filtering
   */
  async findAll(filters?: AuditLogFilters): Promise<AuditLog[]> {
    let query = 'SELECT * FROM audit_logs';
    const values: any[] = [];
    const whereClauses: string[] = [];
    let paramIndex = 1;

    // Build WHERE clauses based on filters
    if (filters) {
      if (filters.user_id) {
        whereClauses.push(`user_id = $${paramIndex}`);
        values.push(filters.user_id);
        paramIndex++;
      }

      if (filters.action_type) {
        whereClauses.push(`action_type = $${paramIndex}`);
        values.push(filters.action_type);
        paramIndex++;
      }

      if (filters.entity_type) {
        whereClauses.push(`entity_type = $${paramIndex}`);
        values.push(filters.entity_type);
        paramIndex++;
      }

      if (filters.entity_id !== undefined) {
        whereClauses.push(`entity_id = $${paramIndex}`);
        values.push(filters.entity_id);
        paramIndex++;
      }

      if (filters.start_date) {
        whereClauses.push(`timestamp >= $${paramIndex}`);
        values.push(filters.start_date);
        paramIndex++;
      }

      if (filters.end_date) {
        whereClauses.push(`timestamp <= $${paramIndex}`);
        values.push(filters.end_date);
        paramIndex++;
      }
    }

    // Add WHERE clauses if any
    if (whereClauses.length > 0) {
      query += ' WHERE ' + whereClauses.join(' AND ');
    }

    // Order by timestamp descending (newest first)
    query += ' ORDER BY timestamp DESC';

    // Add pagination
    if (filters?.limit) {
      query += ` LIMIT $${paramIndex}`;
      values.push(filters.limit);
      paramIndex++;
    }

    if (filters?.offset) {
      query += ` OFFSET $${paramIndex}`;
      values.push(filters.offset);
    }

    const result: QueryResult<AuditLog> = await this.pool.query(query, values);
    return result.rows;
  }

  /**
   * Count audit logs with optional filtering
   */
  async count(filters?: Omit<AuditLogFilters, 'limit' | 'offset'>): Promise<number> {
    let query = 'SELECT COUNT(*) as count FROM audit_logs';
    const values: any[] = [];
    const whereClauses: string[] = [];
    let paramIndex = 1;

    // Build WHERE clauses based on filters
    if (filters) {
      if (filters.user_id) {
        whereClauses.push(`user_id = $${paramIndex}`);
        values.push(filters.user_id);
        paramIndex++;
      }

      if (filters.action_type) {
        whereClauses.push(`action_type = $${paramIndex}`);
        values.push(filters.action_type);
        paramIndex++;
      }

      if (filters.entity_type) {
        whereClauses.push(`entity_type = $${paramIndex}`);
        values.push(filters.entity_type);
        paramIndex++;
      }

      if (filters.entity_id !== undefined) {
        whereClauses.push(`entity_id = $${paramIndex}`);
        values.push(filters.entity_id);
        paramIndex++;
      }

      if (filters.start_date) {
        whereClauses.push(`timestamp >= $${paramIndex}`);
        values.push(filters.start_date);
        paramIndex++;
      }

      if (filters.end_date) {
        whereClauses.push(`timestamp <= $${paramIndex}`);
        values.push(filters.end_date);
        paramIndex++;
      }
    }

    // Add WHERE clauses if any
    if (whereClauses.length > 0) {
      query += ' WHERE ' + whereClauses.join(' AND ');
    }

    const result: QueryResult<{ count: string }> = await this.pool.query(query, values);
    return parseInt(result.rows[0].count, 10);
  }
}
