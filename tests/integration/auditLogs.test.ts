import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { Express } from 'express';
import request from 'supertest';
import { createApp } from '../../src/index';
import { databaseConfig } from '../../src/config/database';
import { ActionType, EntityType } from '../../src/models/AuditLog';

/**
 * Integration Test: Audit Log API Endpoints
 *
 * This test suite validates the audit log API endpoints:
 * 1. GET /api/audit-logs - List audit logs with filtering and pagination
 * 2. GET /api/audit-logs/:id - Get a single audit log by ID
 * 3. GET /api/audit-logs/export - Export audit logs to CSV/JSON
 */
describe('Integration: Audit Log API', () => {
  let pool: Pool;
  let app: Express;

  beforeAll(async () => {
    // Create database pool for testing
    // Use test database if TEST_DB_NAME is set, otherwise use default
    const testDbConfig = {
      ...databaseConfig,
      database: process.env.TEST_DB_NAME || databaseConfig.database,
    };

    pool = new Pool(testDbConfig);

    // Wait for database connection
    const client = await pool.connect();
    client.release();

    // Run migrations to create tables
    await runMigrations(pool);

    // Create Express app with test database pool
    app = createApp(pool);
  });

  afterAll(async () => {
    // Clean up test data
    await pool.query('DELETE FROM audit_logs');

    // Close database pool
    await pool.end();
  });

  beforeEach(async () => {
    // Clean up before each test
    await pool.query('DELETE FROM audit_logs');
  });

  describe('GET /api/audit-logs', () => {
    it('should return an empty list when no audit logs exist', async () => {
      const response = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      expect(response.body).toHaveProperty('data');
      expect(response.body).toHaveProperty('pagination');
      expect(Array.isArray(response.body.data)).toBe(true);
      expect(response.body.data.length).toBe(0);
      expect(response.body.pagination).toMatchObject({
        total: 0,
        limit: 50,
        offset: 0,
        has_more: false,
      });
    });

    it('should list all audit logs', async () => {
      // Create test audit logs
      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 1,
        after_value: { filename: 'test.pdf' },
      });

      await createAuditLog(pool, {
        user_id: 'user456',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 2,
        after_value: { status: 'pass' },
      });

      const response = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      expect(response.body.data).toHaveLength(2);
      expect(response.body.pagination).toMatchObject({
        total: 2,
        limit: 50,
        offset: 0,
        has_more: false,
      });

      // Verify logs are ordered by timestamp DESC (newest first)
      expect(response.body.data[0].action_type).toBe(ActionType.COMPLIANCE_CHECK_EXECUTION);
      expect(response.body.data[1].action_type).toBe(ActionType.DOCUMENT_UPLOAD);
    });

    it('should filter audit logs by user_id', async () => {
      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      await createAuditLog(pool, {
        user_id: 'user456',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      const response = await request(app)
        .get('/api/audit-logs?user_id=user123')
        .expect(200);

      expect(response.body.data).toHaveLength(1);
      expect(response.body.data[0].user_id).toBe('user123');
      expect(response.body.pagination.total).toBe(1);
    });

    it('should filter audit logs by action_type', async () => {
      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
      });

      const response = await request(app)
        .get(`/api/audit-logs?action_type=${ActionType.DOCUMENT_UPLOAD}`)
        .expect(200);

      expect(response.body.data).toHaveLength(1);
      expect(response.body.data[0].action_type).toBe(ActionType.DOCUMENT_UPLOAD);
    });

    it('should filter audit logs by entity_type', async () => {
      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
      });

      const response = await request(app)
        .get(`/api/audit-logs?entity_type=${EntityType.DOCUMENT}`)
        .expect(200);

      expect(response.body.data).toHaveLength(1);
      expect(response.body.data[0].entity_type).toBe(EntityType.DOCUMENT);
    });

    it('should filter audit logs by entity_id', async () => {
      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 100,
      });

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: 200,
      });

      const response = await request(app)
        .get('/api/audit-logs?entity_id=100')
        .expect(200);

      expect(response.body.data).toHaveLength(1);
      expect(response.body.data[0].entity_id).toBe(100);
    });

    it('should filter audit logs by date range', async () => {
      const now = new Date();
      const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const tomorrow = new Date(now.getTime() + 24 * 60 * 60 * 1000);

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        timestamp: yesterday,
      });

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        timestamp: now,
      });

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        timestamp: tomorrow,
      });

      // Filter logs from yesterday to now
      const response = await request(app)
        .get(`/api/audit-logs?start_date=${yesterday.toISOString()}&end_date=${now.toISOString()}`)
        .expect(200);

      expect(response.body.data).toHaveLength(2);
      expect(response.body.pagination.total).toBe(2);
    });

    it('should support pagination with limit and offset', async () => {
      // Create 5 audit logs
      for (let i = 0; i < 5; i++) {
        await createAuditLog(pool, {
          user_id: `user${i}`,
          action_type: ActionType.DOCUMENT_UPLOAD,
          entity_type: EntityType.DOCUMENT,
        });
      }

      // Get first 2 logs
      const response1 = await request(app)
        .get('/api/audit-logs?limit=2&offset=0')
        .expect(200);

      expect(response1.body.data).toHaveLength(2);
      expect(response1.body.pagination).toMatchObject({
        total: 5,
        limit: 2,
        offset: 0,
        has_more: true,
      });

      // Get next 2 logs
      const response2 = await request(app)
        .get('/api/audit-logs?limit=2&offset=2')
        .expect(200);

      expect(response2.body.data).toHaveLength(2);
      expect(response2.body.pagination).toMatchObject({
        total: 5,
        limit: 2,
        offset: 2,
        has_more: true,
      });

      // Ensure different logs returned
      expect(response1.body.data[0].id).not.toBe(response2.body.data[0].id);
    });

    it('should cap limit at 1000', async () => {
      const response = await request(app)
        .get('/api/audit-logs?limit=5000')
        .expect(200);

      expect(response.body.pagination.limit).toBe(1000);
    });

    it('should combine multiple filters', async () => {
      const now = new Date();

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 100,
        timestamp: now,
      });

      await createAuditLog(pool, {
        user_id: 'user456',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 100,
        timestamp: now,
      });

      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 200,
        timestamp: now,
      });

      // Filter by user_id, action_type, and entity_type
      const response = await request(app)
        .get(`/api/audit-logs?user_id=user123&action_type=${ActionType.DOCUMENT_UPLOAD}&entity_type=${EntityType.DOCUMENT}`)
        .expect(200);

      expect(response.body.data).toHaveLength(1);
      expect(response.body.data[0]).toMatchObject({
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 100,
      });
    });

    it('should return 400 for invalid action_type', async () => {
      const response = await request(app)
        .get('/api/audit-logs?action_type=invalid_action')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_ACTION_TYPE',
      });
    });

    it('should return 400 for invalid entity_type', async () => {
      const response = await request(app)
        .get('/api/audit-logs?entity_type=invalid_entity')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_ENTITY_TYPE',
      });
    });

    it('should return 400 for invalid entity_id', async () => {
      const response = await request(app)
        .get('/api/audit-logs?entity_id=not_a_number')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_ENTITY_ID',
      });
    });

    it('should return 400 for invalid start_date', async () => {
      const response = await request(app)
        .get('/api/audit-logs?start_date=invalid_date')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_START_DATE',
      });
    });

    it('should return 400 for invalid end_date', async () => {
      const response = await request(app)
        .get('/api/audit-logs?end_date=invalid_date')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_END_DATE',
      });
    });

    it('should return 400 for invalid limit', async () => {
      const response = await request(app)
        .get('/api/audit-logs?limit=-5')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_LIMIT',
      });
    });

    it('should return 400 for invalid offset', async () => {
      const response = await request(app)
        .get('/api/audit-logs?offset=-1')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_OFFSET',
      });
    });
  });

  describe('GET /api/audit-logs/:id', () => {
    it('should retrieve a single audit log by ID', async () => {
      const log = await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
        before_value: null,
        after_value: { filename: 'test.pdf', size: 1024 },
        metadata: { ip_address: '127.0.0.1' },
      });

      const response = await request(app)
        .get(`/api/audit-logs/${log.id}`)
        .expect(200);

      expect(response.body).toMatchObject({
        id: log.id,
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 42,
      });

      expect(response.body.timestamp).toBeDefined();
      expect(response.body.created_at).toBeDefined();
      expect(response.body.before_value).toBeNull();
      expect(response.body.after_value).toMatchObject({
        filename: 'test.pdf',
        size: 1024,
      });
      expect(response.body.metadata).toMatchObject({
        ip_address: '127.0.0.1',
      });
    });

    it('should return 404 when audit log does not exist', async () => {
      const response = await request(app)
        .get('/api/audit-logs/99999')
        .expect(404);

      expect(response.body.error).toMatchObject({
        name: 'NotFoundError',
        code: 'AUDIT_LOG_NOT_FOUND',
      });
    });

    it('should return 400 for invalid audit log ID', async () => {
      const response = await request(app)
        .get('/api/audit-logs/invalid_id')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_ID',
      });
    });
  });

  describe('GET /api/audit-logs/export', () => {
    beforeEach(async () => {
      // Create test audit logs for export
      await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: 1,
        after_value: { filename: 'doc1.pdf' },
      });

      await createAuditLog(pool, {
        user_id: 'user456',
        action_type: ActionType.COMPLIANCE_CHECK_EXECUTION,
        entity_type: EntityType.COMPLIANCE_CHECK,
        entity_id: 2,
        after_value: { status: 'pass' },
      });

      await createAuditLog(pool, {
        user_id: 'user789',
        action_type: ActionType.REPORT_GENERATION,
        entity_type: EntityType.REPORT,
        entity_id: 3,
        after_value: { type: 'compliance_summary' },
      });
    });

    it('should export audit logs in JSON format by default', async () => {
      const response = await request(app)
        .get('/api/audit-logs/export')
        .expect(200);

      expect(response.headers['content-type']).toContain('application/json');
      expect(response.headers['content-disposition']).toContain('attachment');
      expect(response.headers['content-disposition']).toContain('audit-logs-');
      expect(response.headers['content-disposition']).toContain('.json');

      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBe(3);
    });

    it('should export audit logs in JSON format when format=json', async () => {
      const response = await request(app)
        .get('/api/audit-logs/export?format=json')
        .expect(200);

      expect(response.headers['content-type']).toContain('application/json');
      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBe(3);

      // Verify structure of first log
      expect(response.body[0]).toHaveProperty('id');
      expect(response.body[0]).toHaveProperty('timestamp');
      expect(response.body[0]).toHaveProperty('user_id');
      expect(response.body[0]).toHaveProperty('action_type');
      expect(response.body[0]).toHaveProperty('entity_type');
    });

    it('should export audit logs in CSV format when format=csv', async () => {
      const response = await request(app)
        .get('/api/audit-logs/export?format=csv')
        .expect(200);

      expect(response.headers['content-type']).toContain('text/csv');
      expect(response.headers['content-disposition']).toContain('attachment');
      expect(response.headers['content-disposition']).toContain('audit-logs-');
      expect(response.headers['content-disposition']).toContain('.csv');

      const csvContent = response.text;
      const lines = csvContent.split('\n');

      // Verify CSV header
      expect(lines[0]).toContain('id,timestamp,user_id,action_type,entity_type');

      // Verify at least 4 lines (header + 3 data rows)
      expect(lines.length).toBeGreaterThanOrEqual(4);

      // Verify CSV contains expected data
      expect(csvContent).toContain('user123');
      expect(csvContent).toContain('user456');
      expect(csvContent).toContain('user789');
      expect(csvContent).toContain(ActionType.DOCUMENT_UPLOAD);
      expect(csvContent).toContain(ActionType.COMPLIANCE_CHECK_EXECUTION);
      expect(csvContent).toContain(ActionType.REPORT_GENERATION);
    });

    it('should apply filters to export', async () => {
      const response = await request(app)
        .get(`/api/audit-logs/export?format=json&user_id=user123`)
        .expect(200);

      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBe(1);
      expect(response.body[0].user_id).toBe('user123');
    });

    it('should export all logs without pagination limits', async () => {
      // Create more logs (total will be 13 with the 3 from beforeEach)
      for (let i = 0; i < 10; i++) {
        await createAuditLog(pool, {
          user_id: `bulk_user_${i}`,
          action_type: ActionType.DOCUMENT_UPLOAD,
          entity_type: EntityType.DOCUMENT,
        });
      }

      const response = await request(app)
        .get('/api/audit-logs/export?format=json')
        .expect(200);

      // Should return all 13 logs, not limited to default 50
      expect(response.body.length).toBe(13);
    });

    it('should return 400 for invalid export format', async () => {
      const response = await request(app)
        .get('/api/audit-logs/export?format=xml')
        .expect(400);

      expect(response.body.error).toMatchObject({
        name: 'ValidationError',
        code: 'INVALID_FORMAT',
      });
    });

    it('should handle CSV export with special characters', async () => {
      await createAuditLog(pool, {
        user_id: 'user_special',
        action_type: ActionType.CONFIG_CHANGE,
        entity_type: EntityType.CONFIG,
        after_value: { setting: 'value, with, commas', description: 'Has "quotes"' },
      });

      const response = await request(app)
        .get('/api/audit-logs/export?format=csv&user_id=user_special')
        .expect(200);

      const csvContent = response.text;

      // CSV should escape commas and quotes properly
      expect(csvContent).toContain('user_special');
      // Special characters in JSON should be properly escaped in CSV
      expect(csvContent).toContain('value, with, commas');
    });

    it('should apply action_type filter to export', async () => {
      const response = await request(app)
        .get(`/api/audit-logs/export?format=json&action_type=${ActionType.DOCUMENT_UPLOAD}`)
        .expect(200);

      expect(response.body.length).toBe(1);
      expect(response.body[0].action_type).toBe(ActionType.DOCUMENT_UPLOAD);
    });

    it('should apply date range filter to export', async () => {
      const now = new Date();
      const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);

      const response = await request(app)
        .get(`/api/audit-logs/export?format=json&start_date=${oneHourAgo.toISOString()}`)
        .expect(200);

      // All test logs were created within the last hour
      expect(response.body.length).toBe(3);
    });
  });

  describe('Audit Log Immutability', () => {
    it('should verify audit logs cannot be modified (no PUT/PATCH endpoints)', async () => {
      const log = await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      // Attempt PUT (should return 404 as route doesn't exist)
      await request(app)
        .put(`/api/audit-logs/${log.id}`)
        .send({ user_id: 'hacker' })
        .expect(404);

      // Attempt PATCH (should return 404 as route doesn't exist)
      await request(app)
        .patch(`/api/audit-logs/${log.id}`)
        .send({ user_id: 'hacker' })
        .expect(404);
    });

    it('should verify audit logs cannot be deleted (no DELETE endpoint)', async () => {
      const log = await createAuditLog(pool, {
        user_id: 'user123',
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
      });

      // Attempt DELETE (should return 404 as route doesn't exist)
      await request(app)
        .delete(`/api/audit-logs/${log.id}`)
        .expect(404);

      // Verify log still exists
      const response = await request(app)
        .get(`/api/audit-logs/${log.id}`)
        .expect(200);

      expect(response.body.id).toBe(log.id);
    });
  });
});

