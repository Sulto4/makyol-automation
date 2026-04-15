import * as fs from 'fs/promises';
import * as path from 'path';

/**
 * Pipeline processing response interface
 */
export interface PipelineExtractionData {
  material?: string | null;
  data_expirare?: string | null;
  companie?: string | null;
  producator?: string | null;
  distribuitor?: string | null;
  adresa_producator?: string | null;
  extraction_model?: string | null;
  [key: string]: string | null | undefined;
}

export interface PipelineResponse {
  filename: string;
  classification: string | null;
  confidence: number;
  method: string | null;
  extraction: PipelineExtractionData;
  review_status: string;
  used_vision: boolean;
  error: string | null;
}

/**
 * Pipeline health check response interface
 */
export interface PipelineHealthResponse {
  status: string;
  version?: string;
  uptime?: number;
}

/**
 * Pipeline client options
 */
export interface PipelineClientOptions {
  baseUrl?: string;
  defaultTimeoutMs?: number;
  largeFileTimeoutMs?: number;
  largeFileSizeBytes?: number;
}

/**
 * Base error class for pipeline client errors
 */
export class PipelineError extends Error {
  public readonly code: string;
  public readonly details?: unknown;

  constructor(message: string, code: string, details?: unknown) {
    super(message);
    this.name = this.constructor.name;
    this.code = code;
    this.details = details;
    Error.captureStackTrace(this, this.constructor);
  }

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
 * Error thrown when the pipeline service is unreachable
 */
export class PipelineConnectionError extends PipelineError {
  constructor(baseUrl: string, originalError: Error) {
    super(
      `Failed to connect to pipeline service at ${baseUrl}: ${originalError.message}`,
      'PIPELINE_CONNECTION_ERROR',
      { baseUrl, originalError: originalError.message }
    );
  }
}

/**
 * Error thrown when the pipeline request times out
 */
export class PipelineTimeoutError extends PipelineError {
  constructor(timeoutMs: number) {
    super(
      `Pipeline request timed out after ${timeoutMs}ms`,
      'PIPELINE_TIMEOUT_ERROR',
      { timeoutMs }
    );
  }
}

/**
 * Error thrown when the pipeline returns an error response
 */
export class PipelineProcessingError extends PipelineError {
  constructor(statusCode: number, message: string) {
    super(
      `Pipeline processing failed (HTTP ${statusCode}): ${message}`,
      'PIPELINE_PROCESSING_ERROR',
      { statusCode }
    );
  }
}

/**
 * Pipeline Client Service
 *
 * HTTP client for communicating with the Python document processing pipeline.
 * Sends PDF files for processing and retrieves structured extraction results.
 */
export class PipelineClientService {
  private readonly baseUrl: string;
  private readonly defaultTimeoutMs: number;
  private readonly largeFileTimeoutMs: number;
  private readonly largeFileSizeBytes: number;

  constructor(options?: PipelineClientOptions) {
    this.baseUrl = options?.baseUrl || process.env.PIPELINE_URL || 'http://localhost:8001';
    this.defaultTimeoutMs = options?.defaultTimeoutMs || 60_000;
    this.largeFileTimeoutMs = options?.largeFileTimeoutMs || 180_000;
    this.largeFileSizeBytes = options?.largeFileSizeBytes || 5 * 1024 * 1024; // 5MB
  }

  /**
   * Process a document through the Python pipeline
   *
   * @param filePath - Path to the PDF file to process
   * @returns Pipeline processing response with extracted data
   * @throws PipelineConnectionError if the service is unreachable
   * @throws PipelineTimeoutError if the request times out
   * @throws PipelineProcessingError if the pipeline returns an error
   */
  async processDocument(filePath: string, originalFilename?: string): Promise<PipelineResponse> {
    const absolutePath = path.resolve(filePath);

    // Verify file exists
    const stat = await fs.stat(absolutePath).catch((error: NodeJS.ErrnoException) => {
      throw new PipelineError(
        `File not found: ${absolutePath}`,
        'PIPELINE_FILE_NOT_FOUND',
        { filePath: absolutePath, originalError: error.message }
      );
    });

    // Select timeout based on file size
    const timeoutMs = stat.size > this.largeFileSizeBytes
      ? this.largeFileTimeoutMs
      : this.defaultTimeoutMs;

    // Read file and build multipart form data
    const fileBuffer = await fs.readFile(absolutePath);
    // Use original filename for classification (multer sanitizes names with hashes)
    const fileName = originalFilename || path.basename(absolutePath);

    const formData = new FormData();
    formData.append('file', new Blob([fileBuffer]), fileName);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/api/pipeline/process`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text().catch(() => 'Unknown error');
        throw new PipelineProcessingError(response.status, errorBody);
      }

      const data = await response.json() as PipelineResponse;
      return data;
    } catch (error) {
      if (error instanceof PipelineError) {
        throw error;
      }

      if ((error as Error).name === 'AbortError') {
        throw new PipelineTimeoutError(timeoutMs);
      }

      throw new PipelineConnectionError(this.baseUrl, error as Error);
    } finally {
      clearTimeout(timeoutId);
    }
  }

  /**
   * Check the health of the pipeline service
   *
   * @returns Health check response
   * @throws PipelineConnectionError if the service is unreachable
   * @throws PipelineTimeoutError if the request times out
   */
  async checkHealth(): Promise<PipelineHealthResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/api/pipeline/health`, {
        method: 'GET',
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text().catch(() => 'Unknown error');
        throw new PipelineProcessingError(response.status, errorBody);
      }

      const data = await response.json() as PipelineHealthResponse;
      return data;
    } catch (error) {
      if (error instanceof PipelineError) {
        throw error;
      }

      if ((error as Error).name === 'AbortError') {
        throw new PipelineTimeoutError(this.defaultTimeoutMs);
      }

      throw new PipelineConnectionError(this.baseUrl, error as Error);
    } finally {
      clearTimeout(timeoutId);
    }
  }
}
