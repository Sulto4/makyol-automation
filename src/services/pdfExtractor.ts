import * as fs from 'fs/promises';
import * as path from 'path';
import pdfParse from 'pdf-parse';

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
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') {
        throw new Error(`PDF file not found: ${filePath}`);
      }
      if ((error as NodeJS.ErrnoException).code === 'EACCES') {
        throw new Error(`Permission denied reading PDF file: ${filePath}`);
      }
      throw new Error(`Failed to read PDF file: ${(error as Error).message}`);
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
        throw new Error('Invalid input: expected a Buffer');
      }

      if (buffer.length === 0) {
        throw new Error('Invalid input: buffer is empty');
      }

      // Check for PDF signature
      const pdfSignature = buffer.toString('utf8', 0, 5);
      if (!pdfSignature.startsWith('%PDF-')) {
        throw new Error('Invalid PDF: file does not have PDF signature');
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

      return {
        text: extractedText,
        numPages: data.numpages,
        info: data.info,
        metadata: data.metadata,
      };
    } catch (error) {
      // Check for specific PDF parsing errors
      if ((error as Error).message.includes('Invalid PDF')) {
        throw error;
      }

      if ((error as Error).message.includes('encrypted')) {
        throw new Error('PDF is encrypted and cannot be processed');
      }

      if ((error as Error).message.includes('Invalid input')) {
        throw error;
      }

      throw new Error(`PDF parsing failed: ${(error as Error).message}`);
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
   */
  async extractAndDetectScanned(
    filePath: string
  ): Promise<{ text: string; isScanned: boolean; numPages: number }> {
    const result = await this.extractFromFile(filePath);

    // Heuristic: if text is very short relative to page count, likely scanned
    const avgCharsPerPage = result.text.length / result.numPages;
    const isScanned = avgCharsPerPage < 100; // Threshold: less than 100 chars per page

    return {
      text: result.text,
      isScanned,
      numPages: result.numPages,
    };
  }

  /**
   * Get PDF metadata without extracting full text (faster)
   *
   * @param filePath - Path to the PDF file
   * @returns PDF metadata including page count
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
      throw new Error(`Failed to get PDF metadata: ${(error as Error).message}`);
    }
  }
}

export default PDFExtractorService;
