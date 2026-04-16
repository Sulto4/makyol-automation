import { Pool, QueryResult } from 'pg';
import { OwnerFilter } from './Document';

/**
 * Extraction status enum
 */
export enum ExtractionStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  PARTIAL = 'partial',
  FAILED = 'failed',
}

export interface CertificateMetadata {
  certificate_number?: string;
  issuing_organization?: string;
  issue_date?: string;
  expiry_date?: string;
  certified_company?: string;
  certification_scope?: string;
  [key: string]: any;
}

export interface ErrorDetails {
  message: string;
  code?: string;
  timestamp?: string;
  [key: string]: any;
}

export interface ExtractionResult {
  id: number;
  document_id: number;
  extracted_text: string | null;
  metadata: CertificateMetadata;
  confidence_score: number | null;
  extraction_status: ExtractionStatus;
  error_details: ErrorDetails | null;
  material: string | null;
  data_expirare: string | null;
  companie: string | null;
  producator: string | null;
  distribuitor: string | null;
  adresa_producator: string | null;
  extraction_model: string | null;
  owner_user_id: string | null;
  created_at: Date;
  updated_at: Date;
}

export interface CreateExtractionResultInput {
  document_id: number;
  extracted_text?: string | null;
  metadata?: CertificateMetadata;
  confidence_score?: number | null;
  extraction_status?: ExtractionStatus;
  error_details?: ErrorDetails | null;
  material?: string | null;
  data_expirare?: string | null;
  companie?: string | null;
  producator?: string | null;
  distribuitor?: string | null;
  adresa_producator?: string | null;
  extraction_model?: string | null;
  owner_user_id?: string | null;
}

export interface UpdateExtractionResultInput {
  extracted_text?: string | null;
  metadata?: CertificateMetadata;
  confidence_score?: number | null;
  extraction_status?: ExtractionStatus;
  error_details?: ErrorDetails | null;
  material?: string | null;
  data_expirare?: string | null;
  companie?: string | null;
  producator?: string | null;
  distribuitor?: string | null;
  adresa_producator?: string | null;
  extraction_model?: string | null;
}

export class ExtractionResultModel {
  private pool: Pool;

  constructor(pool: Pool) {
    this.pool = pool;
  }

  async create(input: CreateExtractionResultInput): Promise<ExtractionResult> {
    const query = `
      INSERT INTO extraction_results (
        document_id, extracted_text, metadata, confidence_score, extraction_status,
        error_details, material, data_expirare, companie, producator,
        distribuitor, adresa_producator, extraction_model, owner_user_id
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
      RETURNING *
    `;

    const values = [
      input.document_id,
      input.extracted_text || null,
      JSON.stringify(input.metadata || {}),
      input.confidence_score || null,
      input.extraction_status || ExtractionStatus.PENDING,
      input.error_details ? JSON.stringify(input.error_details) : null,
      input.material || null,
      input.data_expirare || null,
      input.companie || null,
      input.producator || null,
      input.distribuitor || null,
      input.adresa_producator || null,
      input.extraction_model || null,
      input.owner_user_id || null,
    ];

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows[0];
  }

  async findById(id: number, owner: OwnerFilter = null): Promise<ExtractionResult | null> {
    if (owner === null) {
      const r: QueryResult<ExtractionResult> = await this.pool.query(
        'SELECT * FROM extraction_results WHERE id = $1',
        [id],
      );
      return r.rows[0] || null;
    }
    const r: QueryResult<ExtractionResult> = await this.pool.query(
      'SELECT * FROM extraction_results WHERE id = $1 AND owner_user_id = $2',
      [id, owner],
    );
    return r.rows[0] || null;
  }

  async findByDocumentId(documentId: number, owner: OwnerFilter = null): Promise<ExtractionResult | null> {
    if (owner === null) {
      const r: QueryResult<ExtractionResult> = await this.pool.query(
        'SELECT * FROM extraction_results WHERE document_id = $1',
        [documentId],
      );
      return r.rows[0] || null;
    }
    const r: QueryResult<ExtractionResult> = await this.pool.query(
      'SELECT * FROM extraction_results WHERE document_id = $1 AND owner_user_id = $2',
      [documentId, owner],
    );
    return r.rows[0] || null;
  }

  async findAll(
    limit?: number,
    offset?: number,
    status?: ExtractionStatus,
    owner: OwnerFilter = null,
  ): Promise<ExtractionResult[]> {
    const clauses: string[] = [];
    const values: any[] = [];
    let i = 1;

    if (owner !== null) {
      clauses.push(`owner_user_id = $${i++}`);
      values.push(owner);
    }
    if (status) {
      clauses.push(`extraction_status = $${i++}`);
      values.push(status);
    }

    let query = 'SELECT * FROM extraction_results';
    if (clauses.length) query += ` WHERE ${clauses.join(' AND ')}`;
    query += ' ORDER BY created_at DESC';

    if (limit) {
      query += ` LIMIT $${i++}`;
      values.push(limit);
    }
    if (offset) {
      query += ` OFFSET $${i++}`;
      values.push(offset);
    }

    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows;
  }

