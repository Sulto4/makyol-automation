import type { Document, ExtractionResult } from '../types';
import { getCategoryLabel } from './categories';
import { formatDate, parseDataExpirare } from './dates';

interface DocumentWithExtraction {
  document: Document;
  extraction: ExtractionResult | null;
}

// Same column order as Excel and the UI table. CSV can't carry per-row
// formatting, so the expired-row highlight is Excel-only.
const HEADERS = [
  'Fișier',
  'Categorie',
  'Material',
  'Producător',
  'Companie',
  'Distribuitor',
  'Data expirare',
  'Pagini',
  'Adresă producător',
  'Adresă distribuitor',
  'Status procesare',
];

/**
 * Export filtered document data as a downloadable CSV file.
 */
export function exportToCSV(
  items: DocumentWithExtraction[],
  filename: string = 'documente-makyol.csv'
): void {
  const rows = items.map(({ document: doc, extraction }) => {
    const dateExpirareRaw = extraction?.data_expirare ?? null;
    const dateExpirareDisplay = formatDate(dateExpirareRaw);
    const dateExpirareCell =
      parseDataExpirare(dateExpirareRaw) === null
        ? (dateExpirareRaw ?? '')
        : dateExpirareDisplay;

    return [
      doc.original_filename,
      getCategoryLabel(doc.categorie),
      extraction?.material ?? '',
      extraction?.producator ?? '',
      extraction?.companie ?? '',
      extraction?.distribuitor ?? '',
      dateExpirareCell,
      doc.page_count != null ? String(doc.page_count) : '',
      extraction?.adresa_producator ?? '',
      extraction?.adresa_distribuitor ?? '',
      doc.processing_status,
    ];
  });

  const csvContent = [HEADERS, ...rows]
    .map((row) =>
      row.map((cell) => {
        if (/[",\n\r]/.test(cell)) {
          return '"' + cell.replace(/"/g, '""') + '"';
        }
        return cell;
      }).join(',')
    )
    .join('\n');

  const bom = '\uFEFF';
  const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}
