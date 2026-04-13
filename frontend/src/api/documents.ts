import apiClient from './client';
import type {
  DocumentsListResponse,
  DocumentWithExtraction,
  UploadResponse,
  ReprocessResponse,
  ReprocessAllResponse,
  StatsResponse,
  FolderUploadResponse,
  ExportArchiveRequest,
} from '../types';

/**
 * Fetch all documents (no limit — client-side pagination)
 */
export async function listDocuments(): Promise<DocumentsListResponse> {
  const { data } = await apiClient.get<DocumentsListResponse>('/documents');
  return data;
}

/**
 * Fetch a single document with its extraction results
 */
export async function getDocument(id: number): Promise<DocumentWithExtraction> {
  const { data } = await apiClient.get<DocumentWithExtraction>(`/documents/${id}`);
  return data;
}

/**
 * Upload a PDF document with progress tracking
 *
 * @param file - The PDF file to upload
 * @param onProgress - Optional callback receiving upload percentage (0–100)
 */
export async function uploadDocument(
  file: File,
  onProgress?: (percent: number) => void,
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await apiClient.post<UploadResponse>('/documents', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress(event) {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });

  return data;
}

/**
 * Reprocess a single document through the pipeline
 */
export async function reprocessDocument(id: number): Promise<ReprocessResponse> {
  const { data } = await apiClient.post<ReprocessResponse>(`/documents/${id}/reprocess`);
  return data;
}

/**
 * Batch reprocess documents with optional filters
 */
export async function reprocessAll(
  options?: { status?: string; limit?: number },
): Promise<ReprocessAllResponse> {
  const { data } = await apiClient.post<ReprocessAllResponse>(
    '/documents/reprocess-all',
    options,
  );
  return data;
}

/**
 * Fetch aggregated document and extraction statistics
 */
export async function getDocumentStats(): Promise<StatsResponse> {
  const { data } = await apiClient.get<StatsResponse>('/documents/stats');
  return data;
}

/**
 * Upload multiple PDF files preserving folder structure
 *
 * @param files - Array of files with their relative paths
 * @param onProgress - Optional callback receiving upload percentage (0–100)
 */
export async function uploadFolderFiles(
  files: { file: File; relativePath: string }[],
  onProgress?: (percent: number) => void,
): Promise<FolderUploadResponse> {
  const formData = new FormData();
  const relativePaths: string[] = [];

  for (const entry of files) {
    formData.append('files', entry.file);
    relativePaths.push(entry.relativePath);
  }

  formData.append('relativePaths', JSON.stringify(relativePaths));

  const { data } = await apiClient.post<FolderUploadResponse>(
    '/documents/upload-folder',
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress(event) {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    },
  );

  return data;
}

/**
 * Export documents as a ZIP archive and trigger browser download
 *
 * @param request - Archive export configuration
 */
export async function downloadArchive(request: ExportArchiveRequest): Promise<void> {
  const { data } = await apiClient.post('/documents/export-archive', request, {
    responseType: 'blob',
  });

  const blob = new Blob([data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'archive.zip';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}
