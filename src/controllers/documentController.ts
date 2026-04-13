import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { DocumentModel, Document, ProcessingStatus, CreateDocumentInput } from '../models/Document';
import { ExtractionResultModel, ExtractionStatus, CreateExtractionResultInput } from '../models/ExtractionResult';
// Legacy services kept for potential fallback - pipeline now handles extraction
// import { PDFExtractorService } from '../services/pdfExtractor';
// import { MetadataParserService } from '../services/metadataParser';
import { PipelineClientService, PipelineError } from '../services/pipelineClient';
import { AuditService } from '../services/auditService';
import { logger } from '../utils/logger';

/**
 * Document controller class
 * Handles HTTP requests for document upload and processing
 */
export class DocumentController {
  protected pool: Pool;
  private documentModel: DocumentModel;
  private extractionResultModel: ExtractionResultModel;
  private pipelineClient: PipelineClientService;
  private auditService: AuditService;

  constructor(pool: Pool) {
    this.pool = pool;
    this.documentModel = new DocumentModel(pool);
    this.extractionResultModel = new ExtractionResultModel(pool);
    this.pipelineClient = new PipelineClientService();
    this.auditService = new AuditService(pool);
  }

  /**
   * Reprocess a single document through the pipeline
   * Updates classification, upserts extraction result, and sets status to COMPLETED
   */
  protected async reprocessSingleDocument(document: Document): Promise<void> {
    const pipelineResponse = await this.pipelineClient.processDocument(document.file_path);
    logger.info(`Pipeline reprocessed document ${document.id}: type=${pipelineResponse.classification}, confidence=${pipelineResponse.confidence}`);

    if (pipelineResponse.error) {
      throw new Error(pipelineResponse.error);
    }

    // Persist classification to documents table
    if (pipelineResponse.classification) {
      await this.documentModel.updateClassification(document.id, {
        categorie: pipelineResponse.classification,
        confidence: pipelineResponse.confidence ?? 0,
        metoda_clasificare: pipelineResponse.method ?? 'ai',
      });
      logger.info(`Classification saved for document ${document.id}: ${pipelineResponse.classification}`);
    }

    // Map pipeline extracted data to extraction result fields
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
      adresa_distribuitor: extraction.adresa_distribuitor ?? null,
      extraction_model: extraction.extraction_model ?? null,
    };

    // Upsert extraction result: update if exists, create if not
    const existing = await this.extractionResultModel.findByDocumentId(document.id);
    if (existing) {
      await this.extractionResultModel.updateByDocumentId(document.id, extractionInput);
    } else {
      await this.extractionResultModel.create(extractionInput);
    }
    logger.info(`Extraction result upserted for document ${document.id} with status: ${extractionStatus}`);

