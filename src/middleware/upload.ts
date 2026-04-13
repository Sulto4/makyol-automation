import multer from 'multer';
import path from 'path';
import { Request } from 'express';
import { appConfig } from '../config/app';
import * as fs from 'fs';

/**
 * Configure multer storage
 * Files are saved with unique names to prevent collisions
 */
const storage = multer.diskStorage({
  destination: (_req: Request, _file: Express.Multer.File, cb) => {
    const uploadDir = appConfig.upload.uploadDir;

    // Ensure upload directory exists
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }

    cb(null, uploadDir);
  },
  filename: (_req: Request, file: Express.Multer.File, cb) => {
    // Generate unique filename: timestamp-randomstring-originalname
    const uniqueSuffix = `${Date.now()}-${Math.round(Math.random() * 1e9)}`;
    const ext = path.extname(file.originalname);
    const basename = path.basename(file.originalname, ext);
    const sanitizedBasename = basename.replace(/[^a-zA-Z0-9-_]/g, '_');
    const filename = `${sanitizedBasename}-${uniqueSuffix}${ext}`;

    cb(null, filename);
  },
});

/**
 * File filter to accept only PDF files
 */
const fileFilter = (
  _req: Request,
  file: Express.Multer.File,
  cb: multer.FileFilterCallback
): void => {
  // Check MIME type
  if (file.mimetype === 'application/pdf') {
    cb(null, true);
  } else {
    // Reject file
    cb(new Error('Only PDF files are allowed'));
  }
};

/**
 * Multer upload middleware configuration
 *
 * @example
 * ```typescript
 * router.post('/upload', upload.single('file'), controller.handleUpload);
 * ```
 */
export const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: appConfig.upload.maxFileSize,
  },
});

/**
 * Multer upload middleware for folder/batch uploads (up to 100 PDFs)
 *
 * @example
 * ```typescript
 * router.post('/upload-folder', folderUpload, controller.handleFolderUpload);
 * ```
 */
export const folderUpload = upload.array('files', 100);
