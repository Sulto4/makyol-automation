import { useState, useMemo, useCallback } from 'react';
import { useDocuments, useDocumentDetails } from '../hooks/useDocuments';
import DocumentsTable, {
  type SortField,
  type SortDirection,
} from '../components/documents/DocumentsTable';
import Pagination from '../components/shared/Pagination';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import EmptyState from '../components/shared/EmptyState';
import type { Document, ExtractionResult } from '../types';

type AlertTab =
  | 'expirate'
  | 'expira_curand'
  | 'esuate'
  | 'confidence_scazut'
  | 'necesita_review';

interface TabConfig {
  key: AlertTab;
  label: string;
  filter: (doc: Document, extraction?: ExtractionResult) => boolean;
}

const TAB_CONFIGS: TabConfig[] = [
  {
    key: 'expirate',
    label: 'Expirate',
    filter: (_doc, extraction) => {
      if (!extraction?.data_expirare) return false;
      return new Date(extraction.data_expirare) < new Date();
    },
  },
  {
    key: 'expira_curand',
    label: 'Expiră curând',
    filter: (_doc, extraction) => {
      if (!extraction?.data_expirare) return false;
      const expDate = new Date(extraction.data_expirare);
      const today = new Date();
      const in30Days = new Date();
      in30Days.setDate(in30Days.getDate() + 30);
      return expDate > today && expDate < in30Days;
    },
  },
  {
    key: 'esuate',
    label: 'Eșuate',
    filter: (doc) => doc.processing_status === 'failed',
  },
  {
    key: 'confidence_scazut',
    label: 'Confidence scăzut',
    filter: (doc) => doc.confidence !== null && doc.confidence < 0.7,
  },
  {
    key: 'necesita_review',
    label: 'Necesită review',
    filter: (doc) =>
      doc.review_status === 'NEEDS_CHECK' || doc.review_status === 'REVIEW',
  },
];

export default function AlertsPage() {
  const { data, isLoading, isError, error } = useDocuments();
  const [activeTab, setActiveTab] = useState<AlertTab>('expirate');
  const [sortField, setSortField] = useState<SortField>('uploaded_at');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [perPage, setPerPage] = useState(20);

  const allDocuments = useMemo(() => data?.documents ?? [], [data]);

  // Fetch extraction details for all documents to enable expiration filtering
  const allIds = useMemo(() => allDocuments.map((d) => d.id), [allDocuments]);
  const detailQueries = useDocumentDetails(allIds);

  const extractionsMap = useMemo(() => {
    const map = new Map<number, ExtractionResult>();
    detailQueries.forEach((q) => {
      if (q.data?.extraction) {
        map.set(q.data.document.id, q.data.extraction);
      }
    });
    return map;
  }, [detailQueries]);

  // Compute counts for each tab
  const tabCounts = useMemo(() => {
    const counts: Record<AlertTab, number> = {
      expirate: 0,
      expira_curand: 0,
      esuate: 0,
      confidence_scazut: 0,
      necesita_review: 0,
    };
    for (const doc of allDocuments) {
      const extraction = extractionsMap.get(doc.id);
      for (const tab of TAB_CONFIGS) {
        if (tab.filter(doc, extraction)) {
          counts[tab.key]++;
        }
      }
    }
    return counts;
  }, [allDocuments, extractionsMap]);

  // Filter documents for active tab
  const activeConfig = TAB_CONFIGS.find((t) => t.key === activeTab)!;
  const filteredDocuments = useMemo(() => {
    return allDocuments.filter((doc) =>
      activeConfig.filter(doc, extractionsMap.get(doc.id))
    );
  }, [allDocuments, activeConfig, extractionsMap]);

  // Sorting
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
        case 'data_expirare': {
          const aExt = extractionsMap.get(a.id);
          const bExt = extractionsMap.get(b.id);
          aVal = aExt?.data_expirare ?? null;
          bVal = bExt?.data_expirare ?? null;
          break;
        }
        case 'uploaded_at':
        default:
          aVal = a.uploaded_at;
          bVal = b.uploaded_at;
      }

      if (aVal === null && bVal === null) return 0;
      if (aVal === null) return 1;
      if (bVal === null) return -1;
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    // For "expirate" tab, sort by data_expirare desc (most recent first) by default
    if (activeTab === 'expirate' && sortField === 'uploaded_at') {
      sorted.sort((a, b) => {
        const aExp = extractionsMap.get(a.id)?.data_expirare ?? '';
        const bExp = extractionsMap.get(b.id)?.data_expirare ?? '';
        return bExp.localeCompare(aExp);
      });
    }

    return sorted;
  }, [filteredDocuments, sortField, sortDirection, activeTab, extractionsMap]);

  // Pagination
  const paginatedDocuments = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    return sortedDocuments.slice(start, start + perPage);
  }, [sortedDocuments, currentPage, perPage]);

  // Extractions for visible rows
  const visibleExtractions = useMemo(() => {
    const map = new Map<number, ExtractionResult>();
    for (const doc of paginatedDocuments) {
      const ext = extractionsMap.get(doc.id);
      if (ext) map.set(doc.id, ext);
    }
    return map;
  }, [paginatedDocuments, extractionsMap]);

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

  const handleTabChange = useCallback((tab: AlertTab) => {
    setActiveTab(tab);
    setCurrentPage(1);
  }, []);

  if (isLoading) {
    return (
      <div className="p-6">
        <LoadingSpinner size="lg" text="Se încarcă alertele..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-6">
        <EmptyState
          message="Eroare la încărcarea alertelor"
          description={error instanceof Error ? error.message : 'Eroare necunoscută'}
          icon="alert"
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 p-6">
      <h1 className="text-2xl font-bold text-gray-900">Alerte</h1>

      {/* Tab navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-4" aria-label="Tabs">
          {TAB_CONFIGS.map((tab) => {
            const isActive = activeTab === tab.key;
            const count = tabCounts[tab.key];
            return (
              <button
                key={tab.key}
                onClick={() => handleTabChange(tab.key)}
                className={`inline-flex items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium whitespace-nowrap ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab.label}
                <span
                  className={`inline-flex min-w-[1.25rem] items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold ${
                    isActive
                      ? 'bg-blue-100 text-blue-600'
                      : 'bg-gray-100 text-gray-600'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Content */}
      {filteredDocuments.length === 0 ? (
        <EmptyState
          message="Nicio alertă"
          description="Nu există documente care necesită atenție în această categorie."
          icon="search"
        />
      ) : (
        <>
          <DocumentsTable
            documents={paginatedDocuments}
            extractions={visibleExtractions}
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
    </div>
  );
}
