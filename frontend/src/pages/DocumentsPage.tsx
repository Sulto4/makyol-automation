import { useState, useMemo, useCallback } from 'react';
import { Download, FileSpreadsheet, Trash2, Archive } from 'lucide-react';
import toast from 'react-hot-toast';
import { useDocuments, useDocumentDetails, useClearDocuments } from '../hooks/useDocuments';
import { useFilterStore } from '../store/filterStore';
import ConfirmDialog from '../components/shared/ConfirmDialog';
import DocumentFilters from '../components/documents/DocumentFilters';
import DocumentsTable, {
  type SortField,
  type SortDirection,
} from '../components/documents/DocumentsTable';
import Pagination from '../components/shared/Pagination';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import EmptyState from '../components/shared/EmptyState';
import { exportToCSV } from '../utils/csv';
import { exportToExcel } from '../utils/excel';
import { downloadArchive } from '../api/documents';
import { getCategoryLabel } from '../utils/categories';
import type { ExtractionResult } from '../types';

export default function DocumentsPage() {
  const { data, isLoading, isError, error } = useDocuments();
  const { categories, processingStatus, reviewStatus, search } = useFilterStore();

  const [sortField, setSortField] = useState<SortField>('uploaded_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [showClearDialog, setShowClearDialog] = useState(false);

  const clearMutation = useClearDocuments();

  const allDocuments = useMemo(() => data?.documents ?? [], [data]);

  // Client-side filtering
  const filteredDocuments = useMemo(() => {
    let result = allDocuments;

    if (categories.length > 0) {
      result = result.filter((doc) =>
        categories.includes(doc.categorie as typeof categories[number])
      );
    }

    if (processingStatus) {
      result = result.filter((doc) => doc.processing_status === processingStatus);
    }

    if (reviewStatus) {
      result = result.filter((doc) => doc.review_status === reviewStatus);
    }

    if (search.trim()) {
      const q = search.toLowerCase().trim();
      result = result.filter(
        (doc) =>
          doc.original_filename.toLowerCase().includes(q) ||
          doc.filename.toLowerCase().includes(q) ||
          getCategoryLabel(doc.categorie).toLowerCase().includes(q)
      );
    }

    return result;
  }, [allDocuments, categories, processingStatus, reviewStatus, search]);

  // Client-side sorting
  const sortedDocuments = useMemo(() => {
    const sorted = [...filteredDocuments];
    sorted.sort((a, b) => {
      let aVal: string | number | null = null;
      let bVal: string | number | null = null;

      switch (sortField) {
        case 'filename':
          aVal = a.original_filename.toLowerCase();
          bVal = b.original_filename.toLowerCase();
          break;
        case 'categorie':
          aVal = getCategoryLabel(a.categorie);
          bVal = getCategoryLabel(b.categorie);
          break;
        case 'confidence':
          aVal = a.confidence ?? -1;
          bVal = b.confidence ?? -1;
          break;
        case 'processing_status':
          aVal = a.processing_status;
          bVal = b.processing_status;
          break;
        case 'review_status':
          aVal = a.review_status ?? '';
          bVal = b.review_status ?? '';
          break;
        case 'uploaded_at':
          aVal = a.uploaded_at;
          bVal = b.uploaded_at;
          break;
        default:
          // extraction fields sorted by document field fallback
          aVal = a.original_filename.toLowerCase();
          bVal = b.original_filename.toLowerCase();
      }

      if (aVal === null && bVal === null) return 0;
      if (aVal === null) return 1;
      if (bVal === null) return -1;

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [filteredDocuments, sortField, sortDirection]);

  // Pagination
  const paginatedDocuments = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    return sortedDocuments.slice(start, start + perPage);
  }, [sortedDocuments, currentPage, perPage]);

  // Reset page when filters change
  useMemo(() => {
    setCurrentPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [categories, processingStatus, reviewStatus, search]);

  // Fetch extraction data for visible rows
  const visibleIds = useMemo(
    () => paginatedDocuments.map((d) => d.id),
    [paginatedDocuments]
  );
  const detailQueries = useDocumentDetails(visibleIds);

  const extractions = useMemo(() => {
    const map = new Map<number, ExtractionResult>();
    detailQueries.forEach((q) => {
      if (q.data?.extraction) {
        map.set(q.data.document.id, q.data.extraction);
      }
    });
    return map;
  }, [detailQueries]);

  const handleSort = useCallback(
    (field: SortField) => {
      if (field === sortField) {
        setSortDirection((d) => (d === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortField(field);
        setSortDirection('asc');
      }
    },
    [sortField]
  );

  function handleExportExcel() {
    const items = sortedDocuments.map((doc) => ({
      document: doc,
      extraction: extractions.get(doc.id) ?? null,
    }));
    exportToExcel(items);
  }

  function handleClearDocuments() {
    clearMutation.mutate(undefined, {
      onSuccess: () => {
        toast.success('Toate documentele au fost șterse cu succes');
        setShowClearDialog(false);
      },
      onError: (err) => {
        toast.error(err instanceof Error ? err.message : 'Eroare la ștergerea documentelor');
        setShowClearDialog(false);
      },
    });
  }

  function handleExportCSV() {
    const items = sortedDocuments.map((doc) => ({
      document: doc,
      extraction: extractions.get(doc.id) ?? null,
    }));
    exportToCSV(items);
  }

  const [isArchiving, setIsArchiving] = useState(false);

  async function handleExportArchive() {
    const completedDocs = sortedDocuments.filter(
      (d) => d.processing_status === 'completed',
    );
    if (completedDocs.length === 0) {
      toast.error('Nu există documente finalizate pentru export');
      return;
    }
    setIsArchiving(true);
    try {
      await downloadArchive({
        documents: completedDocs.map((d) => ({
          id: d.id,
          relativePath: d.relative_path || d.original_filename,
        })),
        folderName: 'documente',
      });
      toast.success('Arhiva a fost descărcată');
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Eroare la descărcarea arhivei');
    } finally {
      setIsArchiving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <LoadingSpinner size="lg" text="Se încarcă documentele..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <EmptyState
          message="Eroare la încărcarea documentelor"
          description={error instanceof Error ? error.message : 'Eroare necunoscută'}
          icon="alert"
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Documente</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportExcel}
            disabled={sortedDocuments.length === 0}
            className="inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Export Excel
          </button>
          <button
            onClick={handleExportCSV}
            disabled={sortedDocuments.length === 0}
            className="inline-flex items-center gap-2 rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            Export CSV
          </button>
          <button
            onClick={handleExportArchive}
            disabled={sortedDocuments.length === 0 || isArchiving}
            className="inline-flex items-center gap-2 rounded-md bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Archive className="h-4 w-4" />
            {isArchiving ? 'Se descarcă...' : 'Descarcă Arhivă ZIP'}
          </button>
          <button
            onClick={() => setShowClearDialog(true)}
            disabled={allDocuments.length === 0 || clearMutation.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Trash2 className="h-4 w-4" />
            Curăță Documente
          </button>
        </div>
      </div>

      <DocumentFilters />

      {filteredDocuments.length === 0 ? (
        <EmptyState
          message="Nu s-au găsit documente"
          description="Încercați să modificați filtrele sau termenul de căutare."
          icon="search"
        />
      ) : (
        <>
          <DocumentsTable
            documents={paginatedDocuments}
            extractions={extractions}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
          <Pagination
            currentPage={currentPage}
            totalItems={sortedDocuments.length}
            perPage={perPage}
            onPageChange={setCurrentPage}
            onPerPageChange={setPerPage}
          />
        </>
      )}

      <ConfirmDialog
        isOpen={showClearDialog}
        title="Șterge toate documentele"
        message={`Această acțiune va șterge ${allDocuments.length} document(e) și datele asociate. Acțiunea este ireversibilă.`}
        confirmLabel="Șterge tot"
        cancelLabel="Anulează"
        onConfirm={handleClearDocuments}
        onCancel={() => setShowClearDialog(false)}
        variant="danger"
      />
    </div>
  );
}
