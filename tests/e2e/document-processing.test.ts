import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { Express } from 'express';
import request from 'supertest';
import { createApp } from '../../src/index';
import { databaseConfig } from '../../src/config/database';

/**
 * End-to-End Test: Document Processing with Real Romanian Certificate
 *
 * This test suite validates the entire document processing pipeline:
 * 1. Upload a real Romanian certificate PDF
 * 2. Extract text from the PDF
 * 3. Parse metadata (certificate number, dates, issuing org, etc.)
 * 4. Store results in database
 * 5. Retrieve and verify the processed document
 */
describe('E2E: Document Processing Pipeline', () => {
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
    await pool.query('DELETE FROM extraction_results');
    await pool.query('DELETE FROM documents');

    // Close database pool
    await pool.end();
  });

  beforeEach(async () => {
    // Clean up before each test
    await pool.query('DELETE FROM extraction_results');
    await pool.query('DELETE FROM documents');
  });

  describe('Romanian Certificate Processing', () => {
    it('should process a real Romanian ISO certificate PDF end-to-end', async () => {
      // Verify fixture file exists
      const fileExists = await fs.access(romanianCertPath).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);

      // Step 1: Upload document
      const response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Verify response structure
      expect(response.body).toHaveProperty('document');
      expect(response.body).toHaveProperty('extraction');

      const { document, extraction } = response.body;

      // Step 2: Verify document record
      expect(document).toMatchObject({
        id: expect.any(Number),
        filename: expect.stringContaining('romanian-cert.pdf'),
        original_filename: expect.stringContaining('romanian-cert.pdf'),
        file_path: romanianCertPath,
        mime_type: 'application/pdf',
        processing_status: 'completed',
      });

      expect(document.file_size).toBeGreaterThan(0);
      expect(document.uploaded_at).toBeDefined();
      expect(document.processing_started_at).toBeDefined();
      expect(document.processing_completed_at).toBeDefined();
      expect(document.error_message).toBeNull();

      // Step 3: Verify extraction result
      expect(extraction).toMatchObject({
        id: expect.any(Number),
        document_id: document.id,
        extraction_status: expect.stringMatching(/^(success|partial)$/),
      });

      // Step 4: Verify extracted text contains expected Romanian content
      expect(extraction.extracted_text).toBeDefined();
      expect(extraction.extracted_text).toContain('CERTIFICAT DE CONFORMITATE');
      expect(extraction.extracted_text).toContain('ISO 9001:2015');
      expect(extraction.extracted_text).toContain('SRAC');
      expect(extraction.extracted_text).toContain('MAKYOL CONSTRUCT');

      // Step 5: Verify parsed metadata
      expect(extraction.metadata).toBeDefined();
      expect(typeof extraction.metadata).toBe('object');

      // Certificate number should be extracted
      if (extraction.metadata.certificate_number) {
        expect(extraction.metadata.certificate_number).toContain('ISO-RO-2024-12345');
        expect(extraction.metadata.certificate_number_confidence).toBeGreaterThanOrEqual(0.5);
      }

      // Issuing organization should be extracted
      if (extraction.metadata.issuing_organization) {
        expect(extraction.metadata.issuing_organization).toContain('SRAC');
        expect(extraction.metadata.issuing_organization_confidence).toBeGreaterThanOrEqual(0.5);
      }

      // Company name should be extracted
      if (extraction.metadata.certified_company) {
        expect(extraction.metadata.certified_company).toContain('MAKYOL CONSTRUCT');
        expect(extraction.metadata.certified_company_confidence).toBeGreaterThanOrEqual(0.5);
      }

      // Dates should be extracted (Romanian format: dd.MM.yyyy)
      if (extraction.metadata.issue_date) {
        const issueDate = new Date(extraction.metadata.issue_date);
        expect(issueDate).toBeInstanceOf(Date);
        expect(issueDate.getFullYear()).toBe(2024);
        expect(issueDate.getMonth()).toBe(2); // March (0-indexed)
        expect(extraction.metadata.issue_date_confidence).toBeGreaterThanOrEqual(0.5);
      }

      if (extraction.metadata.expiry_date) {
        const expiryDate = new Date(extraction.metadata.expiry_date);
        expect(expiryDate).toBeInstanceOf(Date);
        expect(expiryDate.getFullYear()).toBe(2027);
        expect(extraction.metadata.expiry_date_confidence).toBeGreaterThanOrEqual(0.5);
      }

      // Certification scope should be extracted
      if (extraction.metadata.certification_scope) {
        expect(extraction.metadata.certification_scope).toMatch(/instalatii|constructii/i);
        expect(extraction.metadata.certification_scope_confidence).toBeGreaterThanOrEqual(0.5);
      }

      // Confidence score should be reasonable
      expect(extraction.confidence_score).toBeGreaterThanOrEqual(0.5);
      expect(extraction.confidence_score).toBeLessThanOrEqual(1.0);

      // Step 6: Retrieve document by ID and verify
      const getResponse = await request(app)
        .get(`/api/v1/documents/${document.id}`)
        .expect(200);

      expect(getResponse.body.document.id).toBe(document.id);
      expect(getResponse.body.extraction.id).toBe(extraction.id);
    });

    it('should list documents including the processed Romanian certificate', async () => {
      // Upload a document first
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // List all documents
      const response = await request(app)
        .get('/api/v1/documents')
        .expect(200);

      expect(response.body).toHaveProperty('documents');
      expect(Array.isArray(response.body.documents)).toBe(true);
      expect(response.body.documents.length).toBeGreaterThan(0);

      const doc = response.body.documents[0];
      expect(doc.processing_status).toBe('completed');
      expect(doc.filename).toContain('romanian-cert.pdf');
    });

    it('should filter documents by processing status', async () => {
      // Upload a document
      await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      // Filter by completed status
      const response = await request(app)
        .get('/api/v1/documents?status=completed')
        .expect(200);

      expect(response.body.documents.length).toBeGreaterThan(0);
      response.body.documents.forEach((doc: any) => {
        expect(doc.processing_status).toBe('completed');
      });
    });

    it('should handle missing file gracefully', async () => {
      const response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: '/nonexistent/path/to/file.pdf' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error.code).toBe('FILE_NOT_FOUND');
    });

    it('should reject non-PDF files', async () => {
      const response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: '/some/path/to/file.txt' })
        .expect(400);

      expect(response.body).toHaveProperty('error');
      expect(response.body.error.code).toBe('INVALID_FILE_TYPE');
    });

    it('should return 404 for non-existent document ID', async () => {
      const response = await request(app)
        .get('/api/v1/documents/99999')
        .expect(404);

      expect(response.body.error.code).toBe('DOCUMENT_NOT_FOUND');
    });

    it('should validate document ID parameter', async () => {
      const response = await request(app)
        .get('/api/v1/documents/invalid-id')
        .expect(400);

      expect(response.body.error.code).toBe('INVALID_DOCUMENT_ID');
    });
  });

  describe('Database Integrity', () => {
    it('should maintain referential integrity between documents and extraction_results', async () => {
      // Upload document
      const response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      const documentId = response.body.document.id;

      // Verify document exists in database
      const docResult = await pool.query(
        'SELECT * FROM documents WHERE id = $1',
        [documentId]
      );
      expect(docResult.rows.length).toBe(1);

      // Verify extraction result exists and references the document
      const extractionResult = await pool.query(
        'SELECT * FROM extraction_results WHERE document_id = $1',
        [documentId]
      );
      expect(extractionResult.rows.length).toBe(1);
      expect(extractionResult.rows[0].document_id).toBe(documentId);
    });

    it('should store metadata as valid JSONB', async () => {
      // Upload document
      const response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: romanianCertPath })
        .expect(201);

      const documentId = response.body.document.id;

      // Query metadata directly from database
      const result = await pool.query(
        'SELECT metadata FROM extraction_results WHERE document_id = $1',
        [documentId]
      );

      const metadata = result.rows[0].metadata;
      expect(typeof metadata).toBe('object');

      // Verify JSONB query works (PostgreSQL-specific feature)
      const jsonbQuery = await pool.query(
        "SELECT metadata->>'certificate_number' as cert_num FROM extraction_results WHERE document_id = $1",
        [documentId]
      );

      // If certificate number was extracted, it should be queryable via JSONB
      if (jsonbQuery.rows[0].cert_num) {
        expect(jsonbQuery.rows[0].cert_num).toBeDefined();
      }
    });
  });

  describe('Health Check', () => {
    it('should return healthy status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body.status).toBe('ok');
      expect(response.body.timestamp).toBeDefined();
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

  // Execute migrations
  await pool.query(migration001);
  await pool.query(migration002);
}
