import apiClient from './client';
import type {
  DocumentsListResponse,
  DocumentWithExtraction,
  UploadResponse,
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
