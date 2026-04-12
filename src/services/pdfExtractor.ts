import * as fs from 'fs/promises';
import pdfParse from 'pdf-parse';
import {
  PDFNotFoundError,
  PDFPermissionDeniedError,
  PDFCorruptedError,
  PDFEncryptedError,
  PDFScannedError,
  PDFInvalidFormatError,
  PDFInvalidInputError,
  PDFParsingError,
  PDFFileSystemError,
} from '../utils/errors';

/**
 * PDF extraction result interface
 */
export interface PDFExtractionResult {
  text: string;
  numPages: number;
  info?: any;
  metadata?: any;
}

/**
 * PDF extraction options
 */
export interface PDFExtractionOptions {
  maxPages?: number;
  pageRange?: { start: number; end: number };
}

/**
 * PDF Extractor Service
 *
 * Handles extraction of text content from PDF files using pdf-parse library.
 * Supports both file path and buffer inputs for flexible usage.
 */
export class PDFExtractorService {
  /**
   * Extract text from a PDF file by file path
   *
   * @param filePath - Absolute or relative path to the PDF file
   * @param options - Optional extraction options
   * @returns Extraction result containing text and metadata
   * @throws Error if file doesn't exist or cannot be read
   * @throws Error if PDF parsing fails
   */
  async extractFromFile(
    filePath: string,
    options?: PDFExtractionOptions
  ): Promise<PDFExtractionResult> {
    try {
      // Check if file exists
      await fs.access(filePath);

      // Read file into buffer
      const dataBuffer = await fs.readFile(filePath);

      // Extract from buffer
      return await this.extractFromBuffer(dataBuffer, options);
    } catch (error) {
      // Re-throw custom errors from extractFromBuffer
      if (error instanceof PDFInvalidFormatError ||
          error instanceof PDFCorruptedError ||
          error instanceof PDFEncryptedError ||
          error instanceof PDFInvalidInputError ||
          error instanceof PDFParsingError ||
          error instanceof PDFScannedError) {
        throw error;
      }

      // Handle file system errors
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new PDFNotFoundError(filePath);
      }
      if ((error as NodeJS.ErrnoException).code === 'EACCES') {
        throw new PDFPermissionDeniedError(filePath);
      }

      // Generic file system error
      throw new PDFFileSystemError('read', filePath, error as Error);
    }
  }

  /**
   * Extract text from a PDF buffer
   *
   * @param buffer - PDF file buffer
   * @param options - Optional extraction options
   * @returns Extraction result containing text and metadata
   * @throws Error if PDF parsing fails
   */
  async extractFromBuffer(
    buffer: Buffer,
    options?: PDFExtractionOptions
  ): Promise<PDFExtractionResult> {
    try {
      // Validate buffer
      if (!Buffer.isBuffer(buffer)) {
        throw new PDFInvalidInputError('expected a Buffer');
      }

      if (buffer.length === 0) {
        throw new PDFInvalidInputError('buffer is empty');
      }

      // Check minimum size (valid PDFs must be at least a few bytes)
      if (buffer.length < 10) {
        throw new PDFInvalidInputError(`buffer too small (${buffer.length} bytes), minimum 10 bytes required`);
      }

      // Check for PDF signature
      const pdfSignature = buffer.toString('utf8', 0, 5);
      if (!pdfSignature.startsWith('%PDF-')) {
        const actualHeader = buffer.toString('utf8', 0, Math.min(20, buffer.length));
        throw new PDFInvalidFormatError({
          expectedSignature: '%PDF-',
          actualHeader: actualHeader.replace(/[^\x20-\x7E]/g, '?'), // Show printable chars only
          bufferSize: buffer.length
        });
      }

      // Detect corrupted PDF by checking EOF marker
      const lastBytes = buffer.slice(-10).toString('utf8');
      if (!lastBytes.includes('%%EOF')) {
        throw new PDFCorruptedError(
          'missing EOF marker - file may be truncated or corrupted',
          {
            bufferSize: buffer.length,
            lastBytes: lastBytes.replace(/[^\x20-\x7E]/g, '?')
          }
        );
      }

      // Configure pdf-parse options
      const parseOptions: any = {};

      if (options?.maxPages) {
        parseOptions.max = options.maxPages;
      }

      if (options?.pageRange) {
        // pdf-parse doesn't directly support page ranges, but we can limit via max
        parseOptions.max = options.pageRange.end;
      }

      // Parse PDF
      const data = await pdfParse(buffer, parseOptions);

      // Extract and clean text
      const extractedText = data.text || '';

      // Detect if PDF is scanned (minimal text content)
      const avgCharsPerPage = extractedText.length / (data.numpages || 1);
      if (avgCharsPerPage < 50 && extractedText.trim().length < 100) {
        throw new PDFScannedError(data.numpages, avgCharsPerPage);
      }

      return {
        text: extractedText,
        numPages: data.numpages,
        info: data.info,
        metadata: data.metadata,
      };
    } catch (error) {
      // Re-throw custom errors
      if (error instanceof PDFInvalidInputError ||
          error instanceof PDFInvalidFormatError ||
          error instanceof PDFCorruptedError ||
          error instanceof PDFScannedError) {
        throw error;
      }

      // Check for encryption errors
      const errorMessage = (error as Error).message || '';
      if (errorMessage.toLowerCase().includes('encrypt') ||
          errorMessage.toLowerCase().includes('password')) {
        throw new PDFEncryptedError();
      }

      // Check for corruption indicators
      if (errorMessage.includes('Invalid') ||
          errorMessage.includes('corrupt') ||
          errorMessage.includes('malformed') ||
          errorMessage.includes('damaged')) {
        throw new PDFCorruptedError(errorMessage, {
          originalError: errorMessage
        });
      }

      // Generic parsing error
      throw new PDFParsingError(error as Error);
    }
  }

  /**
   * Validate if a file is a valid PDF
   *
   * @param filePath - Path to the file to validate
   * @returns true if file is a valid PDF, false otherwise
   */
  async isValidPDF(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      const buffer = await fs.readFile(filePath);

      // Check minimum size (PDFs should be at least a few bytes)
      if (buffer.length < 10) {
        return false;
      }

      // Check PDF signature
      const pdfSignature = buffer.toString('utf8', 0, 5);
      return pdfSignature.startsWith('%PDF-');
    } catch (error) {
      return false;
    }
  }

  /**
   * Extract text and detect if PDF is likely scanned (image-based)
   *
   * @param filePath - Path to the PDF file
   * @returns Object containing text and flag indicating if PDF appears to be scanned
   * @throws PDFScannedError if PDF has minimal extractable text (likely scanned)
   */
  async extractAndDetectScanned(
    filePath: string
  ): Promise<{ text: string; isScanned: boolean; numPages: number; avgCharsPerPage: number }> {
    try {
      const result = await this.extractFromFile(filePath);

      // Heuristic: if text is very short relative to page count, likely scanned
      const avgCharsPerPage = result.text.length / result.numPages;
      const isScanned = avgCharsPerPage < 100; // Threshold: less than 100 chars per page

      return {
        text: result.text,
        isScanned,
        numPages: result.numPages,
        avgCharsPerPage,
      };
    } catch (error) {
      // If it's already a scanned error, add file path context
      if (error instanceof PDFScannedError) {
        throw new PDFScannedError(
          (error.details as any).numPages,
          (error.details as any).avgCharsPerPage
        );
      }
      throw error;
    }
  }

  /**
   * Get PDF metadata without extracting full text (faster)
   *
   * @param filePath - Path to the PDF file
   * @returns PDF metadata including page count
   * @throws PDFNotFoundError if file doesn't exist
   * @throws PDFPermissionDeniedError if permission is denied
   * @throws PDFParsingError if metadata extraction fails
   */
  async getMetadata(filePath: string): Promise<{
    numPages: number;
    info?: any;
    metadata?: any;
  }> {
    try {
      await fs.access(filePath);
      const dataBuffer = await fs.readFile(filePath);

      // Parse with max: 0 to avoid extracting text
      const data = await pdfParse(dataBuffer, { max: 0 });

      return {
        numPages: data.numpages,
        info: data.info,
        metadata: data.metadata,
      };
    } catch (error) {
      // Handle file system errors
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new PDFNotFoundError(filePath);
      }
      if ((error as NodeJS.ErrnoException).code === 'EACCES') {
        throw new PDFPermissionDeniedError(filePath);
      }

      // Generic parsing error
      throw new PDFParsingError(error as Error);
    }
  }
}

export default PDFExtractorService;
