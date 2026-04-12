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
  | 'review_status'
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
  { key: 'review_status', label: 'Status revizie' },
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
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {COLUMNS.map((col) => (
              <th
                key={col.key}
                className="cursor-pointer select-none px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 hover:text-gray-700"
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
        <tbody className="divide-y divide-gray-200">
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
