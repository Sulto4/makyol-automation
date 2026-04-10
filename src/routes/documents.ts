import { Router } from 'express';
import { Pool } from 'pg';
import { DocumentController } from '../controllers/documentController';

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
   * @body file - PDF file (when multer is configured)
   * @body file_path - File path for testing (alternative to file upload)
   * @returns 201 - Document created and processed
   * @returns 400 - Invalid request (no file, invalid file type)
   * @returns 422 - PDF processing failed
   * @returns 500 - Server error
   */
  router.post('/', (req, res, next) => controller.uploadDocument(req, res, next));

  return router;
}

export default createDocumentRoutes;
