import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { DocumentModel, Document, ProcessingStatus, ReviewStatus, CreateDocumentInput, OwnerFilter } from '../models/Document';
import { ExtractionResultModel, ExtractionStatus, CreateExtractionResultInput } from '../models/ExtractionResult';
import { PipelineClientService, PipelineError } from '../services/pipelineClient';
import { AuditService } from '../services/auditService';
import { ArchiveService, ArchiveDocumentRecord } from '../services/archiveService';
import { SettingsService } from '../services/settingsService';
import { SettingKey } from '../models/settings';
import { logger } from '../utils/logger';
import { createLimiter } from '../utils/concurrency';

// Fallback used when the DB is unreachable at batch start. 3 matches the
// seeded default in settingsService.DEFAULT_SETTINGS. Validated up to 8
// concurrent during benchmark with no OpenRouter throttling.
const DEFAULT_BATCH_CONCURRENCY = 3;
// Clamp to the same range the settings validator allows so a corrupt DB
// value cannot blow out concurrency or drop it below 1.
const BATCH_CONCURRENCY_MIN = 1;
const BATCH_CONCURRENCY_MAX = 10;

/**
 * Return the owner filter for the current request:
 * - `null` for admins (see everything)
 * - `req.user.id` for regular users (scoped to their own rows)
 */
function ownerOf(req: Request): OwnerFilter {
  if (!req.user) return null;
  return req.user.is_admin ? null : req.user.id;
}

function userIdOf(req: Request): string | null {
  return req.user?.id ?? null;
}

export class DocumentController {
  protected pool: Pool;
  private documentModel: DocumentModel;
  private extractionResultModel: ExtractionResultModel;
  private pipelineClient: PipelineClientService;
  private auditService: AuditService;
  private settingsService: SettingsService;

  constructor(pool: Pool) {
    this.pool = pool;
    this.documentModel = new DocumentModel(pool);
    this.extractionResultModel = new ExtractionResultModel(pool);
    this.pipelineClient = new PipelineClientService();
    this.auditService = new AuditService(pool);
    this.settingsService = new SettingsService(pool);
  }

  /**
   * Read the current batch concurrency from settings. Invoked at the
   * start of each batch operation so the admin's UI-side changes take
   * effect on the next run without a server restart. Clamped to the
   * [BATCH_CONCURRENCY_MIN, BATCH_CONCURRENCY_MAX] range so a stale or
   * corrupt DB value can't produce a pathological value.
   */
  private async resolveBatchConcurrency(): Promise<number> {
    try {
      const raw = await this.settingsService.getSettingValue<number>(
        SettingKey.BATCH_CONCURRENCY,
        DEFAULT_BATCH_CONCURRENCY,
      );
      const parsed = typeof raw === 'number' ? raw : Number(raw);
      if (!Number.isFinite(parsed)) return DEFAULT_BATCH_CONCURRENCY;
      const clamped = Math.max(
        BATCH_CONCURRENCY_MIN,
        Math.min(BATCH_CONCURRENCY_MAX, Math.floor(parsed)),
      );
      return clamped;
    } catch (err: any) {
      logger.warn(
        `Failed to read batch_concurrency setting, falling back to ${DEFAULT_BATCH_CONCURRENCY}: ${err?.message ?? err}`,
      );
      return DEFAULT_BATCH_CONCURRENCY;
    }
  }

