import { useQuery, useQueries, useMutation, useQueryClient } from '@tanstack/react-query';
import { listDocuments, getDocument, getDocumentStats, clearAllDocuments, reviewDocument, reprocessAll } from '../api/documents';
import type { ClearAllResponse, DocumentWithExtraction, ReprocessAllResponse } from '../types';

/**
 * Fetch all documents for client-side pagination / filtering.
 * Auto-polls every 5s when any document is in pending/processing state.
 */
export function useDocuments() {
  return useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
    refetchInterval: (query) => {
      const docs = query.state.data?.documents;
      if (!docs) return false;
      const hasProcessing = docs.some(
        (d) => d.processing_status === 'pending' || d.processing_status === 'processing',
      );
      return hasProcessing ? 5000 : false;
    },
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
 * Each row auto-polls every 3s while its document is processing so
 * extraction fields appear live without a page refresh.
 */
export function useDocumentDetails(ids: number[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: ['documents', id],
      queryFn: () => getDocument(id),
      enabled: id > 0,
      staleTime: 3_000,
      refetchInterval: (query: { state: { data?: DocumentWithExtraction } }) => {
        const status = query.state.data?.document?.processing_status;
        return status === 'processing' || status === 'pending' ? 3000 : false;
      },
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

/**
 * Mutation to batch-reprocess documents through the pipeline.
 * Backend runs the work asynchronously and returns 202 immediately;
 * the documents list will auto-poll while statuses flip to processing.
 */
export function useReprocessAll() {
  const queryClient = useQueryClient();

  return useMutation<ReprocessAllResponse, Error, { status?: string; limit?: number } | undefined>({
    mutationFn: (options) => reprocessAll(options),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['document-stats'] });
    },
  });
}

/**
 * Mutation to review (approve/reject) a document.
 * Invalidates the document cache on success.
 */
export function useReviewDocument() {
  const queryClient = useQueryClient();

  return useMutation<
    DocumentWithExtraction,
    Error,
    {
      id: number;
      payload: {
        action: 'approve' | 'reject';
        rejection_reason?: 'wrong_classification' | 'wrong_extraction';
        corrected_category?: string;
        wrong_fields?: string[];
        comment?: string;
      };
    }
  >({
    mutationFn: ({ id, payload }) => reviewDocument(id, payload),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['documents', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      queryClient.invalidateQueries({ queryKey: ['document-stats'] });
    },
  });
}
