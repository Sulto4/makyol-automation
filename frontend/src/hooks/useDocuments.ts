import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query';
import { listDocuments, getDocument, getDocumentStats, clearAllDocuments } from '../api/documents';
import type { ClearAllResponse } from '../types';

/**
 * Fetch all documents for client-side pagination / filtering
 */
export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
  });
}

/**
 * Fetch a single document with its extraction data
 */
export function useDocument(id: number) {
  return useQuery({
    queryKey: ['documents', id],
    queryFn: () => getDocument(id),
    enabled: id > 0,
  });
}

/**
 * Batch-fetch details for visible page rows (e.g. in a table).
 * Uses useQueries so each row's detail is cached independently.
 */
export function useDocumentDetails(ids: number[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: ['documents', id],
      queryFn: () => getDocument(id),
      enabled: id > 0,
      staleTime: 5 * 60 * 1000,
    })),
  });
}

/**
 * Fetch aggregated document and extraction statistics
 */
export function useDocumentStats() {
  return useQuery({
    queryKey: ['document-stats'],
    queryFn: getDocumentStats,
  });
}

/**
 * Mutation to clear all documents and associated data.
 * Invalidates both documents list and stats on success.
 */
export function useClearDocuments() {
  const queryClient = useQueryClient();

  return useMutation<ClearAllResponse, Error, void>({
    mutationFn: clearAllDocuments,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['document-stats'] });
    },
  });
}