  /**
   * Reprocess a single document through the pipeline.
   * `owner` scopes updates; `actorUserId` is recorded in audit logs.
   * Pass `null` for internal/admin paths.
   */
  protected async reprocessSingleDocument(
    document: Document,
    owner: OwnerFilter,
    actorUserId: string | null,
  ): Promise<void> {
    const pipelineResponse = await this.pipelineClient.processDocument(document.file_path, document.original_filename);
    logger.info(`Pipeline reprocessed document ${document.id}: type=${pipelineResponse.classification}, confidence=${pipelineResponse.confidence}`);

    if (pipelineResponse.error) {
      throw new Error(pipelineResponse.error);
    }

    if (pipelineResponse.classification) {
      await this.documentModel.updateClassification(document.id, {
        categorie: pipelineResponse.classification,
        confidence: pipelineResponse.confidence ?? 0,
        metoda_clasificare: pipelineResponse.method ?? 'ai',
      }, owner);
      logger.info(`Classification saved for document ${document.id}: ${pipelineResponse.classification}`);
    }

    const extraction = pipelineResponse.extraction || {};
    const extractionStatus = pipelineResponse.confidence >= 0.8
      ? ExtractionStatus.SUCCESS
      : pipelineResponse.confidence >= 0.5
        ? ExtractionStatus.PARTIAL
        : ExtractionStatus.FAILED;

    const extractionInput: CreateExtractionResultInput = {
      document_id: document.id,
      extracted_text: null,
      metadata: {},
      confidence_score: pipelineResponse.confidence ?? null,
      extraction_status: extractionStatus,
      material: extraction.material ?? null,
      data_expirare: extraction.data_expirare ?? null,
      companie: extraction.companie ?? null,
      producator: extraction.producator ?? null,
      distribuitor: extraction.distribuitor ?? null,
      adresa_producator: extraction.adresa_producator ?? null,
      extraction_model: extraction.extraction_model ?? null,
      owner_user_id: document.owner_user_id,
    };

    const existing = await this.extractionResultModel.findByDocumentId(document.id, owner);
    if (existing) {
      await this.extractionResultModel.updateByDocumentId(document.id, extractionInput, owner);
    } else {
      await this.extractionResultModel.create(extractionInput);
    }
    logger.info(`Extraction result upserted for document ${document.id} with status: ${extractionStatus}`);

    await this.documentModel.updateStatus(document.id, {
      processing_status: ProcessingStatus.COMPLETED,
      processing_completed_at: new Date(),
      error_message: null,
    }, owner);

    // Silence unused-parameter lint when actorUserId not needed yet (audit is in caller)
    void actorUserId;
  }

  /**
   * POST /api/documents — upload and process a PDF
   */
  async uploadDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const actor = userIdOf(req);
      const owner = ownerOf(req);
      const ownerUserId = req.user?.id ?? null;

      let filePath: string;
      let filename: string;
      let originalFilename: string;
      let fileSize: number;

