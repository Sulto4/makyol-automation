import { Pool, QueryResult } from 'pg';

/**
 * Extraction status enum
 */
export enum ExtractionStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  PARTIAL = 'partial',
  FAILED = 'failed',
}

/**
 * Certificate metadata interface
 */
export interface CertificateMetadata {
  certificate_number?: string;
  issuing_organization?: string;
  issue_date?: string;
  expiry_date?: string;
  certified_company?: string;
  certification_scope?: string;
  [key: string]: any; // Allow additional fields
}

/**
 * Error details interface
 */
export interface ErrorDetails {
  message: string;
  code?: string;
  timestamp?: string;
  [key: string]: any; // Allow additional error fields
}

/**
 * ExtractionResult interface matching the extraction_results table schema
 */
export interface ExtractionResult {
  id: number;
  document_id: number;
  extracted_text: string | null;
  metadata: CertificateMetadata;
  confidence_score: number | null;
  extraction_status: ExtractionStatus;
  error_details: ErrorDetails | null;
  created_at: Date;
  updated_at: Date;
}

/**
 * Input type for creating a new extraction result
 */
export interface CreateExtractionResultInput {
  document_id: number;
  extracted_text?: string | null;
  metadata?: CertificateMetadata;
  confidence_score?: number | null;
  extraction_status?: ExtractionStatus;
  error_details?: ErrorDetails | null;
}

/**
 * Input type for updating an extraction result
 */
export interface UpdateExtractionResultInput {
  extracted_text?: string | null;
  metadata?: CertificateMetadata;
  confidence_score?: number | null;
  extraction_status?: ExtractionStatus;
  error_details?: ErrorDetails | null;
}

/**
 * ExtractionResult model class for database operations
 */
