/**
 * Base error class for PDF extraction errors
 */
export class PDFExtractionError extends Error {
  public readonly code: string;
  public readonly details?: any;

  constructor(message: string, code: string, details?: any) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.details = details;
    Error.captureStackTrace(this, this.constructor);
  }

  /**
   * Convert error to JSON format for API responses
   */
  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      details: this.details,
    };
  }
}

/**
 * Error thrown when PDF file is not found
 */
export class PDFNotFoundError extends PDFExtractionError {
  constructor(filePath: string) {
    super(
      `PDF file not found: ${filePath}`,
      'PDF_NOT_FOUND',
      { filePath }
    );
  }
}

/**
 * Error thrown when permission is denied for reading PDF file
 */
export class PDFPermissionDeniedError extends PDFExtractionError {
  constructor(filePath: string) {
    super(
      `Permission denied reading PDF file: ${filePath}`,
      'PDF_PERMISSION_DENIED',
      { filePath }
    );
  }
}

/**
 * Error thrown when PDF file is corrupted or invalid
 */
export class PDFCorruptedError extends PDFExtractionError {
  constructor(reason: string, details?: any) {
    super(
      `PDF file is corrupted or invalid: ${reason}`,
      'PDF_CORRUPTED',
      { reason, ...details }
    );
  }
}

/**
 * Error thrown when PDF file is encrypted
 */
export class PDFEncryptedError extends PDFExtractionError {
  constructor(message: string = 'PDF is password-protected and cannot be processed without the password') {
    super(
      message,
      'PDF_ENCRYPTED',
      { requiresPassword: true }
    );
  }
}

/**
 * Error thrown when PDF is scanned (image-based) and contains no extractable text
 */
export class PDFScannedError extends PDFExtractionError {
  constructor(numPages: number, avgCharsPerPage: number) {
    super(
      `PDF appears to be scanned (image-based) with minimal extractable text. ` +
      `Average ${avgCharsPerPage.toFixed(0)} characters per page across ${numPages} pages. ` +
      `OCR processing may be required.`,
      'PDF_SCANNED',
      {
        numPages,
        avgCharsPerPage,
        requiresOCR: true,
        suggestion: 'Use OCR (Optical Character Recognition) to extract text from scanned images'
      }
    );
  }
}

/**
 * Error thrown when PDF has invalid signature or format
 */
export class PDFInvalidFormatError extends PDFExtractionError {
  constructor(details?: any) {
    super(
      'File does not have a valid PDF signature or format',
      'PDF_INVALID_FORMAT',
      details
    );
  }
}

/**
 * Error thrown when buffer/input is invalid
 */
export class PDFInvalidInputError extends PDFExtractionError {
  constructor(reason: string) {
    super(
      `Invalid input: ${reason}`,
      'PDF_INVALID_INPUT',
      { reason }
    );
  }
}

/**
 * Error thrown when PDF parsing fails for unknown reasons
 */
export class PDFParsingError extends PDFExtractionError {
  constructor(originalError: Error) {
    super(
      `PDF parsing failed: ${originalError.message}`,
      'PDF_PARSING_FAILED',
      {
        originalError: originalError.message,
        stack: originalError.stack
      }
    );
  }
}

/**
 * Error thrown when file system operation fails
 */
export class PDFFileSystemError extends PDFExtractionError {
  constructor(operation: string, filePath: string, originalError: Error) {
    super(
      `File system error during ${operation}: ${originalError.message}`,
      'PDF_FILESYSTEM_ERROR',
      {
        operation,
        filePath,
        originalError: originalError.message
      }
    );
  }
}
