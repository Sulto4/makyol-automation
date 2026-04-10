import { Request, Response, NextFunction } from 'express';
import { Pool } from 'pg';
import * as path from 'path';
import * as fs from 'fs/promises';
import { DocumentModel, ProcessingStatus, CreateDocumentInput } from '../models/Document';
import { ExtractionResultModel, ExtractionStatus, CreateExtractionResultInput } from '../models/ExtractionResult';
import { PDFExtractorService } from '../services/pdfExtractor';
import { MetadataParserService } from '../services/metadataParser';
import { logger } from '../utils/logger';
import { appConfig } from '../config/app';

/**
 * Document controller class
 * Handles HTTP requests for document upload and processing
 */
export class DocumentController {
  private documentModel: DocumentModel;
  private extractionResultModel: ExtractionResultModel;
  private pdfExtractor: PDFExtractorService;
  private metadataParser: MetadataParserService;

  constructor(pool: Pool) {
    this.documentModel = new DocumentModel(pool);
    this.extractionResultModel = new ExtractionResultModel(pool);
    this.pdfExtractor = new PDFExtractorService();
    this.metadataParser = new MetadataParserService();
  }

  /**
   * Upload and process a PDF document
   *
   * POST /api/documents
   *
   * @example
   * Request body (with file upload - when multer is added):
   * - file: PDF file (multipart/form-data)
   *
   * Request body (for testing without multer):
   * - file_path: string (absolute path to PDF file)
   *
   * Response (201):
   * {
   *   "document": { id, filename, processing_status, ... },
   *   "extraction": { extracted_text, metadata, confidence_score, ... }
   * }
   */
  async uploadDocument(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      let filePath: string;
      let filename: string;
      let originalFilename: string;
      let fileSize: number;

      // Check if file was uploaded via multer (will be available in future subtask)
      if (req.file) {
        filePath = req.file.path;
        filename = req.file.filename;
        originalFilename = req.file.originalname;
        fileSize = req.file.size;
      }
      // For testing: accept file_path in request body
      else if (req.body.file_path) {
        filePath = req.body.file_path;

        // Validate file exists
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

      // Step 2: Update status to PROCESSING
      await this.documentModel.updateStatus(document.id, {
        processing_status: ProcessingStatus.PROCESSING,
        processing_started_at: new Date(),
      });

      // Step 3: Process PDF asynchronously
      // Note: In production, this should be done in a background job queue
      // For now, we'll do it synchronously to demonstrate the full flow
      let extractionResult;
      try {
        // Extract text from PDF
        const pdfResult = await this.pdfExtractor.extractFromFile(filePath);
        logger.info(`PDF text extracted for document ${document.id}: ${pdfResult.text.length} characters`);

        // Parse metadata from extracted text
        const metadata = this.metadataParser.parse(pdfResult.text);
        const confidence = this.calculateConfidence(metadata);

        // Determine extraction status
        const extractionStatus = this.determineExtractionStatus(metadata, confidence);

        // Create extraction result record
        const extractionInput: CreateExtractionResultInput = {
          document_id: document.id,
          extracted_text: pdfResult.text,
          metadata,
          confidence_score: confidence,
          extraction_status: extractionStatus,
        };

        extractionResult = await this.extractionResultModel.create(extractionInput);
        logger.info(`Extraction result created for document ${document.id} with status: ${extractionStatus}`);

        // Update document status to COMPLETED
        await this.documentModel.updateStatus(document.id, {
          processing_status: ProcessingStatus.COMPLETED,
          processing_completed_at: new Date(),
        });

      } catch (error: any) {
        // Handle extraction errors
        logger.error(`PDF extraction failed for document ${document.id}:`, error);

        // Create failed extraction result with error details
        const extractionInput: CreateExtractionResultInput = {
          document_id: document.id,
          extraction_status: ExtractionStatus.FAILED,
          error_details: {
            message: error.message,
            code: error.code,
            timestamp: new Date().toISOString(),
          },
        };

        extractionResult = await this.extractionResultModel.create(extractionInput);

        // Update document status to FAILED
        await this.documentModel.updateStatus(document.id, {
          processing_status: ProcessingStatus.FAILED,
          error_message: error.message,
          processing_completed_at: new Date(),
        });
      }

      // Get the updated document
      const updatedDocument = await this.documentModel.findById(document.id);

      // Return 201 Created with document and extraction results
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
   *
   * @query limit - Maximum number of documents to return (optional)
   * @query offset - Number of documents to skip (optional)
   * @query status - Filter by processing status (optional)
   *
   * @example
   * Response (200):
   * {
   *   "documents": [
   *     { id, filename, processing_status, uploaded_at, ... }
   *   ],
   *   "count": 10,
   *   "limit": 50,
   *   "offset": 0
   * }
   */
  async listDocuments(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      // Parse query parameters
      const limit = req.query.limit ? parseInt(req.query.limit as string, 10) : undefined;
      const offset = req.query.offset ? parseInt(req.query.offset as string, 10) : undefined;
      const status = req.query.status as ProcessingStatus | undefined;

      // Validate status if provided
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

      // Fetch documents from database
      const documents = await this.documentModel.findAll(limit, offset, status);

      // Return list with pagination metadata
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
   * Get a document by ID with its extraction results
   *
   * GET /api/documents/:id
   *
   * @example
   * Response (200):
   * {
   *   "document": { id, filename, processing_status, ... },
   *   "extraction": { extracted_text, metadata, confidence_score, ... }
   * }
   *
   * Response (404):
   * {
   *   "error": {
   *     "name": "NotFoundError",
   *     "message": "Document not found",
   *     "code": "DOCUMENT_NOT_FOUND"
   *   }
   * }
   */
  async getDocumentById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const documentId = parseInt(req.params.id, 10);

      // Validate ID parameter
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

      // Find document by ID
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

      // Find extraction result for this document
      const extraction = await this.extractionResultModel.findByDocumentId(documentId);

      // Return 200 OK with document and extraction results
      res.status(200).json({
        document,
        extraction,
      });

    } catch (error) {
      next(error);
    }
  }

  /**
   * Calculate overall confidence score from metadata
   */
  private calculateConfidence(metadata: any): number {
    const confidenceFields = [
      'certificate_number_confidence',
      'issuing_organization_confidence',
      'issue_date_confidence',
      'expiry_date_confidence',
      'certified_company_confidence',
      'certification_scope_confidence',
    ];

    const confidenceValues = confidenceFields
      .map(field => metadata[field])
      .filter(val => typeof val === 'number');

    if (confidenceValues.length === 0) {
      return 0;
    }

    const sum = confidenceValues.reduce((acc, val) => acc + val, 0);
    return sum / confidenceValues.length;
  }

  /**
   * Determine extraction status based on metadata and confidence
   */
  private determineExtractionStatus(metadata: any, confidence: number): ExtractionStatus {
    // Check if any metadata was extracted
    const hasMetadata = Boolean(
      metadata.certificate_number ||
      metadata.issuing_organization ||
      metadata.issue_date ||
      metadata.expiry_date ||
      metadata.certified_company ||
      metadata.certification_scope
    );

    if (!hasMetadata) {
      return ExtractionStatus.FAILED;
    }

    // High confidence: all major fields extracted
    if (confidence >= 0.8) {
      return ExtractionStatus.SUCCESS;
    }

    // Partial: some fields extracted but low confidence
    if (confidence >= 0.5) {
      return ExtractionStatus.PARTIAL;
    }

    return ExtractionStatus.FAILED;
  }
}
