import { Link, useLocation } from 'react-router-dom';
import { format } from 'date-fns';
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

  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-700/50">
      <td className="px-4 py-3 text-sm">
        <div className="truncate" title={document.original_filename}>
          <Link
            to={`/documents/${document.id}`}
            state={{ from }}
            className="font-medium text-blue-600 hover:text-blue-800 hover:underline dark:text-blue-400 dark:hover:text-blue-300"
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
