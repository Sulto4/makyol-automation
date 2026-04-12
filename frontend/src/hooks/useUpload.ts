import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadDocument } from '../api/documents';
import type { UploadResponse } from '../types';

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
