import { useQuery, useQueries } from '@tanstack/react-query';
import { listDocuments, getDocument } from '../api/documents';

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