      if (req.file) {
        filePath = req.file.path;
        filename = req.file.filename;
        originalFilename = req.file.originalname;
        fileSize = req.file.size;
      } else if (req.body.file_path) {
        filePath = req.body.file_path;
        try {
          const stats = await fs.stat(filePath);
          fileSize = stats.size;
        } catch {
          res.status(400).json({
            error: { name: 'ValidationError', message: 'File not found at the specified path', code: 'FILE_NOT_FOUND' },
          });
          return;
        }
        originalFilename = path.basename(filePath);
        filename = originalFilename;
      } else {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'No file provided. Include a file upload or file_path in request body', code: 'NO_FILE_PROVIDED' },
        });
        return;
      }

      if (!originalFilename.toLowerCase().endsWith('.pdf')) {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'Only PDF files are supported', code: 'INVALID_FILE_TYPE' },
        });
        return;
      }

      const documentInput: CreateDocumentInput = {
        filename,
        original_filename: originalFilename,
        file_path: filePath,
        file_size: fileSize,
        mime_type: 'application/pdf',
        owner_user_id: ownerUserId,
      };

      const document = await this.documentModel.create(documentInput);
      logger.info(`Document created with ID: ${document.id} (owner=${ownerUserId})`);

      try {
        await this.auditService.logDocumentUpload({
          filename: document.filename,
          original_filename: document.original_filename,
          file_size: document.file_size,
          file_path: document.file_path,
        }, actor);
      } catch (auditError: any) {
        logger.error(`Failed to create audit log for document upload ${document.id}:`, auditError);
      }

      await this.documentModel.updateStatus(document.id, {
        processing_status: ProcessingStatus.PROCESSING,
        processing_started_at: new Date(),
      }, owner);

      try {
        await this.auditService.logDocumentStatusChange({
          document_id: document.id,
          filename: document.filename,
          previous_status: ProcessingStatus.PENDING,
          new_status: ProcessingStatus.PROCESSING,
        }, actor);
      } catch (auditError: any) {
        logger.error(`Failed to create audit log for status change ${document.id}:`, auditError);
      }

      let extractionResult;
      try {
        const pipelineStartTime = Date.now();
        const pipelineResponse = await this.pipelineClient.processDocument(filePath, originalFilename);
        const pipelineResponseTimeMs = Date.now() - pipelineStartTime;
        logger.info(`Pipeline processed document ${document.id}: type=${pipelineResponse.classification}, confidence=${pipelineResponse.confidence}`);

        const extraction = pipelineResponse.extraction || {};
        const extractionFields = ['material', 'data_expirare', 'companie', 'producator', 'distribuitor', 'adresa_producator', 'extraction_model'];
        const extractedFields = extractionFields.filter(f => extraction[f] != null && extraction[f] !== '');
        const nullFields = extractionFields.filter(f => extraction[f] == null || extraction[f] === '');
        logger.info(`Document processing summary for ${document.id}`, {
          documentId: document.id,
          extractedFields,
          nullFields,
          usedVision: pipelineResponse.used_vision,
          reviewStatus: pipelineResponse.review_status,
          method: pipelineResponse.method,
          confidence: pipelineResponse.confidence,
          pipelineResponseTimeMs,
        });

        if (pipelineResponse.error) {
          throw new Error(pipelineResponse.error);
        }

        // Normalize review_status from pipeline — it returns 'OK' | 'REVIEW'
        // | 'FAILED' | 'NEEDS_CHECK' but our ReviewStatus enum only knows
        // OK/REVIEW. Anything that isn't a clean OK goes to REVIEW so the
        // UI surfaces it and the field never falls back to OK silently.
        const pipelineReviewStatus =
          pipelineResponse.review_status === 'OK'
            ? ReviewStatus.OK
            : ReviewStatus.REVIEW;
        const pipelineReviewReasons: unknown =
          (pipelineResponse as any).review_reasons ?? [];

        if (pipelineResponse.classification) {
          await this.documentModel.updateClassification(document.id, {
            categorie: pipelineResponse.classification,
            confidence: pipelineResponse.confidence ?? 0,
            metoda_clasificare: pipelineResponse.method ?? 'ai',
            // FIX: previously review_status was never forwarded, so every
            // doc ended up OK regardless of what the pipeline decided.
            review_status: pipelineReviewStatus,
          }, owner);
          logger.info(
            `Classification saved for document ${document.id}: ` +
            `${pipelineResponse.classification} (review_status=${pipelineReviewStatus})`,
          );
        }

        const extractionStatus = pipelineResponse.confidence >= 0.8
          ? ExtractionStatus.SUCCESS
          : pipelineResponse.confidence >= 0.5
            ? ExtractionStatus.PARTIAL
            : ExtractionStatus.FAILED;

        const extractionInput: CreateExtractionResultInput = {
          document_id: document.id,
          extracted_text: null,
          // Persist structured review reasons + pipeline provenance so the
          // UI can show WHY a document is in REVIEW without having to grep
          // the JSON logs, and so future backfills can group by reason.
          metadata: {
            review_reasons: pipelineReviewReasons,
            pipeline_used_vision: pipelineResponse.used_vision,
            pipeline_method: pipelineResponse.method,
            pipeline_total_duration_ms:
              (pipelineResponse as any).total_duration_ms ?? null,
          },
          confidence_score: pipelineResponse.confidence ?? null,
          extraction_status: extractionStatus,
          material: extraction.material ?? null,
          data_expirare: extraction.data_expirare ?? null,
          companie: extraction.companie ?? null,
          producator: extraction.producator ?? null,
          distribuitor: extraction.distribuitor ?? null,
          adresa_producator: extraction.adresa_producator ?? null,
          extraction_model: extraction.extraction_model ?? null,
          owner_user_id: ownerUserId,
        };

        extractionResult = await this.extractionResultModel.create(extractionInput);
        logger.info(`Extraction result created for document ${document.id} with status: ${extractionStatus}`);

        await this.documentModel.updateStatus(document.id, {
          processing_status: ProcessingStatus.COMPLETED,
          processing_completed_at: new Date(),
        }, owner);

        try {
          await this.auditService.logDocumentStatusChange({
            document_id: document.id,
            filename: document.filename,
            previous_status: ProcessingStatus.PROCESSING,
            new_status: ProcessingStatus.COMPLETED,
          }, actor);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for status change ${document.id}:`, auditError);
        }

      } catch (error: any) {
        const errorMessage = error instanceof PipelineError
          ? `Pipeline error: ${error.message}`
          : error.message;
        logger.error(`Pipeline processing failed for document ${document.id}:`, error);

        const extractionInput: CreateExtractionResultInput = {
          document_id: document.id,
          extraction_status: ExtractionStatus.FAILED,
          error_details: {
            message: errorMessage,
            code: error.code || (error instanceof PipelineError ? 'PIPELINE_ERROR' : 'PROCESSING_ERROR'),
            timestamp: new Date().toISOString(),
          },
          owner_user_id: ownerUserId,
        };

        extractionResult = await this.extractionResultModel.create(extractionInput);

        await this.documentModel.updateStatus(document.id, {
          processing_status: ProcessingStatus.FAILED,
          error_message: errorMessage,
          processing_completed_at: new Date(),
        }, owner);

        try {
          await this.auditService.logDocumentStatusChange({
            document_id: document.id,
            filename: document.filename,
            previous_status: ProcessingStatus.PROCESSING,
            new_status: ProcessingStatus.FAILED,
            reason: error.message,
          }, actor);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for status change ${document.id}:`, auditError);
        }
      }

      const updatedDocument = await this.documentModel.findById(document.id, owner);

      res.status(201).json({
        document: updatedDocument,
        extraction: extractionResult,
      });

    } catch (error) {
      next(error);
    }
  }

  async listDocuments(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
      const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;
      const status = req.query.status as ProcessingStatus | undefined;

      if (status && !Object.values(ProcessingStatus).includes(status)) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: `Invalid status. Must be one of: ${Object.values(ProcessingStatus).join(', ')}`,
            code: 'INVALID_STATUS',
          },
        });
        return;
      }

      const documents = await this.documentModel.findAll(limit, offset, status, owner);

      res.status(200).json({
        documents,
        count: documents.length,
        limit: limit || null,
        offset: offset || 0,
      });

    } catch (error) {
      next(error);
    }
  }

  async reprocessDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const actor = userIdOf(req);
      const documentId = parseInt(req.params.id, 10);

      if (isNaN(documentId) || documentId <= 0) {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'Invalid document ID. Must be a positive integer.', code: 'INVALID_DOCUMENT_ID' },
        });
        return;
      }

      const document = await this.documentModel.findById(documentId, owner);

      if (!document) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'Document not found', code: 'DOCUMENT_NOT_FOUND' },
        });
        return;
      }

      try {
        await this.reprocessSingleDocument(document, owner, actor);
      } catch (error: any) {
        if (error instanceof PipelineError && error.code === 'ECONNREFUSED') {
          res.status(503).json({
            error: { name: 'ServiceUnavailableError', message: 'Pipeline service is not available', code: 'PIPELINE_UNAVAILABLE' },
          });
          return;
        }

        if (error instanceof PipelineError || error.code === 'ENOENT') {
          res.status(422).json({
            error: { name: 'UnprocessableEntityError', message: `Failed to reprocess document: ${error.message}`, code: 'REPROCESS_FAILED' },
          });
          return;
        }

        throw error;
      }

      const updatedDocument = await this.documentModel.findById(documentId, owner);
      const extraction = await this.extractionResultModel.findByDocumentId(documentId, owner);

      logger.info(`Document ${documentId} reprocessed successfully`);

      res.status(200).json({
        document: updatedDocument,
        extraction,
      });

    } catch (error) {
      next(error);
    }
  }

  async reprocessAll(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const actor = userIdOf(req);
      const { status, limit } = req.body || {};

      if (status && !Object.values(ProcessingStatus).includes(status)) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: `Invalid status. Must be one of: ${Object.values(ProcessingStatus).join(', ')}`,
            code: 'INVALID_STATUS',
          },
        });
        return;
      }

      const documents = await this.documentModel.findAll(
        limit ? parseInt(limit as string, 10) : undefined,
        undefined,
        status as ProcessingStatus | undefined,
        owner,
      );

      const jobId = `reprocess-${Date.now()}`;

      res.status(202).json({
        message: `Reprocessing ${documents.length} document(s) in the background`,
        jobId,
        total: documents.length,
      });

      void (async () => {
        try {
          const concurrency = await this.resolveBatchConcurrency();
          logger.info(`[${jobId}] Background reprocessing STARTED for ${documents.length} documents (owner=${owner ?? 'admin-all'}, concurrency=${concurrency})`);

          let processed = 0;
          let failed = 0;
          const limit = createLimiter(concurrency);

          await Promise.all(documents.map(document => limit(async () => {
            try {
              logger.info(`[${jobId}] Processing document ${document.id} (${document.original_filename})...`);
              await this.reprocessSingleDocument(document, owner, actor);
              processed++;
              logger.info(`[${jobId}] Reprocessed document ${document.id} (${processed}/${documents.length})`);
            } catch (error: any) {
              failed++;
              logger.error(`[${jobId}] Failed to reprocess document ${document.id}: ${error.message}`);

              try {
                await this.documentModel.updateStatus(document.id, {
                  processing_status: ProcessingStatus.FAILED,
                  error_message: error.message,
                  processing_completed_at: new Date(),
                }, owner);
              } catch (updateError: any) {
                logger.error(`[${jobId}] Failed to update status for document ${document.id}: ${updateError.message}`);
              }
            }
          })));

          logger.info(`[${jobId}] Batch reprocessing complete: ${processed} succeeded, ${failed} failed out of ${documents.length}`);
        } catch (bgError: any) {
          logger.error(`[${jobId}] Background reprocessing crashed: ${bgError.message}`);
        }
      })();

      return;

    } catch (error) {
      next(error);
    }
  }

  async getStats(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const ownerClause = owner !== null ? 'WHERE owner_user_id = $1' : '';
      const ownerParams = owner !== null ? [owner] : [];

      const classificationQuery = `
        SELECT
          COUNT(*)::int AS total_documents,
          COUNT(*) FILTER (WHERE processing_status = 'completed')::int AS completed,
          COUNT(*) FILTER (WHERE processing_status = 'failed')::int AS failed,
          COUNT(*) FILTER (WHERE processing_status = 'pending')::int AS pending,
          COUNT(*) FILTER (WHERE processing_status = 'processing')::int AS processing,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'filename_regex')::int AS method_filename_regex,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'text_rules')::int AS method_text_rules,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'ai')::int AS method_ai,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'filename+text_agree')::int AS method_filename_text_agree,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'text_override')::int AS method_text_override,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'vision')::int AS method_vision,
          ROUND(AVG(confidence)::numeric, 4) AS average_confidence,
          COUNT(*) FILTER (WHERE categorie = 'ALTELE')::int AS categorie_altele
        FROM documents
        ${ownerClause}
      `;

      const extractionQuery = `
        SELECT
          COUNT(*)::int AS total,
          COUNT(companie)::int AS has_companie,
          COUNT(material)::int AS has_material,
          COUNT(data_expirare)::int AS has_data_expirare,
          COUNT(producator)::int AS has_producator,
          COUNT(distribuitor)::int AS has_distribuitor,
          COUNT(adresa_producator)::int AS has_adresa_producator
        FROM extraction_results
        ${ownerClause}
      `;

      const [classificationResult, extractionResult] = await Promise.all([
        this.pool.query(classificationQuery, ownerParams),
        this.pool.query(extractionQuery, ownerParams),
      ]);

      const classRow = classificationResult.rows[0];
      const extrRow = extractionResult.rows[0];

      res.status(200).json({
        classification: {
          total_documents: classRow.total_documents,
          completed: classRow.completed,
          failed: classRow.failed,
          pending: classRow.pending,
          processing: classRow.processing,
          by_method: {
            filename_regex: classRow.method_filename_regex,
            text_rules: classRow.method_text_rules,
            ai: classRow.method_ai,
            'filename+text_agree': classRow.method_filename_text_agree,
            text_override: classRow.method_text_override,
            vision: classRow.method_vision,
          },
          average_confidence: classRow.average_confidence ? parseFloat(classRow.average_confidence) : null,
          categorie_altele: classRow.categorie_altele,
        },
        extraction: {
          total: extrRow.total,
          has_companie: extrRow.has_companie,
          has_material: extrRow.has_material,
          has_data_expirare: extrRow.has_data_expirare,
          has_producator: extrRow.has_producator,
          has_distribuitor: extrRow.has_distribuitor,
          has_adresa_producator: extrRow.has_adresa_producator,
        },
      });

    } catch (error) {
      next(error);
    }
  }

  async clearAllDocuments(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const actor = userIdOf(req);
      const deletedCount = await this.documentModel.deleteAll(owner);

      try {
        await this.auditService.logDocumentDelete({
          document_id: 0,
          filename: '*',
          file_path: '*',
        }, actor);
      } catch (auditError: any) {
        logger.error('Failed to create audit log for bulk document delete:', auditError);
      }

      logger.info(`Bulk delete completed: ${deletedCount} document(s) removed`);

      res.status(200).json({
        deleted: deletedCount,
        message: `Successfully deleted ${deletedCount} document(s)`,
      });

    } catch (error) {
      next(error);
    }
  }

  async uploadFolder(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const actor = userIdOf(req);
      const ownerUserId = req.user?.id ?? null;

      const files = req.files as Express.Multer.File[] | undefined;
      const relativePaths: string[] = req.body.relativePaths
        ? (typeof req.body.relativePaths === 'string'
          ? JSON.parse(req.body.relativePaths)
          : req.body.relativePaths)
        : [];

      if (!files || files.length === 0) {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'No files provided. Upload files via multipart form data.', code: 'NO_FILES_PROVIDED' },
        });
        return;
      }

      const results: Array<{
        document: Document | null;
        extraction: any;
        relativePath: string | null;
        success: boolean;
        error: string | null;
      }> = [];

      const documentsToProcess: Array<{ document: Document }> = [];

      for (let idx = 0; idx < files.length; idx++) {
        const file = files[idx];
        const relativePath = relativePaths[idx] || file.originalname;

        if (!file.originalname.toLowerCase().endsWith('.pdf')) {
          results.push({ document: null, extraction: null, relativePath, success: false, error: 'Only PDF files are supported' });
          continue;
        }

        try {
          const documentInput: CreateDocumentInput = {
            filename: file.filename,
            original_filename: file.originalname,
            file_path: file.path,
            file_size: file.size,
            mime_type: 'application/pdf',
            relative_path: relativePath,
            owner_user_id: ownerUserId,
          };

          const document = await this.documentModel.create(documentInput);
          logger.info(`[uploadFolder] Document created with ID: ${document.id}, relativePath: ${relativePath}`);

          documentsToProcess.push({ document });
          results.push({ document, extraction: null, relativePath, success: true, error: null });
        } catch (fileError: any) {
          logger.error(`[uploadFolder] Failed to create record for ${file.originalname}:`, fileError);
          results.push({ document: null, extraction: null, relativePath, success: false, error: fileError.message });
        }
      }

      const jobId = `folder-upload-${Date.now()}`;

      res.status(202).json({
        results,
        totalProcessed: files.length,
        totalFailed: results.filter(r => r.error).length,
        totalAccepted: documentsToProcess.length,
        jobId,
        message: `${documentsToProcess.length} document(s) accepted for processing in the background`,
      });

      void (async () => {
        let processed = 0;
        let failed = 0;
        const total = documentsToProcess.length;
        const concurrency = await this.resolveBatchConcurrency();
        const limit = createLimiter(concurrency);

        logger.info(`[${jobId}] Folder upload processing STARTED for ${total} documents (concurrency=${concurrency})`);

        await Promise.all(documentsToProcess.map(({ document }) => limit(async () => {
          try {
            await this.documentModel.updateStatus(document.id, {
              processing_status: ProcessingStatus.PROCESSING,
              processing_started_at: new Date(),
            }, owner);

            await this.reprocessSingleDocument(document, owner, actor);
            processed++;
            logger.info(`[${jobId}] Processed document ${document.id} (${processed}/${total})`);
          } catch (error: any) {
            failed++;
            const errorMessage = error instanceof PipelineError
              ? `Pipeline error: ${error.message}`
              : error.message;
            logger.error(`[${jobId}] Failed to process document ${document.id}: ${errorMessage}`);

            try {
              await this.extractionResultModel.create({
                document_id: document.id,
                extraction_status: ExtractionStatus.FAILED,
                error_details: {
                  message: errorMessage,
                  code: error.code || 'PROCESSING_ERROR',
                  timestamp: new Date().toISOString(),
                },
                owner_user_id: ownerUserId,
              });
            } catch (extractionError: any) {
              logger.error(`[${jobId}] Failed to create error extraction for document ${document.id}: ${extractionError.message}`);
            }

            try {
              await this.documentModel.updateStatus(document.id, {
                processing_status: ProcessingStatus.FAILED,
                error_message: errorMessage,
                processing_completed_at: new Date(),
              }, owner);
            } catch (statusError: any) {
              logger.error(`[${jobId}] Failed to update status for document ${document.id}: ${statusError.message}`);
            }
          }
        })));

        logger.info(`[${jobId}] Folder upload processing complete: ${processed} succeeded, ${failed} failed out of ${total}`);
      })();

      return;

    } catch (error) {
      next(error);
    }
  }

  async exportArchive(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const { documents: documentEntries, folderName } = req.body || {};

      if (!documentEntries || !Array.isArray(documentEntries) || documentEntries.length === 0) {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'Request body must include a non-empty "documents" array with { id, relativePath } entries.', code: 'INVALID_DOCUMENTS_INPUT' },
        });
        return;
      }

      const archiveRecords: ArchiveDocumentRecord[] = [];

      for (const entry of documentEntries) {
        const documentId = typeof entry.id === 'string' ? parseInt(entry.id, 10) : entry.id;

        if (isNaN(documentId) || documentId <= 0) {
          logger.warn(`[exportArchive] Skipping invalid document ID: ${entry.id}`);
          continue;
        }

        const document = await this.documentModel.findById(documentId, owner);
        if (!document) {
          logger.warn(`[exportArchive] Document not found (or not owned): ${documentId}`);
          continue;
        }

        const extraction = await this.extractionResultModel.findByDocumentId(documentId, owner);

        archiveRecords.push({
          document,
          extraction,
          relativePath: entry.relativePath || document.relative_path || document.original_filename,
          absolutePath: document.file_path,
        });
      }

      if (archiveRecords.length === 0) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'No valid documents found for the given IDs.', code: 'NO_DOCUMENTS_FOUND' },
        });
        return;
      }

      const archiveFilename = folderName ? `${folderName}.zip` : `archive-${Date.now()}.zip`;

      const archiveService = new ArchiveService();
      await archiveService.generateArchive(archiveRecords, res, archiveFilename);

      logger.info(`[exportArchive] Archive streamed with ${archiveRecords.length} documents`);

    } catch (error) {
      next(error);
    }
  }

  async reviewDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    const VALID_CATEGORIES = [
      'ISO', 'CE', 'FISA_TEHNICA', 'AGREMENT', 'AVIZ_TEHNIC', 'AVIZ_SANITAR',
      'DECLARATIE_CONFORMITATE', 'CERTIFICAT_CALITATE', 'AUTORIZATIE_DISTRIBUTIE',
      'CUI', 'CERTIFICAT_GARANTIE', 'DECLARATIE_PERFORMANTA', 'AVIZ_TEHNIC_SI_AGREMENT', 'ALTELE',
    ];

    try {
      const owner = ownerOf(req);
      const actor = userIdOf(req);
      const documentId = parseInt(req.params.id, 10);

      if (isNaN(documentId) || documentId <= 0) {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'Invalid document ID. Must be a positive integer.', code: 'INVALID_DOCUMENT_ID' },
        });
        return;
      }

      const document = await this.documentModel.findById(documentId, owner);

      if (!document) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'Document not found', code: 'DOCUMENT_NOT_FOUND' },
        });
        return;
      }

      const { action, rejection_reason, corrected_category, wrong_fields, comment } = req.body;

      if (action !== 'approve' && action !== 'reject') {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'Action must be "approve" or "reject".', code: 'INVALID_ACTION' },
        });
        return;
      }

      let updatedDocument: Document | null = null;

      if (action === 'approve') {
        updatedDocument = await this.documentModel.updateReviewStatus(documentId, ReviewStatus.OK, owner);

        try {
          await this.auditService.logDocumentReview({
            document_id: documentId,
            filename: document.filename,
            review_action: 'approve',
            comment,
          }, actor);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for document review ${documentId}:`, auditError);
        }

      } else if (rejection_reason === 'wrong_classification') {
        if (!corrected_category || !VALID_CATEGORIES.includes(corrected_category)) {
          res.status(400).json({
            error: { name: 'ValidationError', message: `corrected_category must be one of: ${VALID_CATEGORIES.join(', ')}`, code: 'INVALID_CATEGORY' },
          });
          return;
        }

        const originalCategory = document.categorie;

        updatedDocument = await this.documentModel.updateClassification(documentId, {
          categorie: corrected_category,
          confidence: 1.0,
          metoda_clasificare: 'human_review',
          review_status: ReviewStatus.OK,
        }, owner);

        try {
          await this.auditService.logDocumentReview({
            document_id: documentId,
            filename: document.filename,
            review_action: 'reject',
            rejection_reason: 'wrong_classification',
            original_category: originalCategory || undefined,
            corrected_category,
            comment,
          }, actor);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for document review ${documentId}:`, auditError);
        }

      } else if (rejection_reason === 'wrong_extraction') {
        if (!wrong_fields || !Array.isArray(wrong_fields) || wrong_fields.length === 0) {
          res.status(400).json({
            error: { name: 'ValidationError', message: 'wrong_fields must be a non-empty array.', code: 'INVALID_WRONG_FIELDS' },
          });
          return;
        }

        updatedDocument = await this.documentModel.updateReviewStatus(documentId, ReviewStatus.REVIEW, owner);

        try {
          await this.auditService.logDocumentReview({
            document_id: documentId,
            filename: document.filename,
            review_action: 'reject',
            rejection_reason: 'wrong_extraction',
            wrong_fields,
            comment,
          }, actor);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for document review ${documentId}:`, auditError);
        }

      } else {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'rejection_reason must be "wrong_classification" or "wrong_extraction" when action is "reject".', code: 'INVALID_REJECTION_REASON' },
        });
        return;
      }

      const extraction = await this.extractionResultModel.findByDocumentId(documentId, owner);

      res.status(200).json({
        document: updatedDocument,
        extraction,
      });

    } catch (error) {
      next(error);
    }
  }

  async getDocumentById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const owner = ownerOf(req);
      const documentId = parseInt(req.params.id, 10);

      if (isNaN(documentId) || documentId <= 0) {
        res.status(400).json({
          error: { name: 'ValidationError', message: 'Invalid document ID. Must be a positive integer.', code: 'INVALID_DOCUMENT_ID' },
        });
        return;
      }

      const document = await this.documentModel.findById(documentId, owner);

      if (!document) {
        res.status(404).json({
          error: { name: 'NotFoundError', message: 'Document not found', code: 'DOCUMENT_NOT_FOUND' },
        });
        return;
      }

      const extraction = await this.extractionResultModel.findByDocumentId(documentId, owner);

      res.status(200).json({
        document,
        extraction,
      });

    } catch (error) {
      next(error);
    }
  }

}
