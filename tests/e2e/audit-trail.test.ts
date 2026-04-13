import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { Express } from 'express';
import request from 'supertest';
import { createApp } from '../../src/index';
import { databaseConfig } from '../../src/config/database';
import { ActionType, EntityType } from '../../src/models/AuditLog';

/**
 * End-to-End Test: Audit Trail in Document Workflow
 *
 * This test suite validates that audit logging is properly integrated into the document workflow:
 * 1. Upload a Romanian certificate PDF
 * 2. Verify audit logs are created for document upload
 * 3. Verify audit logs are created for status changes (PENDING -> PROCESSING -> COMPLETED)
 * 4. Query and filter audit logs
 * 5. Export audit logs in CSV and JSON formats
 * 6. Verify audit log immutability
 */
describe('E2E: Audit Trail in Document Workflow', () => {
  let pool: Pool;
  let app: Express;
  const romanianCertPath = path.join(__dirname, '../fixtures/romanian-cert.pdf');

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
    await pool.query('DELETE FROM extraction_results');
    await pool.query('DELETE FROM documents');

    // Close database pool
    await pool.end();
  });

  beforeEach(async () => {
    // Clean up before each test
    await pool.query('DELETE FROM audit_logs');
    await pool.query('DELETE FROM extraction_results');
    await pool.query('DELETE FROM documents');
  });

  describe('Document Upload with Audit Trail', () => {
    it('should create audit logs for the complete document processing workflow', async () => {
      // Verify fixture file exists
      const fileExists = await fs.access(romanianCertPath).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);

      // Step 1: Upload document
      const uploadResponse = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      expect(uploadResponse.body).toHaveProperty('document');
      expect(uploadResponse.body).toHaveProperty('extraction');

      const { document } = uploadResponse.body;
      expect(document.id).toBeDefined();
      expect(document.processing_status).toBe('completed');

      // Step 2: Verify audit logs were created
      const auditLogsResponse = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      expect(auditLogsResponse.body).toHaveProperty('data');
      expect(auditLogsResponse.body).toHaveProperty('pagination');
      expect(Array.isArray(auditLogsResponse.body.data)).toBe(true);

      // Should have 3 audit log entries: upload + 2 status changes
      expect(auditLogsResponse.body.data.length).toBe(3);

      const auditLogs = auditLogsResponse.body.data;

      // Step 3: Verify document upload audit log
      const uploadLog = auditLogs.find((log: any) => log.action_type === ActionType.DOCUMENT_UPLOAD);
      expect(uploadLog).toBeDefined();
      expect(uploadLog).toMatchObject({
        action_type: ActionType.DOCUMENT_UPLOAD,
        entity_type: EntityType.DOCUMENT,
        entity_id: null, // Document ID not yet known at upload time
      });

      expect(uploadLog.metadata).toBeDefined();
      expect(uploadLog.metadata.filename).toContain('romanian-cert.pdf');
      expect(uploadLog.metadata.original_filename).toContain('romanian-cert.pdf');
      expect(uploadLog.metadata.file_size).toBeGreaterThan(0);
      expect(uploadLog.created_at).toBeDefined();

      // Step 4: Verify status change audit logs
      const statusChangeLogs = auditLogs.filter(
        (log: any) => log.action_type === ActionType.DOCUMENT_STATUS_CHANGE
      );
      expect(statusChangeLogs.length).toBe(2);

      // Verify PENDING -> PROCESSING status change
      const processingLog = statusChangeLogs.find(
        (log: any) => log.after_value?.status === 'processing'
      );
      expect(processingLog).toBeDefined();
      expect(processingLog).toMatchObject({
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: document.id,
      });
      expect(processingLog.before_value).toEqual({ status: 'pending' });
      expect(processingLog.after_value).toEqual({ status: 'processing' });
      expect(processingLog.metadata.filename).toContain('romanian-cert.pdf');

      // Verify PROCESSING -> COMPLETED status change
      const completedLog = statusChangeLogs.find(
        (log: any) => log.after_value?.status === 'completed'
      );
      expect(completedLog).toBeDefined();
      expect(completedLog).toMatchObject({
        action_type: ActionType.DOCUMENT_STATUS_CHANGE,
        entity_type: EntityType.DOCUMENT,
        entity_id: document.id,
      });
      expect(completedLog.before_value).toEqual({ status: 'processing' });
      expect(completedLog.after_value).toEqual({ status: 'completed' });
      expect(completedLog.metadata.filename).toContain('romanian-cert.pdf');

      // Step 5: Verify timestamp ordering (upload < processing < completed)
      const uploadTime = new Date(uploadLog.created_at).getTime();
      const processingTime = new Date(processingLog.created_at).getTime();
      const completedTime = new Date(completedLog.created_at).getTime();

      expect(processingTime).toBeGreaterThanOrEqual(uploadTime);
      expect(completedTime).toBeGreaterThanOrEqual(processingTime);
    });

    it('should filter audit logs by action type', async () => {
      // Upload a document to create audit logs
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Filter by DOCUMENT_UPLOAD action type
      const uploadLogsResponse = await request(app)
        .get(`/api/audit-logs?action_type=${ActionType.DOCUMENT_UPLOAD}`)
        .expect(200);

      expect(uploadLogsResponse.body.data).toHaveLength(1);
      expect(uploadLogsResponse.body.data[0].action_type).toBe(ActionType.DOCUMENT_UPLOAD);

      // Filter by DOCUMENT_STATUS_CHANGE action type
      const statusChangeLogsResponse = await request(app)
        .get(`/api/audit-logs?action_type=${ActionType.DOCUMENT_STATUS_CHANGE}`)
        .expect(200);

      expect(statusChangeLogsResponse.body.data).toHaveLength(2);
      statusChangeLogsResponse.body.data.forEach((log: any) => {
        expect(log.action_type).toBe(ActionType.DOCUMENT_STATUS_CHANGE);
      });
    });

    it('should filter audit logs by entity type and entity ID', async () => {
      // Upload a document
      const uploadResponse = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      const documentId = uploadResponse.body.document.id;

      // Filter by entity_type = DOCUMENT
      const documentLogsResponse = await request(app)
        .get(`/api/audit-logs?entity_type=${EntityType.DOCUMENT}`)
        .expect(200);

      // Should get 2 status change logs (upload log has entity_id = null)
      expect(documentLogsResponse.body.data.length).toBeGreaterThanOrEqual(2);
      documentLogsResponse.body.data.forEach((log: any) => {
        expect(log.entity_type).toBe(EntityType.DOCUMENT);
      });

      // Filter by specific document ID
      const specificDocumentLogsResponse = await request(app)
        .get(`/api/audit-logs?entity_type=${EntityType.DOCUMENT}&entity_id=${documentId}`)
        .expect(200);

      expect(specificDocumentLogsResponse.body.data).toHaveLength(2);
      specificDocumentLogsResponse.body.data.forEach((log: any) => {
        expect(log.entity_id).toBe(documentId);
        expect(log.action_type).toBe(ActionType.DOCUMENT_STATUS_CHANGE);
      });
    });

    it('should filter audit logs by date range', async () => {
      // Upload a document
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Get current date range
      const now = new Date();
      const startDate = new Date(now.getTime() - 60000); // 1 minute ago
      const endDate = new Date(now.getTime() + 60000); // 1 minute in future

      // Filter by date range that includes the logs
      const logsInRangeResponse = await request(app)
        .get(`/api/audit-logs?start_date=${startDate.toISOString()}&end_date=${endDate.toISOString()}`)
        .expect(200);

      expect(logsInRangeResponse.body.data.length).toBe(3);

      // Filter by date range that excludes the logs (far in the past)
      const pastStartDate = new Date('2020-01-01T00:00:00.000Z');
      const pastEndDate = new Date('2020-12-31T23:59:59.999Z');

      const logsOutOfRangeResponse = await request(app)
        .get(`/api/audit-logs?start_date=${pastStartDate.toISOString()}&end_date=${pastEndDate.toISOString()}`)
        .expect(200);

      expect(logsOutOfRangeResponse.body.data.length).toBe(0);
    });

    it('should support pagination for audit logs', async () => {
      // Upload multiple documents to create more audit logs
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: path.join(__dirname, '../fixtures/cert-sample-1.pdf') })
        .expect(201);

      // Get first page with limit=2
      const page1Response = await request(app)
        .get('/api/audit-logs?limit=2&offset=0')
        .expect(200);

      expect(page1Response.body.data).toHaveLength(2);
      expect(page1Response.body.pagination).toMatchObject({
        total: 6, // 3 logs per document × 2 documents
        limit: 2,
        offset: 0,
        has_more: true,
      });

      // Get second page with limit=2
      const page2Response = await request(app)
        .get('/api/audit-logs?limit=2&offset=2')
        .expect(200);

      expect(page2Response.body.data).toHaveLength(2);
      expect(page2Response.body.pagination).toMatchObject({
        total: 6,
        limit: 2,
        offset: 2,
        has_more: true,
      });

      // Verify different records on different pages
      const page1Ids = page1Response.body.data.map((log: any) => log.id);
      const page2Ids = page2Response.body.data.map((log: any) => log.id);
      expect(page1Ids).not.toEqual(page2Ids);
    });

    it('should retrieve a single audit log by ID', async () => {
      // Upload a document
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Get all audit logs
      const allLogsResponse = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      const firstLog = allLogsResponse.body.data[0];
      expect(firstLog.id).toBeDefined();

      // Retrieve single audit log by ID
      const singleLogResponse = await request(app)
        .get(`/api/audit-logs/${firstLog.id}`)
        .expect(200);

      expect(singleLogResponse.body).toHaveProperty('id', firstLog.id);
      expect(singleLogResponse.body).toHaveProperty('action_type');
      expect(singleLogResponse.body).toHaveProperty('entity_type');
      expect(singleLogResponse.body).toHaveProperty('created_at');
    });

    it('should return 404 for non-existent audit log ID', async () => {
      const response = await request(app)
        .get('/api/audit-logs/999999')
        .expect(404);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error.code).toBe('AUDIT_LOG_NOT_FOUND');
    });
  });

  describe('Audit Log Export', () => {
    it('should export audit logs to JSON format', async () => {
      // Upload a document to create audit logs
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Export to JSON
      const response = await request(app)
        .get('/api/audit-logs/export?format=json')
        .expect(200);

      expect(response.headers['content-type']).toContain('application/json');
      expect(response.headers['content-disposition']).toMatch(/^attachment; filename="audit-logs-.*\.json"$/);

      expect(Array.isArray(response.body)).toBe(true);
      expect(response.body.length).toBe(3);

      const exportedLog = response.body[0];
      expect(exportedLog).toHaveProperty('id');
      expect(exportedLog).toHaveProperty('action_type');
      expect(exportedLog).toHaveProperty('entity_type');
      expect(exportedLog).toHaveProperty('created_at');
    });

    it('should export audit logs to CSV format', async () => {
      // Upload a document to create audit logs
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Export to CSV
      const response = await request(app)
        .get('/api/audit-logs/export?format=csv')
        .expect(200);

      expect(response.headers['content-type']).toContain('text/csv');
      expect(response.headers['content-disposition']).toMatch(/^attachment; filename="audit-logs-.*\.csv"$/);
      expect(typeof response.text).toBe('string');

      // Verify CSV structure
      const lines = response.text.split('\n').filter(line => line.trim());
      expect(lines.length).toBeGreaterThan(1); // Header + at least 1 data row

      // Verify CSV header
      const header = lines[0];
      expect(header).toContain('id');
      expect(header).toContain('timestamp');
      expect(header).toContain('user_id');
      expect(header).toContain('action_type');
      expect(header).toContain('entity_type');
      expect(header).toContain('entity_id');
      expect(header).toContain('before_value');
      expect(header).toContain('after_value');
      expect(header).toContain('metadata');
      expect(header).toContain('created_at');

      // Verify CSV has 3 data rows (upload + 2 status changes)
      const dataRows = lines.slice(1);
      expect(dataRows.length).toBe(3);
    });

    it('should export filtered audit logs', async () => {
      // Upload a document
      const uploadResponse = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      const documentId = uploadResponse.body.document.id;

      // Export only DOCUMENT_STATUS_CHANGE logs to JSON
      const jsonResponse = await request(app)
        .get(`/api/audit-logs/export?format=json&action_type=${ActionType.DOCUMENT_STATUS_CHANGE}`)
        .expect(200);

      expect(Array.isArray(jsonResponse.body)).toBe(true);
      expect(jsonResponse.body.length).toBe(2);
      jsonResponse.body.forEach((log: any) => {
        expect(log.action_type).toBe(ActionType.DOCUMENT_STATUS_CHANGE);
      });

      // Export logs for specific document to CSV
      const csvResponse = await request(app)
        .get(`/api/audit-logs/export?format=csv&entity_id=${documentId}`)
        .expect(200);

      const lines = csvResponse.text.split('\n').filter(line => line.trim());
      const dataRows = lines.slice(1);
      expect(dataRows.length).toBe(2); // Only status change logs have entity_id
    });

    it('should handle CSV export with special characters', async () => {
      // Create an audit log with special characters in metadata
      await pool.query(`
        INSERT INTO audit_logs (
          user_id, action_type, entity_type, entity_id,
          before_value, after_value, metadata
        ) VALUES (
          'user123',
          '${ActionType.CONFIG_CHANGE}',
          '${EntityType.CONFIG}',
          NULL,
          NULL,
          '{"key": "value"}',
          '{"description": "Test with comma, quote \\"escaped\\", and newline\\n"}'
        )
      `);

      // Export to CSV
      const response = await request(app)
        .get('/api/audit-logs/export?format=csv')
        .expect(200);

      expect(response.headers['content-type']).toContain('text/csv');
      expect(typeof response.text).toBe('string');

      // Verify CSV is properly formatted (no broken rows due to special chars)
      const lines = response.text.split('\n').filter(line => line.trim());
      expect(lines.length).toBeGreaterThan(1);
    });
  });

  describe('Audit Log Immutability', () => {
    it('should not allow modification of audit logs (no PUT/PATCH endpoints)', async () => {
      // Upload a document to create audit logs
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Get audit log ID
      const logsResponse = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      const auditLogId = logsResponse.body.data[0].id;

      // Attempt PUT (should return 404 or 405 Method Not Allowed)
      const putResponse = await request(app)
        .put(`/api/audit-logs/${auditLogId}`)
        .send({ action_type: 'modified' });

      expect([404, 405]).toContain(putResponse.status);

      // Attempt PATCH (should return 404 or 405 Method Not Allowed)
      const patchResponse = await request(app)
        .patch(`/api/audit-logs/${auditLogId}`)
        .send({ action_type: 'modified' });

      expect([404, 405]).toContain(patchResponse.status);
    });

    it('should not allow deletion of audit logs (no DELETE endpoint)', async () => {
      // Upload a document to create audit logs
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Get audit log ID
      const logsResponse = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      const auditLogId = logsResponse.body.data[0].id;
      const initialCount = logsResponse.body.pagination.total;

      // Attempt DELETE (should return 404 or 405 Method Not Allowed)
      const deleteResponse = await request(app)
        .delete(`/api/audit-logs/${auditLogId}`);

      expect([404, 405]).toContain(deleteResponse.status);

      // Verify audit log still exists
      const afterDeleteResponse = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      expect(afterDeleteResponse.body.pagination.total).toBe(initialCount);
    });
  });

  describe('Multiple Document Workflow', () => {
    it('should create separate audit trails for multiple documents', async () => {
      // Upload first document
      const upload1Response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      const doc1Id = upload1Response.body.document.id;

      // Upload second document
      const upload2Response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: path.join(__dirname, '../fixtures/cert-sample-1.pdf') })
        .expect(201);

      const doc2Id = upload2Response.body.document.id;

      // Verify total audit logs (3 per document)
      const allLogsResponse = await request(app)
        .get('/api/audit-logs')
        .expect(200);

      expect(allLogsResponse.body.pagination.total).toBe(6);

      // Verify logs for first document
      const doc1LogsResponse = await request(app)
        .get(`/api/audit-logs?entity_id=${doc1Id}`)
        .expect(200);

      expect(doc1LogsResponse.body.data).toHaveLength(2); // Status change logs only
      doc1LogsResponse.body.data.forEach((log: any) => {
        expect(log.entity_id).toBe(doc1Id);
      });

      // Verify logs for second document
      const doc2LogsResponse = await request(app)
        .get(`/api/audit-logs?entity_id=${doc2Id}`)
        .expect(200);

      expect(doc2LogsResponse.body.data).toHaveLength(2); // Status change logs only
      doc2LogsResponse.body.data.forEach((log: any) => {
        expect(log.entity_id).toBe(doc2Id);
      });

      // Verify logs are distinct
      const doc1LogIds = doc1LogsResponse.body.data.map((log: any) => log.id);
      const doc2LogIds = doc2LogsResponse.body.data.map((log: any) => log.id);
      const intersection = doc1LogIds.filter((id: number) => doc2LogIds.includes(id));
      expect(intersection.length).toBe(0); // No overlap
    });
  });
});

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

  // Execute migrations in order
  await pool.query(migration001);
  await pool.query(migration002);
  await pool.query(migration003);
}
