import { Pool, QueryResult } from 'pg';

/**
 * Processing status enum for documents
 */
export enum ProcessingStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * Review status enum for document classification
 */
export enum ReviewStatus {
  OK = 'OK',
  REVIEW = 'REVIEW',
  NEEDS_CHECK = 'NEEDS_CHECK',
}

/**
 * Document interface matching the documents table schema
 */
export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  processing_status: ProcessingStatus;
  error_message: string | null;
  uploaded_at: Date;
  processing_started_at: Date | null;
  processing_completed_at: Date | null;
  categorie: string | null;
  confidence: number | null;
  metoda_clasificare: string | null;
  review_status: ReviewStatus | null;
  created_at: Date;
  updated_at: Date;
}

/**
 * Input type for creating a new document
 */
export interface CreateDocumentInput {
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type?: string;
  categorie?: string;
  confidence?: number;
  metoda_clasificare?: string;
  review_status?: ReviewStatus;
}

/**
 * Input type for updating document status
 */
export interface UpdateDocumentStatusInput {
  processing_status: ProcessingStatus;
  error_message?: string | null;
  processing_started_at?: Date;
  processing_completed_at?: Date;
  categorie?: string;
  confidence?: number;
  metoda_clasificare?: string;
  review_status?: ReviewStatus;
}

/**
 * Input type for updating document classification
 */
export interface UpdateClassificationInput {
  categorie: string;
  confidence: number;
  metoda_clasificare: string;
  review_status?: ReviewStatus;
}

/**
 * Document model class for database operations
 */
export class DocumentModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /**
   * Create a new document record
   */
  async create(input: CreateDocumentInput): Promise<Document> {
    const query = `
      INSERT INTO documents (
        filename,
        original_filename,
        file_path,
        file_size,
        mime_type
      ) VALUES ($1, $2, $3, $4, $5)
      RETURNING *
    `;

    const values = [
      input.filename,
      input.original_filename,
      input.file_path,
      input.file_size,
      input.mime_type || 'application/pdf',
    ];

    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0];
  }

  /**
   * Find a document by ID
   */
  async findById(id: number): Promise<Document | null> {
    const query = 'SELECT * FROM documents WHERE id = $1';
    const result: QueryResult<Document> = await this.pool.query(query, [id]);
    return result.rows[0] || null;
  }

  /**
   * Find all documents with optional filtering
   */
  async findAll(
    limit?: number,
    offset?: number,
    status?: ProcessingStatus
  ): Promise<Document[]> {
    let query = 'SELECT * FROM documents';
    const values: any[] = [];
    let paramIndex = 1;

    if (status) {
      query += ` WHERE processing_status = $${paramIndex}`;
      values.push(status);
      paramIndex++;
    }

    query += ' ORDER BY uploaded_at DESC';

    if (limit) {
      query += ` LIMIT $${paramIndex}`;
      values.push(limit);
      paramIndex++;
    }

    if (offset) {
      query += ` OFFSET $${paramIndex}`;
      values.push(offset);
    }

    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows;
  }

  /**
   * Update document processing status
   */
  async updateStatus(
    id: number,
    statusUpdate: UpdateDocumentStatusInput
  ): Promise<Document | null> {
    const setClauses: string[] = [];
    const values: any[] = [];
    let paramIndex = 1;

    setClauses.push(`processing_status = $${paramIndex}`);
    values.push(statusUpdate.processing_status);
    paramIndex++;

    if (statusUpdate.error_message !== undefined) {
      setClauses.push(`error_message = $${paramIndex}`);
      values.push(statusUpdate.error_message);
      paramIndex++;
    }

    if (statusUpdate.processing_started_at) {
      setClauses.push(`processing_started_at = $${paramIndex}`);
      values.push(statusUpdate.processing_started_at);
      paramIndex++;
    }

    if (statusUpdate.processing_completed_at) {
      setClauses.push(`processing_completed_at = $${paramIndex}`);
      values.push(statusUpdate.processing_completed_at);
      paramIndex++;
    }

    const query = `
      UPDATE documents
      SET ${setClauses.join(', ')}
      WHERE id = $${paramIndex}
      RETURNING *
    `;
    values.push(id);

    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  /**
   * Update document classification fields
   */
  async updateClassification(
    id: number,
    input: UpdateClassificationInput
  ): Promise<Document | null> {
    const query = `
      UPDATE documents
      SET categorie = $1,
          confidence = $2,
          metoda_clasificare = $3,
          review_status = $4
      WHERE id = $5
      RETURNING *
    `;

    const values = [
      input.categorie,
      input.confidence,
      input.metoda_clasificare,
      input.review_status || ReviewStatus.OK,
      id,
    ];

    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  /**
   * Delete a document by ID
   */
  async delete(id: number): Promise<boolean> {
    const query = 'DELETE FROM documents WHERE id = $1 RETURNING id';
    const result: QueryResult = await this.pool.query(query, [id]);
    return result.rowCount !== null && result.rowCount > 0;
  }

  /**
   * Count documents by status
   */
  async countByStatus(status?: ProcessingStatus): Promise<number> {
    let query = 'SELECT COUNT(*) as count FROM documents';
    const values: any[] = [];

    if (status) {
      query += ' WHERE processing_status = $1';
      values.push(status);
    }

    const result: QueryResult<{ count: string }> = await this.pool.query(query, values);
    return parseInt(result.rows[0].count, 10);
  }

  /**
   * Find documents pending processing
   */
  async findPending(limit?: number): Promise<Document[]> {
    return this.findAll(limit, undefined, ProcessingStatus.PENDING);
  }
}

export default DocumentModel;
