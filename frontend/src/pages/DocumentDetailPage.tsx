import { useMemo } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
import { useDocument } from '../hooks/useDocuments';
import DocumentDetail from '../components/documents/DocumentDetail';
import LoadingSpinner from '../components/shared/LoadingSpinner';

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const documentId = Number(id) || 0;
  const { data, isLoading, isError, error } = useDocument(documentId);

  // Get prev/next document IDs from the sorted list stored by DocumentsPage
  const { prevId, nextId, currentIndex, total } = useMemo(() => {
    try {
      const raw = sessionStorage.getItem('docNavIds');
      if (!raw) return { prevId: null, nextId: null, currentIndex: -1, total: 0 };
      const ids: number[] = JSON.parse(raw);
      const idx = ids.indexOf(documentId);
      return {
        prevId: idx > 0 ? ids[idx - 1] : null,
        nextId: idx < ids.length - 1 ? ids[idx + 1] : null,
        currentIndex: idx,
        total: ids.length,
      };
    } catch {
      return { prevId: null, nextId: null, currentIndex: -1, total: 0 };
    }
  }, [documentId]);

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      {/* Navigation bar */}
      <div className="flex items-center justify-between">
        <Link
          to="/documents"
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        >
          <ArrowLeft className="h-4 w-4" />
          Înapoi la documente
        </Link>

        {total > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => prevId && navigate(`/documents/${prevId}`)}
              disabled={!prevId}
              className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <ChevronLeft className="h-4 w-4" />
              Anterior
            </button>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {currentIndex + 1} / {total}
            </span>
            <button
              onClick={() => nextId && navigate(`/documents/${nextId}`)}
              disabled={!nextId}
              className="flex items-center gap-1 rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Următor
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {isLoading && (
        <div className="flex flex-1 items-center justify-center">
          <LoadingSpinner size="lg" text="Se încarcă documentul..." />
        </div>
      )}

      {isError && (
        <div className="flex flex-1 flex-col items-center justify-center gap-3 text-red-600">
          <AlertTriangle className="h-12 w-12" />
          <p className="text-lg font-medium">Eroare la încărcarea documentului</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {error instanceof Error ? error.message : 'Eroare necunoscută'}
          </p>
          <Link
            to="/documents"
            className="mt-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          >
            Înapoi la documente
          </Link>
        </div>
      )}

      {data && (
        <div className="flex-1 min-h-0">
          <DocumentDetail data={data} />
        </div>
      )}
    </div>
  );
}