    // Update document status to COMPLETED and clear error
    await this.documentModel.updateStatus(document.id, {
      processing_status: ProcessingStatus.COMPLETED,
      processing_completed_at: new Date(),
      error_message: null,
    });
  }

  /**
   * Upload and process a PDF document
   *
   * POST /api/documents
   */
  async uploadDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      let filePath: string;
      let filename: string;
      let originalFilename: string;
      let fileSize: number;

      // Check if file was uploaded via multer
      if (req.file) {
        filePath = req.file.path;
        filename = req.file.filename;
        originalFilename = req.file.originalname;
        fileSize = req.file.size;
      }
      // For testing: accept file_path in request body
      else if (req.body.file_path) {
        filePath = req.body.file_path;

        try {
          const stats = await fs.stat(filePath);
          fileSize = stats.size;
        } catch (error) {
          res.status(400).json({
            error: {
              name: 'ValidationError',
              message: 'File not found at the specified path',
              code: 'FILE_NOT_FOUND',
            }
          });
          return;
        }

        originalFilename = path.basename(filePath);
        filename = originalFilename;
      }
      // No file provided
      else {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'No file provided. Include a file upload or file_path in request body',
            code: 'NO_FILE_PROVIDED',
          }
        });
        return;
      }

      // Validate file is PDF
      if (!originalFilename.toLowerCase().endsWith('.pdf')) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Only PDF files are supported',
            code: 'INVALID_FILE_TYPE',
          }
        });
        return;
      }

      // Step 1: Create document record with PENDING status
      const documentInput: CreateDocumentInput = {
        filename,
        original_filename: originalFilename,
        file_path: filePath,
        file_size: fileSize,
        mime_type: 'application/pdf',
      };

      const document = await this.documentModel.create(documentInput);
      logger.info(`Document created with ID: ${document.id}`);

      // Audit log: Document upload
      try {
        await this.auditService.logDocumentUpload({
          filename: document.filename,
          original_filename: document.original_filename,
          file_size: document.file_size,
          file_path: document.file_path,
        }, null);
      } catch (auditError: any) {
        logger.error(`Failed to create audit log for document upload ${document.id}:`, auditError);
      }

      // Step 2: Update status to PROCESSING
      await this.documentModel.updateStatus(document.id, {
        processing_status: ProcessingStatus.PROCESSING,
        processing_started_at: new Date(),
      });

      // Audit log: Status change to PROCESSING
      try {
        await this.auditService.logDocumentStatusChange({
          document_id: document.id,
          filename: document.filename,
          previous_status: ProcessingStatus.PENDING,
          new_status: ProcessingStatus.PROCESSING,
        }, null);
      } catch (auditError: any) {
        logger.error(`Failed to create audit log for status change ${document.id}:`, auditError);
      }

      // Step 3: Process document through Python pipeline
      let extractionResult;
      try {
        const pipelineStartTime = Date.now();
        const pipelineResponse = await this.pipelineClient.processDocument(filePath);
        const pipelineResponseTimeMs = Date.now() - pipelineStartTime;
        logger.info(`Pipeline processed document ${document.id}: type=${pipelineResponse.classification}, confidence=${pipelineResponse.confidence}`);

        // Per-document processing summary
        const extraction = pipelineResponse.extraction || {};
        const extractionFields = ['material', 'data_expirare', 'companie', 'producator', 'distribuitor', 'adresa_producator', 'adresa_distribuitor', 'extraction_model'];
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

        // Persist classification to documents table
        if (pipelineResponse.classification) {
          await this.documentModel.updateClassification(document.id, {
            categorie: pipelineResponse.classification,
            confidence: pipelineResponse.confidence ?? 0,
            metoda_clasificare: pipelineResponse.method ?? 'ai',
          });
          logger.info(`Classification saved for document ${document.id}: ${pipelineResponse.classification}`);
        }

        // Map pipeline extracted data to extraction result fields
        const extractionStatus = pipelineResponse.confidence >= 0.8
          ? ExtractionStatus.SUCCESS
          : pipelineResponse.confidence >= 0.5
            ? ExtractionStatus.PARTIAL
            : ExtractionStatus.FAILED;

        // Create extraction result record with pipeline data
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
          adresa_distribuitor: extraction.adresa_distribuitor ?? null,
          extraction_model: extraction.extraction_model ?? null,
        };

        extractionResult = await this.extractionResultModel.create(extractionInput);
        logger.info(`Extraction result created for document ${document.id} with status: ${extractionStatus}`);

        // Update document status to COMPLETED
        await this.documentModel.updateStatus(document.id, {
          processing_status: ProcessingStatus.COMPLETED,
          processing_completed_at: new Date(),
        });

        // Audit log: Status change to COMPLETED
        try {
          await this.auditService.logDocumentStatusChange({
            document_id: document.id,
            filename: document.filename,
            previous_status: ProcessingStatus.PROCESSING,
            new_status: ProcessingStatus.COMPLETED,
          }, null);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for status change ${document.id}:`, auditError);
        }

      } catch (error: any) {
        // Handle pipeline errors gracefully
        const errorMessage = error instanceof PipelineError
          ? `Pipeline error: ${error.message}`
          : error.message;
        logger.error(`Pipeline processing failed for document ${document.id}:`, error);

        // Create failed extraction result with error details
        const extractionInput: CreateExtractionResultInput = {
          document_id: document.id,
          extraction_status: ExtractionStatus.FAILED,
          error_details: {
            message: errorMessage,
            code: error.code || (error instanceof PipelineError ? 'PIPELINE_ERROR' : 'PROCESSING_ERROR'),
            timestamp: new Date().toISOString(),
          },
        };

        extractionResult = await this.extractionResultModel.create(extractionInput);

        // Update document status to FAILED
        await this.documentModel.updateStatus(document.id, {
          processing_status: ProcessingStatus.FAILED,
          error_message: errorMessage,
          processing_completed_at: new Date(),
        });

        // Audit log: Status change to FAILED
        try {
          await this.auditService.logDocumentStatusChange({
            document_id: document.id,
            filename: document.filename,
            previous_status: ProcessingStatus.PROCESSING,
            new_status: ProcessingStatus.FAILED,
            reason: error.message,
          }, null);
        } catch (auditError: any) {
          logger.error(`Failed to create audit log for status change ${document.id}:`, auditError);
        }
      }

      // Get the updated document
      const updatedDocument = await this.documentModel.findById(document.id);

      res.status(201).json({
        document: updatedDocument,
        extraction: extractionResult,
      });

    } catch (error) {
      next(error);
    }
  }

  /**
   * List all documents with optional filtering and pagination
   *
   * GET /api/documents
   */
  async listDocuments(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
      const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;
      const status = req.query.status as ProcessingStatus | undefined;

      if (status && !Object.values(ProcessingStatus).includes(status)) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: `Invalid status. Must be one of: ${Object.values(ProcessingStatus).join(', ')}`,
            code: 'INVALID_STATUS',
          }
        });
        return;
      }

      const documents = await this.documentModel.findAll(limit, offset, status);

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

  /**
   * Reprocess a document through the pipeline
   *
   * POST /api/documents/:id/reprocess
   */
  async reprocessDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const documentId = parseInt(req.params.id, 10);

      if (isNaN(documentId) || documentId <= 0) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Invalid document ID. Must be a positive integer.',
            code: 'INVALID_DOCUMENT_ID',
          }
        });
        return;
      }

      const document = await this.documentModel.findById(documentId);

      if (!document) {
        res.status(404).json({
          error: {
            name: 'NotFoundError',
            message: 'Document not found',
            code: 'DOCUMENT_NOT_FOUND',
          }
        });
        return;
      }

      try {
        await this.reprocessSingleDocument(document);
      } catch (error: any) {
        if (error instanceof PipelineError && error.code === 'ECONNREFUSED') {
          res.status(503).json({
            error: {
              name: 'ServiceUnavailableError',
              message: 'Pipeline service is not available',
              code: 'PIPELINE_UNAVAILABLE',
            }
          });
          return;
        }

        // File-level errors (e.g., file not found, unreadable)
        if (error instanceof PipelineError || error.code === 'ENOENT') {
          res.status(422).json({
            error: {
              name: 'UnprocessableEntityError',
              message: `Failed to reprocess document: ${error.message}`,
              code: 'REPROCESS_FAILED',
            }
          });
          return;
        }

        throw error;
      }

      // Get updated document and extraction
      const updatedDocument = await this.documentModel.findById(documentId);
      const extraction = await this.extractionResultModel.findByDocumentId(documentId);

      logger.info(`Document ${documentId} reprocessed successfully`);

      res.status(200).json({
        document: updatedDocument,
        extraction,
      });

    } catch (error) {
      next(error);
    }
  }

  /**
   * Reprocess all documents matching optional filters
   *
   * POST /api/documents/reprocess-all
   */
  async reprocessAll(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { status, limit } = req.body || {};

      // Validate status against ProcessingStatus enum if provided
      if (status && !Object.values(ProcessingStatus).includes(status)) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: `Invalid status. Must be one of: ${Object.values(ProcessingStatus).join(', ')}`,
            code: 'INVALID_STATUS',
          }
        });
        return;
      }

      // Query matching documents
      const documents = await this.documentModel.findAll(
        limit ? parseInt(limit as string, 10) : undefined,
        undefined,
        status as ProcessingStatus | undefined
      );

      const jobId = `reprocess-${Date.now()}`;

      // Respond immediately
      res.status(202).json({
        message: `Reprocessing ${documents.length} document(s) in the background`,
        jobId,
        total: documents.length,
      });

      // Fire-and-forget: background processing in its own try-catch
      void (async () => {
        try {
          const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

          let processed = 0;
          let failed = 0;

          for (const document of documents) {
            try {
              await this.reprocessSingleDocument(document);
              processed++;
              logger.info(`[${jobId}] Reprocessed document ${document.id} (${processed}/${documents.length})`);
            } catch (error: any) {
              failed++;
              logger.error(`[${jobId}] Failed to reprocess document ${document.id}: ${error.message}`);

              // Update document status to FAILED
              try {
                await this.documentModel.updateStatus(document.id, {
                  processing_status: ProcessingStatus.FAILED,
                  error_message: error.message,
                  processing_completed_at: new Date(),
                });
              } catch (updateError: any) {
                logger.error(`[${jobId}] Failed to update status for document ${document.id}: ${updateError.message}`);
              }
            }

            // 1s delay between documents
            if (document !== documents[documents.length - 1]) {
              await delay(1000);
            }
          }

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

  /**
   * Get processing statistics for documents and extractions
   *
   * GET /api/documents/stats
   */
  async getStats(_req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      // Classification stats from documents table
      const classificationQuery = `
        SELECT
          COUNT(*)::int AS total_documents,
          COUNT(*) FILTER (WHERE processing_status = 'COMPLETED')::int AS completed,
          COUNT(*) FILTER (WHERE processing_status = 'FAILED')::int AS failed,
          COUNT(*) FILTER (WHERE processing_status = 'PENDING')::int AS pending,
          COUNT(*) FILTER (WHERE processing_status = 'PROCESSING')::int AS processing,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'filename_regex')::int AS method_filename_regex,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'text_rules')::int AS method_text_rules,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'ai')::int AS method_ai,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'filename+text_agree')::int AS method_filename_text_agree,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'text_override')::int AS method_text_override,
          COUNT(*) FILTER (WHERE metoda_clasificare = 'vision')::int AS method_vision,
          ROUND(AVG(confidence)::numeric, 4) AS average_confidence,
          COUNT(*) FILTER (WHERE categorie = 'ALTELE')::int AS categorie_altele
        FROM documents
      `;

      // Extraction stats from extraction_results table
      const extractionQuery = `
        SELECT
          COUNT(*)::int AS total,
          COUNT(companie)::int AS has_companie,
          COUNT(material)::int AS has_material,
          COUNT(data_expirare)::int AS has_data_expirare,
          COUNT(producator)::int AS has_producator,
          COUNT(distribuitor)::int AS has_distribuitor,
          COUNT(adresa_producator)::int AS has_adresa_producator,
          COUNT(adresa_distribuitor)::int AS has_adresa_distribuitor
        FROM extraction_results
      `;

      const [classificationResult, extractionResult] = await Promise.all([
        this.pool.query(classificationQuery),
        this.pool.query(extractionQuery),
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
          has_adresa_distribuitor: extrRow.has_adresa_distribuitor,
        },
      });

    } catch (error) {
      next(error);
    }
  }

  /**
   * Delete all documents and their associated data
   *
   * DELETE /api/documents
   */
  async clearAllDocuments(_req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const deletedCount = await this.documentModel.deleteAll();

      // Audit log: Bulk document delete
      try {
        await this.auditService.logDocumentDelete({
          document_id: 0,
          filename: '*',
          file_path: '*',
        }, null);
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

  /**
   * Get a document by ID with its extraction results
   *
   * GET /api/documents/:id
   */
  async getDocumentById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const documentId = parseInt(req.params.id, 10);

      if (isNaN(documentId) || documentId <= 0) {
        res.status(400).json({
          error: {
            name: 'ValidationError',
            message: 'Invalid document ID. Must be a positive integer.',
            code: 'INVALID_DOCUMENT_ID',
          }
        });
        return;
      }

      const document = await this.documentModel.findById(documentId);

      if (!document) {
        res.status(404).json({
          error: {
            name: 'NotFoundError',
            message: 'Document not found',
            code: 'DOCUMENT_NOT_FOUND',
          }
        });
        return;
      }

      const extraction = await this.extractionResultModel.findByDocumentId(documentId);

      res.status(200).json({
        document,
        extraction,
      });

    } catch (error) {
      next(error);
    }
  }

}
