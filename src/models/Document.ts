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
  relative_path: string | null;
  owner_user_id: string | null;
  page_count: number | null;
  created_at: Date;
  updated_at: Date;
  data_expirare?: string | null;
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
  relative_path?: string;
  owner_user_id?: string | null;
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
  page_count?: number | null;
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
 * Owner filter type.
 * - `string`: scope queries to that user_id (regular users).
 * - `null`: no scoping — admin / system / tests. Caller accepts responsibility for read/write access.
 */
export type OwnerFilter = string | null;

/**
 * Document model class for database operations.
 *
 * All read/write methods accept an `OwnerFilter` that scopes the SQL to a
 * single user when a UUID is provided. Pass `null` only from admin paths
 * or internal tasks — controllers should derive it via `req.user`.
 */
export class DocumentModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  /** Create a new document record. owner_user_id defaults to NULL for legacy callers. */
  async create(input: CreateDocumentInput): Promise<Document> {
    const query = `
      INSERT INTO documents (
        filename,
        original_filename,
        file_path,
        file_size,
        mime_type,
        relative_path,
        owner_user_id
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      RETURNING *
    `;

    const values = [
      input.filename,
      input.original_filename,
      input.file_path,
      input.file_size,
      input.mime_type || 'application/pdf',
      input.relative_path || null,
      input.owner_user_id || null,
    ];

    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0];
  }

  async findById(id: number, owner: OwnerFilter = null): Promise<Document | null> {
    if (owner === null) {
      const r: QueryResult<Document> = await this.pool.query(
        'SELECT * FROM documents WHERE id = $1',
        [id],
      );
      return r.rows[0] || null;
    }
    const r: QueryResult<Document> = await this.pool.query(
      'SELECT * FROM documents WHERE id = $1 AND owner_user_id = $2',
      [id, owner],
    );
    return r.rows[0] || null;
  }

  async findAll(
    limit?: number,
    offset?: number,
    status?: ProcessingStatus,
    owner: OwnerFilter = null,
  ): Promise<Document[]> {
    const clauses: string[] = [];
    const values: any[] = [];
    let i = 1;

    if (owner !== null) {
      clauses.push(`owner_user_id = $${i++}`);
      values.push(owner);
    }
    if (status) {
      clauses.push(`processing_status = $${i++}`);
      values.push(status);
    }

    let query =
      'SELECT documents.*, er.data_expirare ' +
      'FROM documents ' +
      'LEFT JOIN extraction_results er ON er.document_id = documents.id';
    if (clauses.length) {
      const scoped = clauses.map((c) => c.replace(/^(owner_user_id|processing_status)/, 'documents.$1'));
      query += ` WHERE ${scoped.join(' AND ')}`;
    }
    query += ' ORDER BY documents.uploaded_at DESC';

    if (limit) {
      query += ` LIMIT $${i++}`;
      values.push(limit);
    }
    if (offset) {
      query += ` OFFSET $${i++}`;
      values.push(offset);
    }

    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows;
  }

  async updateStatus(
    id: number,
    statusUpdate: UpdateDocumentStatusInput,
    owner: OwnerFilter = null,
  ): Promise<Document | null> {
    const setClauses: string[] = [];
    const values: any[] = [];
    let i = 1;

    setClauses.push(`processing_status = $${i++}`);
    values.push(statusUpdate.processing_status);

    if (statusUpdate.error_message !== undefined) {
      setClauses.push(`error_message = $${i++}`);
      values.push(statusUpdate.error_message);
    }
    if (statusUpdate.processing_started_at) {
      setClauses.push(`processing_started_at = $${i++}`);
      values.push(statusUpdate.processing_started_at);
    }
    if (statusUpdate.processing_completed_at) {
      setClauses.push(`processing_completed_at = $${i++}`);
      values.push(statusUpdate.processing_completed_at);
    }
    if (statusUpdate.page_count !== undefined) {
      setClauses.push(`page_count = $${i++}`);
      values.push(statusUpdate.page_count);
    }

    let where = `WHERE id = $${i++}`;
    values.push(id);
    if (owner !== null) {
      where += ` AND owner_user_id = $${i++}`;
      values.push(owner);
    }

    const query = `UPDATE documents SET ${setClauses.join(', ')} ${where} RETURNING *`;
    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  async updateClassification(
    id: number,
    input: UpdateClassificationInput,
    owner: OwnerFilter = null,
  ): Promise<Document | null> {
    const values: any[] = [
      input.categorie,
      input.confidence,
      input.metoda_clasificare,
      input.review_status || ReviewStatus.OK,
      id,
    ];
    let where = 'WHERE id = $5';
    if (owner !== null) {
      where += ' AND owner_user_id = $6';
      values.push(owner);
    }
    const query = `
      UPDATE documents
      SET categorie = $1, confidence = $2, metoda_clasificare = $3, review_status = $4
      ${where}
      RETURNING *
    `;
    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  async updateReviewStatus(
    id: number,
    reviewStatus: ReviewStatus,
    owner: OwnerFilter = null,
  ): Promise<Document | null> {
    const values: any[] = [reviewStatus, id];
    let where = 'WHERE id = $2';
    if (owner !== null) {
      where += ' AND owner_user_id = $3';
      values.push(owner);
    }
    const query = `UPDATE documents SET review_status = $1 ${where} RETURNING *`;
    const result: QueryResult<Document> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  async deleteAll(owner: OwnerFilter = null): Promise<number> {
    if (owner === null) {
      const r: QueryResult = await this.pool.query('DELETE FROM documents RETURNING id');
      return r.rowCount ?? 0;
    }
    const r: QueryResult = await this.pool.query(
      'DELETE FROM documents WHERE owner_user_id = $1 RETURNING id',
      [owner],
    );
    return r.rowCount ?? 0;
  }

  async delete(id: number, owner: OwnerFilter = null): Promise<boolean> {
    if (owner === null) {
      const r: QueryResult = await this.pool.query(
        'DELETE FROM documents WHERE id = $1 RETURNING id',
        [id],
      );
      return (r.rowCount ?? 0) > 0;
    }
    const r: QueryResult = await this.pool.query(
      'DELETE FROM documents WHERE id = $1 AND owner_user_id = $2 RETURNING id',
      [id, owner],
    );
    return (r.rowCount ?? 0) > 0;
  }

  async countByStatus(status?: ProcessingStatus, owner: OwnerFilter = null): Promise<number> {
    const clauses: string[] = [];
    const values: any[] = [];
    let i = 1;
    if (owner !== null) {
      clauses.push(`owner_user_id = $${i++}`);
      values.push(owner);
    }
    if (status) {
      clauses.push(`processing_status = $${i++}`);
      values.push(status);
    }
    let query = 'SELECT COUNT(*) as count FROM documents';
    if (clauses.length) query += ` WHERE ${clauses.join(' AND ')}`;

    const result: QueryResult<{ count: string }> = await this.pool.query(query, values);
    return parseInt(result.rows[0].count, 10);
  }

  async findPending(limit?: number, owner: OwnerFilter = null): Promise<Document[]> {
    return this.findAll(limit, undefined, ProcessingStatus.PENDING, owner);
  }
}

export default DocumentModel;
