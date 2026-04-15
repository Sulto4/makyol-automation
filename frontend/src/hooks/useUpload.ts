import { useState, useCallback, useRef } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadDocument, uploadFolderFiles, downloadArchive as downloadArchiveApi } from '../api/documents';
import type { UploadResponse, FolderUploadResponse } from '../types';

/**
 * Upload mutation with Axios progress tracking.
 * Returns `progress` (0–100) alongside standard mutation state.
 */
export function useUpload() {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);

  const mutation = useMutation<UploadResponse, Error, File>({
    mutationFn: (file: File) => uploadDocument(file, setProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      setProgress(0);
    },
    onError: () => {
      setProgress(0);
    },
  });

  return { ...mutation, progress };
}

/**
 * Folder upload mutation with Axios progress tracking.
 * Manages the full folder upload lifecycle including ZIP download.
 * Returns `progress` (0–100) and `downloadArchive` alongside standard mutation state.
 */
export function useFolderUpload() {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);
  const resultsRef = useRef<FolderUploadResponse | null>(null);

  const mutation = useMutation<
    FolderUploadResponse,
    Error,
    { file: File; relativePath: string }[]
  >({
    mutationFn: (files) => uploadFolderFiles(files, setProgress),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      resultsRef.current = data;
      setProgress(0);
    },
    onError: () => {
      setProgress(0);
    },
  });

  const downloadArchive = useCallback(async () => {
    const data = resultsRef.current ?? mutation.data;
    if (!data) return;

    const documents = data.results
      .filter((r) => r.success && r.document)
      .map((r) => ({ id: r.document!.id, relativePath: r.relativePath ?? '' }));

    if (documents.length === 0) return;

    await downloadArchiveApi({
      documents,
      folderName: 'documents',
    });
  }, [mutation.data]);

  return { ...mutation, progress, downloadArchive };
}
