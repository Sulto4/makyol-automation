import { useState, useRef, useEffect } from 'react';
import { Filter, ChevronDown, X } from 'lucide-react';
import { useFilterStore } from '../../store/filterStore';
import { CATEGORY_LABELS } from '../../utils/categories';
import SearchBar from '../shared/SearchBar';
import type { DocumentCategory, ProcessingStatus, ReviewStatus } from '../../types';

const ALL_CATEGORIES = Object.keys(CATEGORY_LABELS) as DocumentCategory[];

const PROCESSING_STATUS_OPTIONS: { value: ProcessingStatus; label: string }[] = [
  { value: 'pending', label: 'În așteptare' },
  { value: 'processing', label: 'În procesare' },
  { value: 'completed', label: 'Finalizat' },
  { value: 'failed', label: 'Eșuat' },
];

const REVIEW_STATUS_OPTIONS: { value: ReviewStatus; label: string }[] = [
  { value: 'OK', label: 'OK' },
  { value: 'REVIEW', label: 'De revizuit' },
  { value: 'NEEDS_CHECK', label: 'Necesită verificare' },
];

function CategoryMultiSelect() {
  const { categories, setCategories } = useFilterStore();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  function toggle(cat: DocumentCategory) {
    setCategories(
      categories.includes(cat)
        ? categories.filter((c) => c !== cat)
        : [...categories, cat]
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between rounded-md border border-gray-300 bg-white px-3 py-2 text-sm hover:border-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:hover:border-gray-500"
      >
        <span className="truncate text-gray-700 dark:text-gray-300">
          {categories.length === 0
            ? 'Toate categoriile'
            : `${categories.length} selectate`}
        </span>
        <ChevronDown className="ml-2 h-4 w-4 flex-shrink-0 text-gray-400" />
      </button>

      {open && (
        <div className="absolute z-20 mt-1 max-h-60 w-64 overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-600 dark:bg-gray-800">
          {categories.length > 0 && (
            <button
              onClick={() => setCategories([])}
              className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-blue-600 hover:bg-gray-50 dark:text-blue-400 dark:hover:bg-gray-700"
            >
              <X className="h-3 w-3" />
              Resetează selecția
            </button>
          )}
          {ALL_CATEGORIES.map((cat) => (
            <label
              key={cat}
              className="flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <input
                type="checkbox"
                checked={categories.includes(cat)}
                onChange={() => toggle(cat)}
                className="h-3.5 w-3.5 rounded border-gray-300 text-blue-600 focus:ring-blue-500 dark:border-gray-600"
              />
              <span className="text-gray-700 dark:text-gray-300">{CATEGORY_LABELS[cat]}</span>
            </label>
          ))}
        </div>
      )}
    </div>
  );
}

export default function DocumentFilters() {
  const {
    processingStatus,
    reviewStatus,
    search,
    setProcessingStatus,
    setReviewStatus,
    setSearch,
    resetFilters,
    categories,
  } = useFilterStore();

  const hasFilters =
    categories.length > 0 || processingStatus !== '' || reviewStatus !== '' || search !== '';

  return (
    <div className="flex flex-wrap items-end gap-4">
      <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
        <Filter className="h-4 w-4" />
        Filtre
      </div>

      <div className="w-64">
        <SearchBar value={search} onChange={setSearch} />
      </div>

      <div className="w-52">
        <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">Categorie</label>
        <CategoryMultiSelect />
      </div>

      <div className="w-44">
        <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
          Status procesare
        </label>
        <select
          value={processingStatus}
          onChange={(e) => setProcessingStatus(e.target.value as ProcessingStatus | '')}
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
        >
          <option value="">Toate</option>
          {PROCESSING_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      <div className="w-44">
        <label className="mb-1 block text-xs font-medium text-gray-500 dark:text-gray-400">
          Status revizie
        </label>
        <select
          value={reviewStatus}
          onChange={(e) => setReviewStatus(e.target.value as ReviewStatus | '')}
          className="block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300"
        >
          <option value="">Toate</option>
          {REVIEW_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {hasFilters && (
        <button
          onClick={resetFilters}
          className="inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/30"
        >
          <X className="h-3.5 w-3.5" />
          Resetează
        </button>
      )}
    </div>
  );
}
