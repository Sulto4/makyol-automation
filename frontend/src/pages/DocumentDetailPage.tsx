import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { useDocument } from '../hooks/useDocuments';
import DocumentDetail from '../components/documents/DocumentDetail';
import LoadingSpinner from '../components/shared/LoadingSpinner';

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const documentId = Number(id) || 0;
  const { data, isLoading, isError, error } = useDocument(documentId);

  return (
    <div className="flex h-full flex-col gap-4 p-6">
      <div className="flex items-center gap-3">
        <Link
          to="/documents"
          className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"
        >
          <ArrowLeft className="h-4 w-4" />
          Înapoi la documente
        </Link>
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
          <p className="text-sm text-gray-500">
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
