/**
 * Processing status for documents
 */
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * Review status — actual backend values
 */
export type ReviewStatus = 'OK' | 'REVIEW' | 'NEEDS_CHECK';

/**
 * Classification method — actual backend values
 */
export type ClassificationMethod =
  | 'filename_regex'
  | 'text_rules'
  | 'ai'
  | 'text_override'
  | 'vision';

/**
 * Extraction status
 */
export type ExtractionStatus = 'pending' | 'success' | 'partial' | 'failed';

/**
 * Document category — the 14 classification categories
 */
export type DocumentCategory =
  | 'ISO'
  | 'CE'
  | 'FISA_TEHNICA'
  | 'DECLARATIE_PERFORMANTA'
  | 'DECLARATIE_CONFORMITATE'
  | 'CERTIFICAT_CONSTANTA'
  | 'AVIZ_SANITAR'
  | 'RAPORT_INCERCARE'
  | 'CERTIFICAT_CALITATE'
  | 'PROCES_VERBAL'
  | 'AGREMENTARE_TEHNICA'
  | 'BULETIN_ANALIZA'
  | 'CERTIFICAT_GARANTIE'
  | 'UNKNOWN';

/**
 * Document interface matching the documents table schema
 */
export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  processing_status: ProcessingStatus;
  categorie: DocumentCategory | string | null;
  confidence: number | null;
  metoda_clasificare: ClassificationMethod | null;
  review_status: ReviewStatus | null;
  error_message: string | null;
  uploaded_at: string;
  processing_started_at: string | null;
  processing_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * Certificate metadata interface
 */
export interface CertificateMetadata {
  certificate_number?: string;
  issuing_organization?: string;
  issue_date?: string;
  expiry_date?: string;
  certified_company?: string;
  certification_scope?: string;
  [key: string]: unknown;
}

/**
 * Error details interface
 */
export interface ErrorDetails {
  message: string;
  code?: string;
  timestamp?: string;
  [key: string]: unknown;
}

/**
 * Extraction result interface matching the extraction_results table schema
 */
export interface ExtractionResult {
  id: number;
  document_id: number;
  extracted_text: string | null;
  material: string | null;
  data_expirare: string | null;
  companie: string | null;
  producator: string | null;
  distribuitor: string | null;
  adresa_producator: string | null;
  metadata: CertificateMetadata;
  confidence_score: number | null;
  extraction_status: ExtractionStatus;
  extraction_model: string | null;
  error_details: ErrorDetails | null;
  created_at: string;
  updated_at: string;
}

/**
 * Combined document with extraction data (from GET /api/documents/:id)
 */
export interface DocumentWithExtraction {
  document: Document;
  extraction: ExtractionResult | null;
}

/**
 * Documents list response (from GET /api/documents)
 */
export interface DocumentsListResponse {
  documents: Document[];
}

/**
 * Upload response (from POST /api/documents)
 */
export interface UploadResponse {
  document: Document;
  extraction: ExtractionResult;
}

/**
 * API error response
 */
export interface ApiErrorResponse {
  error: string;
  code?: string;
  details?: string;
}
