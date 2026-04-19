import { Link, useLocation } from 'react-router-dom';
import { format } from 'date-fns';
import { Loader2 } from 'lucide-react';
import type { Document, ExtractionResult } from '../../types';
import CategoryBadge from './CategoryBadge';
import ConfidenceBar from './ConfidenceBar';
import StatusBadge from './StatusBadge';
import ExpirationWarning from '../shared/ExpirationWarning';

export interface DocumentRowProps {
  document: Document;
  extraction?: ExtractionResult | null;
}

export default function DocumentRow({ document, extraction }: DocumentRowProps) {
  const formattedDate = format(new Date(document.uploaded_at), 'dd.MM.yyyy HH:mm');
  const location = useLocation();
  const from = `${location.pathname}${location.search}`;
  const isProcessing =
    document.processing_status === 'processing' || document.processing_status === 'pending';

  return (
    <tr
      className={`border-b border-gray-200 dark:border-gray-700 ${
        isProcessing
          ? 'bg-blue-50/60 hover:bg-blue-100/70 dark:bg-blue-900/20 dark:hover:bg-blue-900/30'
          : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
      }`}
    >
      <td className="px-4 py-3 text-sm">
        <div className="flex items-center gap-2 truncate" title={document.original_filename}>
          {isProcessing && (
            <Loader2
              className="h-3.5 w-3.5 shrink-0 animate-spin text-blue-600 dark:text-blue-400"
              aria-label="Se procesează"
            />
          )}
          <Link
            to={`/documents/${document.id}`}
            state={{ from }}
            className="truncate font-medium text-blue-600 hover:text-blue-800 hover:underline dark:text-blue-400 dark:hover:text-blue-300"
          >
            {document.original_filename}
          </Link>
        </div>
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <CategoryBadge category={document.categorie} />
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
        <div className="truncate" title={extraction?.material || ''}>
          {extraction?.material || '—'}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
        <div className="truncate" title={extraction?.producator || ''}>
          {extraction?.producator || '—'}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
        <div className="truncate" title={extraction?.companie || ''}>
          {extraction?.companie || '—'}
        </div>
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
        <div className="truncate" title={extraction?.distribuitor || ''}>
          {extraction?.distribuitor || '—'}
        </div>
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <ExpirationWarning dataExpirare={extraction?.data_expirare ?? null} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700 dark:text-gray-300">
        {document.page_count ?? '—'}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <ConfidenceBar confidence={document.confidence} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <StatusBadge status={document.processing_status} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
        {formattedDate}
      </td>
    </tr>
  );
}
