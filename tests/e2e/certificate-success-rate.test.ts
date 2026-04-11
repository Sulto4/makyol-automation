import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { Express } from 'express';
import request from 'supertest';
import { createApp } from '../../src/index';
import { databaseConfig } from '../../src/config/database';

/**
 * E2E Test: Verify 80%+ Success Rate on Romanian Certificate Samples
 *
 * This test validates that the PDF extraction pipeline achieves at least 80%
 * success rate for extracting key metadata from Romanian certificates:
 * - Certificate numbers
 * - Issuing organizations
 * - Issue dates and expiry dates
 * - Company names
 * - Certification scope
 */
describe('E2E: Certificate Success Rate Verification', () => {
  let pool: Pool;
  let app: Express;

  // Define all test certificates with their expected metadata
  const certificates = [
    {
      name: 'romanian-cert.pdf',
      path: path.join(__dirname, '../fixtures/romanian-cert.pdf'),
      expected: {
        certificateNumber: 'ISO-RO-2024-12345',
        issuingOrg: 'SRAC',
        company: 'MAKYOL CONSTRUCT',
        issueDate: { year: 2024, month: 3, day: 15 }, // 15.03.2024
        expiryDate: { year: 2027, month: 3, day: 15 }, // 15.03.2027
        scope: 'instalatii',
      },
    },
    {
      name: 'cert-sample-1.pdf',
      path: path.join(__dirname, '../fixtures/cert-sample-1.pdf'),
      expected: {
        certificateNumber: 'ENV-RO-2023-78901',
        issuingOrg: 'SRAC',
        company: 'CONSTRUCȚII PREMIUM',
        issueDate: { year: 2023, month: 6, day: 20 }, // 20/06/2023
        expiryDate: { year: 2026, month: 6, day: 20 }, // 20/06/2026
        scope: 'construcții',
      },
    },
    {
      name: 'cert-sample-2.pdf',
      path: path.join(__dirname, '../fixtures/cert-sample-2.pdf'),
      expected: {
        certificateNumber: 'OHSAS-2024-56789',
        issuingOrg: 'ACAR',
        company: 'MAKYOL INFRASTRUCTURE',
        issueDate: { year: 2024, month: 1, day: 10 }, // 10.01.2024
        expiryDate: { year: 2027, month: 1, day: 10 }, // 10.01.2027
        scope: 'infrastructură',
      },
    },
    {
      name: 'cert-sample-3.pdf',
      path: path.join(__dirname, '../fixtures/cert-sample-3.pdf'),
      expected: {
        certificateNumber: 'QMS-RO-2025-11223',
        issuingOrg: 'RENAR',
        company: 'INSTALAȚII MODERNE',
        issueDate: { year: 2025, month: 11, day: 5 }, // 05.11.2025
        expiryDate: { year: 2028, month: 11, day: 5 }, // 05.11.2028
        scope: 'instalații',
      },
    },
    {
      name: 'cert-sample-4.pdf',
      path: path.join(__dirname, '../fixtures/cert-sample-4.pdf'),
      expected: {
        certificateNumber: 'ISMS-2024-99887',
        issuingOrg: 'ARS',
        company: 'MAKYOL DIGITAL SERVICES',
        issueDate: { year: 2024, month: 8, day: 30 }, // 30-08-2024
        expiryDate: { year: 2027, month: 8, day: 30 }, // 30-08-2027
        scope: 'software',
      },
    },
  ];

  beforeAll(async () => {
    // Create database pool for testing
    const testDbConfig = {
      ...databaseConfig,
      database: process.env.TEST_DB_NAME || databaseConfig.database,
    };

    pool = new Pool(testDbConfig);

    // Wait for database connection
    const client = await pool.connect();
    client.release();

    // Run migrations
    await runMigrations(pool);

    // Create Express app
    app = createApp(pool);
  });

  afterAll(async () => {
    // Clean up
    await pool.query('DELETE FROM extraction_results');
    await pool.query('DELETE FROM documents');
    await pool.end();
  });

  beforeEach(async () => {
    // Clean up before each test
    await pool.query('DELETE FROM extraction_results');
    await pool.query('DELETE FROM documents');
  });

  describe('80%+ Success Rate Verification', () => {
    it('should achieve 80%+ success rate for certificate number extraction', async () => {
      const results = await processCertificates();
      const successRate = calculateSuccessRate(results, 'certificate_number');

      console.log(`\n📊 Certificate Number Extraction Success Rate: ${(successRate * 100).toFixed(1)}%`);
      console.log(`   ✓ Successful: ${results.filter(r => r.extractedCertificateNumber).length}/${results.length}`);

      expect(successRate).toBeGreaterThanOrEqual(0.8);
    });

    it('should achieve 80%+ success rate for issuing organization extraction', async () => {
      const results = await processCertificates();
      const successRate = calculateSuccessRate(results, 'issuing_organization');

      console.log(`\n📊 Issuing Organization Extraction Success Rate: ${(successRate * 100).toFixed(1)}%`);
      console.log(`   ✓ Successful: ${results.filter(r => r.extractedIssuingOrg).length}/${results.length}`);

      expect(successRate).toBeGreaterThanOrEqual(0.8);
    });

    it('should achieve 80%+ success rate for issue date extraction', async () => {
      const results = await processCertificates();
      const successRate = calculateSuccessRate(results, 'issue_date');

      console.log(`\n📊 Issue Date Extraction Success Rate: ${(successRate * 100).toFixed(1)}%`);
      console.log(`   ✓ Successful: ${results.filter(r => r.extractedIssueDate).length}/${results.length}`);

      expect(successRate).toBeGreaterThanOrEqual(0.8);
    });

    it('should achieve 80%+ success rate for expiry date extraction', async () => {
      const results = await processCertificates();
      const successRate = calculateSuccessRate(results, 'expiry_date');

      console.log(`\n📊 Expiry Date Extraction Success Rate: ${(successRate * 100).toFixed(1)}%`);
      console.log(`   ✓ Successful: ${results.filter(r => r.extractedExpiryDate).length}/${results.length}`);

      expect(successRate).toBeGreaterThanOrEqual(0.8);
    });

    it('should achieve 80%+ success rate for company name extraction', async () => {
      const results = await processCertificates();
      const successRate = calculateSuccessRate(results, 'certified_company');

      console.log(`\n📊 Company Name Extraction Success Rate: ${(successRate * 100).toFixed(1)}%`);
      console.log(`   ✓ Successful: ${results.filter(r => r.extractedCompany).length}/${results.length}`);

      expect(successRate).toBeGreaterThanOrEqual(0.8);
    });

    it('should achieve 80%+ success rate for certification scope extraction', async () => {
      const results = await processCertificates();
      const successRate = calculateSuccessRate(results, 'certification_scope');

      console.log(`\n📊 Certification Scope Extraction Success Rate: ${(successRate * 100).toFixed(1)}%`);
      console.log(`   ✓ Successful: ${results.filter(r => r.extractedScope).length}/${results.length}`);

      expect(successRate).toBeGreaterThanOrEqual(0.8);
    });

    it('should generate detailed report of extraction results', async () => {
      const results = await processCertificates();

      console.log('\n' + '='.repeat(80));
      console.log('📋 DETAILED EXTRACTION RESULTS REPORT');
      console.log('='.repeat(80) + '\n');

      results.forEach((result, index) => {
        const cert = certificates[index];
        console.log(`\n📄 Certificate ${index + 1}: ${cert.name}`);
        console.log('─'.repeat(80));

        console.log(`   Certificate Number:`);
        console.log(`     Expected: ${cert.expected.certificateNumber}`);
        console.log(`     Extracted: ${result.extractedCertificateNumber || 'NOT FOUND'}`);
        console.log(`     Status: ${result.extractedCertificateNumber ? '✓ SUCCESS' : '✗ FAILED'}`);

        console.log(`   Issuing Organization:`);
        console.log(`     Expected: ${cert.expected.issuingOrg}`);
        console.log(`     Extracted: ${result.extractedIssuingOrg || 'NOT FOUND'}`);
        console.log(`     Status: ${result.extractedIssuingOrg ? '✓ SUCCESS' : '✗ FAILED'}`);

        console.log(`   Company Name:`);
        console.log(`     Expected: ${cert.expected.company}`);
        console.log(`     Extracted: ${result.extractedCompany || 'NOT FOUND'}`);
        console.log(`     Status: ${result.extractedCompany ? '✓ SUCCESS' : '✗ FAILED'}`);

        console.log(`   Issue Date:`);
        console.log(`     Expected: ${formatDate(cert.expected.issueDate)}`);
        console.log(`     Extracted: ${result.extractedIssueDate || 'NOT FOUND'}`);
        console.log(`     Status: ${result.extractedIssueDate ? '✓ SUCCESS' : '✗ FAILED'}`);

        console.log(`   Expiry Date:`);
        console.log(`     Expected: ${formatDate(cert.expected.expiryDate)}`);
        console.log(`     Extracted: ${result.extractedExpiryDate || 'NOT FOUND'}`);
        console.log(`     Status: ${result.extractedExpiryDate ? '✓ SUCCESS' : '✗ FAILED'}`);

        console.log(`   Certification Scope:`);
        console.log(`     Expected (contains): ${cert.expected.scope}`);
        console.log(`     Extracted: ${result.extractedScope || 'NOT FOUND'}`);
        console.log(`     Status: ${result.extractedScope ? '✓ SUCCESS' : '✗ FAILED'}`);

        console.log(`   Overall Confidence: ${(result.confidenceScore * 100).toFixed(1)}%`);

        if (result.errorDetails) {
          console.log(`   ⚠️  Error Details: ${JSON.stringify(result.errorDetails)}`);
        }
      });

      console.log('\n' + '='.repeat(80));
      console.log('📊 OVERALL SUCCESS RATES');
      console.log('='.repeat(80) + '\n');

      const rates = {
        'Certificate Number': calculateSuccessRate(results, 'certificate_number'),
        'Issuing Organization': calculateSuccessRate(results, 'issuing_organization'),
        'Issue Date': calculateSuccessRate(results, 'issue_date'),
        'Expiry Date': calculateSuccessRate(results, 'expiry_date'),
        'Company Name': calculateSuccessRate(results, 'certified_company'),
        'Certification Scope': calculateSuccessRate(results, 'certification_scope'),
      };

      Object.entries(rates).forEach(([field, rate]) => {
        const percentage = (rate * 100).toFixed(1);
        const status = rate >= 0.8 ? '✓' : '✗';
        console.log(`   ${status} ${field}: ${percentage}% (${rate >= 0.8 ? 'PASS' : 'FAIL'})`);
      });

      const averageRate = Object.values(rates).reduce((a, b) => a + b, 0) / Object.values(rates).length;
      console.log(`\n   📈 Average Success Rate: ${(averageRate * 100).toFixed(1)}%`);
      console.log(`   🎯 Target: 80.0%`);
      console.log(`   ${averageRate >= 0.8 ? '✅ OVERALL: PASS' : '❌ OVERALL: FAIL'}`);

      console.log('\n' + '='.repeat(80) + '\n');

      // Expect average success rate to be >= 80%
      expect(averageRate).toBeGreaterThanOrEqual(0.8);
    });
  });

  /**
   * Process all certificates and collect extraction results
   */
  async function processCertificates() {
    const results = [];

    for (const cert of certificates) {
      // Verify file exists
      const fileExists = await fs.access(cert.path).then(() => true).catch(() => false);
      expect(fileExists).toBe(true);

      // Upload and process document
      const response = await request(app)
        .post('/api/v1/documents')
        .send({ file_path: cert.path })
        .expect(201);

      const { document, extraction } = response.body;

      // Verify basic processing succeeded
      expect(document.processing_status).toBe('completed');
      expect(extraction.extraction_status).toMatch(/^(success|partial)$/);

      // Collect extraction results
      results.push({
        name: cert.name,
        documentId: document.id,
        extractedText: extraction.extracted_text,
        metadata: extraction.metadata || {},
        confidenceScore: extraction.confidence_score || 0,
        errorDetails: extraction.error_details,

        // Check if each field was successfully extracted
        extractedCertificateNumber: extraction.metadata?.certificate_number || null,
        extractedIssuingOrg: extraction.metadata?.issuing_organization || null,
        extractedCompany: extraction.metadata?.certified_company || null,
        extractedIssueDate: extraction.metadata?.issue_date || null,
        extractedExpiryDate: extraction.metadata?.expiry_date || null,
        extractedScope: extraction.metadata?.certification_scope || null,
      });
    }

    return results;
  }

  /**
   * Calculate success rate for a specific metadata field
   */
  function calculateSuccessRate(results: any[], field: string): number {
    const total = results.length;
    const successful = results.filter((r) => {
      const fieldMap: { [key: string]: string } = {
        certificate_number: 'extractedCertificateNumber',
        issuing_organization: 'extractedIssuingOrg',
        certified_company: 'extractedCompany',
        issue_date: 'extractedIssueDate',
        expiry_date: 'extractedExpiryDate',
        certification_scope: 'extractedScope',
      };

      const extractedField = fieldMap[field];
      return r[extractedField] !== null && r[extractedField] !== undefined;
    }).length;

    return successful / total;
  }

  /**
   * Format date object for display
   */
  function formatDate(dateObj: { year: number; month: number; day: number }): string {
    return `${dateObj.day.toString().padStart(2, '0')}.${dateObj.month.toString().padStart(2, '0')}.${dateObj.year}`;
  }
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
