import { Link } from 'react-router-dom';
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

  return (
    <tr className="border-b border-gray-200 hover:bg-gray-50">
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <Link
          to={`/documents/${document.id}`}
          className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
          title={document.original_filename}
        >
          {document.original_filename.length > 40
            ? `${document.original_filename.slice(0, 37)}...`
            : document.original_filename}
        </Link>
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <CategoryBadge category={document.categorie} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
        {extraction?.material || '—'}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
        {extraction?.producator || '—'}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
        {extraction?.companie || '—'}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-700">
        {extraction?.distribuitor || '—'}
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <ExpirationWarning dataExpirare={extraction?.data_expirare ?? null} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <ConfidenceBar confidence={document.confidence} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <StatusBadge status={document.processing_status} />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm">
        <StatusBadge status={document.review_status} variant="review" />
      </td>
      <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
        {formattedDate}
      </td>
    </tr>
  );
}
