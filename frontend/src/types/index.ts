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
  adresa_distribuitor: string | null;
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

/**
 * Setting value type - supports any JSON-serializable value
 */
export type SettingValue = string | number | boolean | object | null;

/**
 * Setting interface matching the backend settings table schema
 */
export interface Setting {
  key: string;
  value: SettingValue;
  created_at: string;
  updated_at: string;
}

/**
 * Settings list response (from GET /api/settings)
 */
export interface SettingsListResponse {
  success: true;
  data: Setting[];
  count: number;
}

/**
 * Single setting response (from GET /api/settings/:key)
 */
export interface SettingResponse {
  success: true;
  data: Setting;
}

/**
 * Update setting response (from PUT /api/settings/:key)
 */
export interface UpdateSettingResponse {
  success: true;
  data: Setting;
  message: string;
}

/**
 * Update setting input (for PUT /api/settings/:key)
 */
export interface UpdateSettingInput {
  value: SettingValue;
}

/**
 * Classification statistics from GET /api/documents/stats
 */
export interface DocumentStats {
  total_documents: number;
  completed: number;
  failed: number;
  pending: number;
  processing: number;
  by_method: Record<string, number>;
  average_confidence: number | null;
  categorie_altele: number;
}

/**
 * Extraction field fill-rate statistics from GET /api/documents/stats
 */
export interface ExtractionStats {
  total: number;
  has_companie: number;
  has_material: number;
  has_data_expirare: number;
  has_producator: number;
  has_distribuitor: number;
  has_adresa_producator: number;
  has_adresa_distribuitor: number;
}

/**
 * Combined stats response (from GET /api/documents/stats)
 */
export interface StatsResponse {
  classification: DocumentStats;
  extraction: ExtractionStats;
}

/**
 * Reprocess single document response (from POST /api/documents/:id/reprocess)
 */
export interface ReprocessResponse {
  document: Document;
  extraction: ExtractionResult;
}

/**
 * Batch reprocess response (from POST /api/documents/reprocess-all)
 */
export interface ReprocessAllResponse {
  message: string;
  jobId: string;
  total: number;
}

/**
 * Clear all documents response (from DELETE /api/documents)
 */
export interface ClearAllResponse {
  message: string;
  deleted: number;
}

/**
 * File with its relative folder path for folder upload
 */
export interface FolderUploadFile {
  file: File;
  relativePath: string;
}

/**
 * Per-file result from folder upload processing
 */
export interface FolderUploadResult {
  document: Document;
  extraction: ExtractionResult | null;
  relativePath: string;
  success: boolean;
  error?: string;
}

/**
 * Batch response from folder upload (from POST /api/documents/folder-upload)
 */
export interface FolderUploadResponse {
  results: FolderUploadResult[];
  totalProcessed: number;
  totalFailed: number;
}

/**
 * Request payload for downloading an archive with folder structure
 */
export interface ExportArchiveRequest {
  documents: { id: number; relativePath: string }[];
  folderName: string;
}
