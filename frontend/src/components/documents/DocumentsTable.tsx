import { ChevronUp, ChevronDown } from 'lucide-react';
import type { Document, ExtractionResult } from '../../types';
import DocumentRow from './DocumentRow';

export type SortField =
  | 'filename'
  | 'categorie'
  | 'material'
  | 'producator'
  | 'companie'
  | 'distribuitor'
  | 'data_expirare'
  | 'confidence'
  | 'processing_status'
  | 'uploaded_at';

export type SortDirection = 'asc' | 'desc';

interface Column {
  key: SortField;
  label: string;
}

const COLUMNS: Column[] = [
  { key: 'filename', label: 'Fișier' },
  { key: 'categorie', label: 'Categorie' },
  { key: 'material', label: 'Material' },
  { key: 'producator', label: 'Producător' },
  { key: 'companie', label: 'Companie' },
  { key: 'distribuitor', label: 'Distribuitor' },
  { key: 'data_expirare', label: 'Data expirare' },
  { key: 'confidence', label: 'Încredere' },
  { key: 'processing_status', label: 'Status procesare' },
  { key: 'uploaded_at', label: 'Data încărcare' },
];

export interface DocumentsTableProps {
  documents: Document[];
  extractions?: Map<number, ExtractionResult>;
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

export default function DocumentsTable({
  documents,
  extractions,
  sortField,
  sortDirection,
  onSort,
}: DocumentsTableProps) {
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <table className="w-full min-w-[1460px] table-fixed divide-y divide-gray-200 dark:divide-gray-700">
        <colgroup>
          <col className="w-[200px]" /> {/* Fișier */}
          <col className="w-[180px]" /> {/* Categorie */}
          <col className="w-[150px]" /> {/* Material */}
          <col className="w-[130px]" /> {/* Producător */}
          <col className="w-[130px]" /> {/* Companie */}
          <col className="w-[130px]" /> {/* Distribuitor */}
          <col className="w-[180px]" /> {/* Data expirare */}
          <col className="w-[100px]" /> {/* Încredere */}
          <col className="w-[130px]" /> {/* Status procesare */}
          <col className="w-[130px]" /> {/* Data încărcare */}
        </colgroup>
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className="cursor-pointer select-none px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                onClick={() => onSort(col.key)}
              >
                <div className="flex items-center gap-1">
                  {col.label}
                  {sortField === col.key ? (
                    sortDirection === 'asc' ? (
                      <ChevronUp className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5" />
                    )
                  ) : (
                    <span className="h-3.5 w-3.5" />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {documents.map((doc) => (
            <DocumentRow
              key={doc.id}
              document={doc}
              extraction={extractions?.get(doc.id) ?? null}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