export class ExtractionResultModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Create a new extraction result record
   */
  async create(input: CreateExtractionResultInput): Promise<ExtractionResult> {
    const query = `
      INSERT INTO extraction_results (
        document_id,
        extracted_text,
        metadata,
        confidence_score,
        extraction_status,
        error_details
      ) VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;

    const values = [
      input.document_id,
      input.extracted_text || null,
      JSON.stringify(input.metadata || {}),
      input.confidence_score || null,
      input.extraction_status || ExtractionStatus.PENDING,
      input.error_details ? JSON.stringify(input.error_details) : null,
    ];

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows[0];
  }

  /**
   * Find an extraction result by ID
   */
  async findById(id: number): Promise<ExtractionResult | null> {
    const query = 'SELECT * FROM extraction_results WHERE id = $1';
    const result: QueryResult<ExtractionResult> = await this.pool.query(query, [id]);
    return result.rows[0] || null;
  }

  /**
   * Find an extraction result by document ID
   */
  async findByDocumentId(documentId: number): Promise<ExtractionResult | null> {
    const query = 'SELECT * FROM extraction_results WHERE document_id = $1';
    const result: QueryResult<ExtractionResult> = await this.pool.query(query, [documentId]);
    return result.rows[0] || null;
  }

  /**
   * Find all extraction results with optional filtering
   */
  async findAll(
    limit?: number,
    offset?: number,
    status?: ExtractionStatus
  ): Promise<ExtractionResult[]> {
    let query = 'SELECT * FROM extraction_results';
    const values: any[] = [];
    let paramIndex = 1;

    if (status) {
      query += ` WHERE extraction_status = $${paramIndex}`;
      values.push(status);
      paramIndex++;
    }

    query += ' ORDER BY created_at DESC';

    if (limit) {
      query += ` LIMIT $${paramIndex}`;
      values.push(limit);
      paramIndex++;
    }

    if (offset) {
      query += ` OFFSET $${paramIndex}`;
      values.push(offset);
    }

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows;
  }

  /**
   * Update an extraction result
   */
  async update(
    id: number,
    updateData: UpdateExtractionResultInput
  ): Promise<ExtractionResult | null> {
    const setClauses: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;

    if (updateData.extracted_text !== undefined) {
      setClauses.push(`extracted_text = $${paramIndex}`);
      values.push(updateData.extracted_text);
      paramIndex++;
    }

    if (updateData.metadata !== undefined) {
      setClauses.push(`metadata = $${paramIndex}`);
      values.push(JSON.stringify(updateData.metadata));
      paramIndex++;
    }

    if (updateData.confidence_score !== undefined) {
      setClauses.push(`confidence_score = $${paramIndex}`);
      values.push(updateData.confidence_score);
      paramIndex++;
    }

    if (updateData.extraction_status !== undefined) {
      setClauses.push(`extraction_status = $${paramIndex}`);
      values.push(updateData.extraction_status);
      paramIndex++;
    }

    if (updateData.error_details !== undefined) {
      setClauses.push(`error_details = $${paramIndex}`);
      values.push(updateData.error_details ? JSON.stringify(updateData.error_details) : null);
      paramIndex++;
    }

    if (setClauses.length === 0) {
      // No fields to update
      return this.findById(id);
    }

    const query = `
      UPDATE extraction_results
      SET ${setClauses.join(', ')}
      WHERE id = $${paramIndex}
      RETURNING *
    `;
    values.push(id);

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  /**
   * Update extraction result by document ID
   */
  async updateByDocumentId(
    documentId: number,
    updateData: UpdateExtractionResultInput
  ): Promise<ExtractionResult | null> {
    const setClauses: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;

    if (updateData.extracted_text !== undefined) {
      setClauses.push(`extracted_text = $${paramIndex}`);
      values.push(updateData.extracted_text);
      paramIndex++;
    }

    if (updateData.metadata !== undefined) {
      setClauses.push(`metadata = $${paramIndex}`);
      values.push(JSON.stringify(updateData.metadata));
      paramIndex++;
    }

    if (updateData.confidence_score !== undefined) {
      setClauses.push(`confidence_score = $${paramIndex}`);
      values.push(updateData.confidence_score);
      paramIndex++;
    }

    if (updateData.extraction_status !== undefined) {
      setClauses.push(`extraction_status = $${paramIndex}`);
      values.push(updateData.extraction_status);
      paramIndex++;
    }

    if (updateData.error_details !== undefined) {
      setClauses.push(`error_details = $${paramIndex}`);
      values.push(updateData.error_details ? JSON.stringify(updateData.error_details) : null);
      paramIndex++;
    }

    if (setClauses.length === 0) {
      // No fields to update
      return this.findByDocumentId(documentId);
    }

    const query = `
      UPDATE extraction_results
      SET ${setClauses.join(', ')}
      WHERE document_id = $${paramIndex}
      RETURNING *
    `;
    values.push(documentId);

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  /**
   * Delete an extraction result by ID
   */
  async delete(id: number): Promise<boolean> {
    const query = 'DELETE FROM extraction_results WHERE id = $1 RETURNING id';
    const result: QueryResult = await this.pool.query(query, [id]);
    return result.rowCount !== null && result.rowCount > 0;
  }

  /**
   * Delete an extraction result by document ID
   */
  async deleteByDocumentId(documentId: number): Promise<boolean> {
    const query = 'DELETE FROM extraction_results WHERE document_id = $1 RETURNING id';
    const result: QueryResult = await this.pool.query(query, [documentId]);
    return result.rowCount !== null && result.rowCount > 0;
  }

  /**
   * Search extraction results by metadata field
   */
  async searchByMetadata(
    field: string,
    value: string,
    limit?: number
  ): Promise<ExtractionResult[]> {
    const query = `
      SELECT * FROM extraction_results
      WHERE metadata->>'${field}' ILIKE $1
      ORDER BY created_at DESC
      ${limit ? `LIMIT ${limit}` : ''}
    `;

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, [`%${value}%`]);
    return result.rows;
  }

  /**
   * Get extraction results with successful status
   */
  async findSuccessful(limit?: number): Promise<ExtractionResult[]> {
    return this.findAll(limit, undefined, ExtractionStatus.SUCCESS);
  }

  /**
   * Get extraction results with failed status
   */
  async findFailed(limit?: number): Promise<ExtractionResult[]> {
    return this.findAll(limit, undefined, ExtractionStatus.FAILED);
  }

  /**
   * Count extraction results by status
   */
  async countByStatus(status?: ExtractionStatus): Promise<number> {
    let query = 'SELECT COUNT(*) as count FROM extraction_results';
    const values: any[] = [];

    if (status) {
      query += ' WHERE extraction_status = $1';
      values.push(status);
    }

    const result: QueryResult<{ count: string }> = await this.pool.query(query, values);
    return parseInt(result.rows[0].count, 10);
  }
}

export default ExtractionResultModel;