  private buildUpdateSet(
    updateData: UpdateExtractionResultInput,
    startIndex: number,
  ): { setClauses: string[]; values: any[]; nextIndex: number } {
    const setClauses: string[] = [];
    const values: any[] = [];
    let i = startIndex;

    const push = (col: string, val: any) => {
      setClauses.push(`${col} = $${i++}`);
      values.push(val);
    };

    if (updateData.extracted_text !== undefined) push('extracted_text', updateData.extracted_text);
    if (updateData.metadata !== undefined) push('metadata', JSON.stringify(updateData.metadata));
    if (updateData.confidence_score !== undefined) push('confidence_score', updateData.confidence_score);
    if (updateData.extraction_status !== undefined) push('extraction_status', updateData.extraction_status);
    if (updateData.error_details !== undefined) {
      push('error_details', updateData.error_details ? JSON.stringify(updateData.error_details) : null);
    }
    if (updateData.material !== undefined) push('material', updateData.material);
    if (updateData.data_expirare !== undefined) push('data_expirare', updateData.data_expirare);
    if (updateData.companie !== undefined) push('companie', updateData.companie);
    if (updateData.producator !== undefined) push('producator', updateData.producator);
    if (updateData.distribuitor !== undefined) push('distribuitor', updateData.distribuitor);
    if (updateData.adresa_producator !== undefined) push('adresa_producator', updateData.adresa_producator);
    if (updateData.extraction_model !== undefined) push('extraction_model', updateData.extraction_model);

    return { setClauses, values, nextIndex: i };
  }

  async update(
    id: number,
    updateData: UpdateExtractionResultInput,
    owner: OwnerFilter = null,
  ): Promise<ExtractionResult | null> {
    const { setClauses, values, nextIndex } = this.buildUpdateSet(updateData, 1);
    if (setClauses.length === 0) return this.findById(id, owner);

    let i = nextIndex;
    let where = `WHERE id = $${i++}`;
    values.push(id);
    if (owner !== null) {
      where += ` AND owner_user_id = $${i++}`;
      values.push(owner);
    }
    const query = `UPDATE extraction_results SET ${setClauses.join(', ')} ${where} RETURNING *`;
    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  async updateByDocumentId(
    documentId: number,
    updateData: UpdateExtractionResultInput,
    owner: OwnerFilter = null,
  ): Promise<ExtractionResult | null> {
    const { setClauses, values, nextIndex } = this.buildUpdateSet(updateData, 1);
    if (setClauses.length === 0) return this.findByDocumentId(documentId, owner);

    let i = nextIndex;
    let where = `WHERE document_id = $${i++}`;
    values.push(documentId);
    if (owner !== null) {
      where += ` AND owner_user_id = $${i++}`;
      values.push(owner);
    }
    const query = `UPDATE extraction_results SET ${setClauses.join(', ')} ${where} RETURNING *`;
    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows[0] || null;
  }

  async delete(id: number, owner: OwnerFilter = null): Promise<boolean> {
    if (owner === null) {
      const r: QueryResult = await this.pool.query(
        'DELETE FROM extraction_results WHERE id = $1 RETURNING id',
        [id],
      );
      return (r.rowCount ?? 0) > 0;
    }
    const r: QueryResult = await this.pool.query(
      'DELETE FROM extraction_results WHERE id = $1 AND owner_user_id = $2 RETURNING id',
      [id, owner],
    );
    return (r.rowCount ?? 0) > 0;
  }

  async deleteByDocumentId(documentId: number, owner: OwnerFilter = null): Promise<boolean> {
    if (owner === null) {
      const r: QueryResult = await this.pool.query(
        'DELETE FROM extraction_results WHERE document_id = $1 RETURNING id',
        [documentId],
      );
      return (r.rowCount ?? 0) > 0;
    }
    const r: QueryResult = await this.pool.query(
      'DELETE FROM extraction_results WHERE document_id = $1 AND owner_user_id = $2 RETURNING id',
      [documentId, owner],
    );
    return (r.rowCount ?? 0) > 0;
  }

  async searchByMetadata(
    field: string,
    value: string,
    limit?: number,
    owner: OwnerFilter = null,
  ): Promise<ExtractionResult[]> {
    const values: any[] = [`%${value}%`];
    let where = `WHERE metadata->>'${field}' ILIKE $1`;
    let i = 2;
    if (owner !== null) {
      where += ` AND owner_user_id = $${i++}`;
      values.push(owner);
    }
    const query = `
      SELECT * FROM extraction_results
      ${where}
      ORDER BY created_at DESC
      ${limit ? `LIMIT ${limit}` : ''}
    `;
    const result: QueryResult<ExtractionResult> = await this.pool.query(query, values);
    return result.rows;
  }

  async findSuccessful(limit?: number, owner: OwnerFilter = null): Promise<ExtractionResult[]> {
    return this.findAll(limit, undefined, ExtractionStatus.SUCCESS, owner);
  }

  async findFailed(limit?: number, owner: OwnerFilter = null): Promise<ExtractionResult[]> {
    return this.findAll(limit, undefined, ExtractionStatus.FAILED, owner);
  }

  async countByStatus(status?: ExtractionStatus, owner: OwnerFilter = null): Promise<number> {
    const clauses: string[] = [];
    const values: any[] = [];
    let i = 1;
    if (owner !== null) {
      clauses.push(`owner_user_id = $${i++}`);
      values.push(owner);
    }
    if (status) {
      clauses.push(`extraction_status = $${i++}`);
      values.push(status);
    }
    let query = 'SELECT COUNT(*) as count FROM extraction_results';
    if (clauses.length) query += ` WHERE ${clauses.join(' AND ')}`;
    const result: QueryResult<{ count: string }> = await this.pool.query(query, values);
    return parseInt(result.rows[0].count, 10);
  }
}

export default ExtractionResultModel;
