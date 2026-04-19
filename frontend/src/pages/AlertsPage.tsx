import { useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useDocuments, useDocumentDetails } from '../hooks/useDocuments';
import DocumentsTable, {
  type SortField,
  type SortDirection,
} from '../components/documents/DocumentsTable';
import Pagination from '../components/shared/Pagination';
import LoadingSpinner from '../components/shared/LoadingSpinner';
import EmptyState from '../components/shared/EmptyState';
import ProcessingBanner from '../components/shared/ProcessingBanner';
import { parseDataExpirare, isExpired, isExpiringSoon } from '../utils/dates';
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
  filter: (doc: Document) => boolean;
}

const TAB_CONFIGS: TabConfig[] = [
  {
    key: 'expirate',
    label: 'Expirate',
    filter: (doc) => isExpired(parseDataExpirare(doc.data_expirare ?? null)),
  },
  {
    key: 'expira_curand',
    label: 'Expiră curând',
    filter: (doc) => isExpiringSoon(parseDataExpirare(doc.data_expirare ?? null), 30),
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

const VALID_TABS = new Set<AlertTab>(TAB_CONFIGS.map((t) => t.key));
const DEFAULT_TAB: AlertTab = 'expirate';
const DEFAULT_SORT_FIELD: SortField = 'uploaded_at';
const DEFAULT_SORT_DIR: SortDirection = 'desc';
const DEFAULT_PER_PAGE = 20;

export default function AlertsPage() {
  const { data, isLoading, isError, error } = useDocuments();
  const [searchParams, setSearchParams] = useSearchParams();

  const activeTab: AlertTab = (() => {
    const t = searchParams.get('tab') as AlertTab | null;
    return t && VALID_TABS.has(t) ? t : DEFAULT_TAB;
  })();
  const sortField = (searchParams.get('sort') as SortField) || DEFAULT_SORT_FIELD;
  const sortDirection: SortDirection =
    searchParams.get('dir') === 'asc' ? 'asc' : DEFAULT_SORT_DIR;
  const currentPage = Math.max(1, Number(searchParams.get('page')) || 1);
  const perPage = Math.max(1, Number(searchParams.get('per')) || DEFAULT_PER_PAGE);

  // Helper that merges param updates while keeping the URL clean (drop defaults)
  const updateParams = useCallback(
    (next: Partial<Record<'tab' | 'sort' | 'dir' | 'page' | 'per', string>>) => {
      setSearchParams(
        (prev) => {
          const merged = new URLSearchParams(prev);
          for (const [k, v] of Object.entries(next)) {
            if (v == null) merged.delete(k);
            else merged.set(k, v);
          }
          // Drop defaults so URLs stay tidy
          if (merged.get('tab') === DEFAULT_TAB) merged.delete('tab');
          if (merged.get('sort') === DEFAULT_SORT_FIELD) merged.delete('sort');
          if (merged.get('dir') === DEFAULT_SORT_DIR) merged.delete('dir');
          if (merged.get('page') === '1') merged.delete('page');
          if (merged.get('per') === String(DEFAULT_PER_PAGE)) merged.delete('per');
          return merged;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  const allDocuments = useMemo(() => data?.documents ?? [], [data]);

  // Compute counts for each tab — all filters read only from Document fields
  // (including data_expirare joined into the list response), so no N+1 fetch.
  const tabCounts = useMemo(() => {
    const counts: Record<AlertTab, number> = {
      expirate: 0,
      expira_curand: 0,
      esuate: 0,
      confidence_scazut: 0,
      necesita_review: 0,
    };
    for (const doc of allDocuments) {
      for (const tab of TAB_CONFIGS) {
        if (tab.filter(doc)) {
          counts[tab.key]++;
        }
      }
    }
    return counts;
  }, [allDocuments]);

  // Filter documents for active tab
  const activeConfig = TAB_CONFIGS.find((t) => t.key === activeTab)!;
  const filteredDocuments = useMemo(() => {
    return allDocuments.filter((doc) => activeConfig.filter(doc));
  }, [allDocuments, activeConfig]);

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
          aVal = parseDataExpirare(a.data_expirare ?? null)?.getTime() ?? null;
          bVal = parseDataExpirare(b.data_expirare ?? null)?.getTime() ?? null;
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
        const aExp = parseDataExpirare(a.data_expirare ?? null)?.getTime() ?? 0;
        const bExp = parseDataExpirare(b.data_expirare ?? null)?.getTime() ?? 0;
        return bExp - aExp;
      });
    }

    return sorted;
  }, [filteredDocuments, sortField, sortDirection, activeTab]);

  // Pagination
  const paginatedDocuments = useMemo(() => {
    const start = (currentPage - 1) * perPage;
    return sortedDocuments.slice(start, start + perPage);
  }, [sortedDocuments, currentPage, perPage]);

  // Store sorted document IDs for prev/next navigation in detail view
  useMemo(() => {
    const ids = sortedDocuments.map((d) => d.id);
    sessionStorage.setItem('docNavIds', JSON.stringify(ids));
  }, [sortedDocuments]);

  // Extraction details only for the paginated rows — avoids N+1 fan-out across
  // the whole list while keeping material/companie/producator visible in the table.
  const visibleIds = useMemo(
    () => paginatedDocuments.map((d) => d.id),
    [paginatedDocuments],
  );
  const detailQueries = useDocumentDetails(visibleIds);

  const visibleExtractions = useMemo(() => {
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
        updateParams({ dir: sortDirection === 'asc' ? 'desc' : 'asc' });
      } else {
        updateParams({ sort: field, dir: 'asc' });
      }
    },
    [sortField, sortDirection, updateParams],
  );

  const handleTabChange = useCallback(
    (tab: AlertTab) => {
      updateParams({ tab, page: '1' });
    },
    [updateParams],
  );

  const handlePageChange = useCallback(
    (page: number) => {
      updateParams({ page: String(page) });
    },
    [updateParams],
  );

  const handlePerPageChange = useCallback(
    (per: number) => {
      updateParams({ per: String(per), page: '1' });
    },
    [updateParams],
  );

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
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Alerte</h1>

      <ProcessingBanner documents={allDocuments} />

      {/* Tab navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
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
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300 dark:hover:border-gray-600'
                }`}
              >
                {tab.label}
                <span
                  className={`inline-flex min-w-[1.25rem] items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold ${
                    isActive
                      ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
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
            onPageChange={handlePageChange}
            onPerPageChange={handlePerPageChange}
          />
        </>
      )}
    </div>
  );
}
