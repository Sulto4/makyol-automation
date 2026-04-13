import { useMemo } from 'react';
import { useDocuments, useDocumentStats } from '../hooks/useDocuments';
import SummaryCards from '../components/dashboard/SummaryCards';
import CategoryChart from '../components/dashboard/CategoryChart';
import StatusChart from '../components/dashboard/StatusChart';
import ClassificationChart from '../components/dashboard/ClassificationChart';
import ExtractionFillChart from '../components/dashboard/ExtractionFillChart';
import RecentActivity from '../components/dashboard/RecentActivity';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import EmptyState from '../components/shared/EmptyState';

export default function DashboardPage() {
  const { data, isLoading, isError, error } = useDocuments();
  const { data: statsData } = useDocumentStats();

  const documents = useMemo(() => data?.documents ?? [], [data]);

  if (isLoading) {
    return (
      <div className="p-6">
        <LoadingSpinner size="lg" text="Se încarcă datele..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <EmptyState
          message="Eroare la încărcarea datelor"
          description={error instanceof Error ? error.message : 'Eroare necunoscută'}
          icon="alert"
        />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="p-6">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Panou de Control</h1>
        <EmptyState
          message="Nu există documente"
          description="Încărcați primul document pentru a vedea statisticile."
          icon="document"
        />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Panou de Control</h1>

      <SummaryCards documents={documents} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Distribuție pe Categorii
          </h3>
          <CategoryChart documents={documents} />
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Status Procesare
          </h3>
          <StatusChart documents={documents} />
        </div>
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-900">
          Metodă Clasificare
        </h3>
        <ClassificationChart documents={documents} />
      </div>

      {statsData?.extraction && statsData.extraction.total > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Rata de Completare Extracție
          </h3>
          <ExtractionFillChart stats={statsData.extraction} />
        </div>
      )}

      <RecentActivity documents={documents} />
    </div>
  );
}
