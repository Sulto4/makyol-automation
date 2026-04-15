import { ChevronLeft, ChevronRight } from 'lucide-react';

interface PaginationProps {
  currentPage: number;
  totalItems: number;
  perPage: number;
  onPageChange: (page: number) => void;
  onPerPageChange: (perPage: number) => void;
}

const PER_PAGE_OPTIONS = [20, 50, 100];

export default function Pagination({
  currentPage,
  totalItems,
  perPage,
  onPageChange,
  onPerPageChange,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(totalItems / perPage));
  const safeCurrentPage = Math.min(currentPage, totalPages);

  const startItem = totalItems === 0 ? 0 : (safeCurrentPage - 1) * perPage + 1;
  const endItem = Math.min(safeCurrentPage * perPage, totalItems);

  function getPageNumbers(): (number | '...')[] {
    const pages: (number | '...')[] = [];
    if (totalPages <= 7) {
      for (let i = 1; i <= totalPages; i++) pages.push(i);
      return pages;
    }
    pages.push(1);
    if (safeCurrentPage > 3) pages.push('...');
    const start = Math.max(2, safeCurrentPage - 1);
    const end = Math.min(totalPages - 1, safeCurrentPage + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (safeCurrentPage < totalPages - 2) pages.push('...');
    pages.push(totalPages);
    return pages;
  }

  return (
    <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-800 sm:px-6">
      <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
        <span>Afișează</span>
        <select
          value={perPage}
          onChange={(e) => {
            onPerPageChange(Number(e.target.value));
            onPageChange(1);
          }}
          className="rounded-md border border-gray-300 bg-white px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
        >
          {PER_PAGE_OPTIONS.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
        <span>
          din {totalItems} rezultate ({startItem}–{endItem})
        </span>
      </div>

      <nav className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(safeCurrentPage - 1)}
          disabled={safeCurrentPage <= 1}
          className="inline-flex items-center rounded-md px-2 py-1 text-sm text-gray-500 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          <ChevronLeft className="h-4 w-4" />
          <span>Anterior</span>
        </button>

        {getPageNumbers().map((page, idx) =>
          page === '...' ? (
            <span key={`ellipsis-${idx}`} className="px-2 py-1 text-sm text-gray-500 dark:text-gray-400">
              …
            </span>
          ) : (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              className={`inline-flex items-center rounded-md px-3 py-1 text-sm font-medium ${
                page === safeCurrentPage
                  ? 'bg-blue-600 text-white dark:bg-blue-500'
                  : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
              }`}
            >
              {page}
            </button>
          ),
        )}

        <button
          onClick={() => onPageChange(safeCurrentPage + 1)}
          disabled={safeCurrentPage >= totalPages}
          className="inline-flex items-center rounded-md px-2 py-1 text-sm text-gray-500 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          <span>Următor</span>
          <ChevronRight className="h-4 w-4" />
        </button>
      </nav>
    </div>
  );
}