/**
 * Helper function to create an audit log for testing
 */
async function createAuditLog(
  pool: Pool,
  data: {
    user_id?: string;
    action_type: ActionType;
    entity_type: EntityType;
    entity_id?: number;
    before_value?: any;
    after_value?: any;
    metadata?: any;
    timestamp?: Date;
  }
): Promise<any> {
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
    data.timestamp || new Date(),
    data.user_id || null,
    data.action_type,
    data.entity_type,
    data.entity_id || null,
    data.before_value ? JSON.stringify(data.before_value) : null,
    data.after_value ? JSON.stringify(data.after_value) : null,
    JSON.stringify(data.metadata || {}),
  ];

  const result = await pool.query(query, values);
  return result.rows[0];
}

/**
 * Run database migrations
 */
async function runMigrations(pool: Pool): Promise<void> {
  const migrationsDir = path.join(__dirname, '../../migrations');

  // Read migration files
  const migration001 = await fs.readFile(
    path.join(migrationsDir, '001_create_documents_table.sql'),
    'utf8'
  );
  const migration002 = await fs.readFile(
    path.join(migrationsDir, '002_create_extraction_results_table.sql'),
    'utf8'
  );
  const migration003 = await fs.readFile(
    path.join(migrationsDir, '003_create_audit_logs_table.sql'),
    'utf8'
  );

  // Execute migrations
  await pool.query(migration001);
  await pool.query(migration002);
  await pool.query(migration003);
}
