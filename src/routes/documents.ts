import { Router } from 'express';
import { Pool } from 'pg';
import { DocumentController } from '../controllers/documentController';
import { upload, folderUpload } from '../middleware/upload';

/**
 * Create and configure document routes
 *
 * @param pool - PostgreSQL connection pool
 * @returns Configured Express router
 */
export function createDocumentRoutes(pool: Pool): Router {
  const router = Router();
  const controller = new DocumentController(pool);

  /**
   * POST /api/documents
   * Upload and process a PDF document
   *
   * @body file - PDF file (multipart/form-data)
   * @body file_path - File path for testing (alternative to file upload)
   * @returns 201 - Document created and processed
   * @returns 400 - Invalid request (no file, invalid file type)
   * @returns 422 - PDF processing failed
   * @returns 500 - Server error
   */
  router.post('/', upload.single('file'), (req, res, next) => controller.uploadDocument(req, res, next));

  /**
   * GET /api/documents
   * List all documents with optional filtering and pagination
   *
   * @query limit - Maximum number of documents to return (optional)
   * @query offset - Number of documents to skip (optional)
   * @query status - Filter by processing status (optional)
   * @returns 200 - List of documents
   * @returns 400 - Invalid query parameters
   * @returns 500 - Server error
   */
  router.get('/', (req, res, next) => controller.listDocuments(req, res, next));

  /**
   * GET /api/documents/stats
   * Get document processing statistics
   *
   * @returns 200 - Processing statistics (counts by status, success rate, etc.)
   * @returns 500 - Server error
   */
  router.get('/stats', (req, res, next) => controller.getStats(req, res, next));

  /**
   * POST /api/documents/reprocess-all
   * Reprocess all failed documents in batch
   *
   * @returns 200 - Batch reprocessing results
   * @returns 500 - Server error
   */
  router.post('/reprocess-all', (req, res, next) => controller.reprocessAll(req, res, next));

  /**
   * DELETE /api/documents
   * Delete all documents and their associated data
   *
   * @returns 200 - All documents deleted successfully
   * @returns 500 - Server error
   */
  router.delete('/', (req, res, next) => controller.clearAllDocuments(req, res, next));

  /**
   * POST /api/documents/upload-folder
   * Upload and process multiple PDF documents from a folder structure
   *
   * @body files - PDF files (multipart/form-data)
   * @returns 201 - Documents created and processed
   * @returns 400 - Invalid request (no files, invalid file types)
   * @returns 500 - Server error
   */
  router.post('/upload-folder', folderUpload, (req, res, next) => controller.uploadFolder(req, res, next));

  /**
   * POST /api/documents/export-archive
   * Export documents as an Excel archive
   *
   * @body JSON body with export parameters
   * @returns 200 - Archive exported successfully
   * @returns 400 - Invalid request
   * @returns 500 - Server error
   */
  router.post('/export-archive', (req, res, next) => controller.exportArchive(req, res, next));

  /**
   * GET /api/documents/:id
   * Retrieve a document and its extraction results by ID
   *
   * @param id - Document ID
   * @returns 200 - Document found with extraction results
   * @returns 400 - Invalid document ID
   * @returns 404 - Document not found
   * @returns 500 - Server error
   */
  router.get('/:id', (req, res, next) => controller.getDocumentById(req, res, next));

  /**
   * POST /api/documents/:id/reprocess
   * Reprocess a single document by ID
   *
   * @param id - Document ID
   * @returns 200 - Document reprocessed successfully
   * @returns 400 - Invalid document ID
   * @returns 404 - Document not found
   * @returns 422 - Reprocessing failed
   * @returns 500 - Server error
   */
  router.post('/:id/reprocess', (req, res, next) => controller.reprocessDocument(req, res, next));

  return router;
}

export default createDocumentRoutes;
