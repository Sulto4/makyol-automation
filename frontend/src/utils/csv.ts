import type { Document, ExtractionResult } from '../types';
import { getCategoryLabel } from './categories';
import { formatDate } from './dates';

interface DocumentWithExtraction {
  document: Document;
  extraction: ExtractionResult | null;
}

/**
 * Export filtered document data as a downloadable CSV file.
 */
export function exportToCSV(
  items: DocumentWithExtraction[],
  filename: string = 'documente-makyol.csv'
): void {
  const headers = [
    'ID',
    'Fișier Original',
    'Categorie',
    'Status Procesare',
    'Status Review',
    'Încredere',
    'Metodă Clasificare',
    'Material',
    'Producător',
    'Companie',
    'Distribuitor',
    'Adresa Distribuitor',
    'Data Expirare',
    'Încărcat La',
  ];

  const rows = items.map(({ document: doc, extraction }) => [
    String(doc.id),
    doc.original_filename,
    getCategoryLabel(doc.categorie),
    doc.processing_status,
    doc.review_status ?? '',
    doc.confidence != null ? (doc.confidence * 100).toFixed(1) + '%' : '',
    doc.metoda_clasificare ?? '',
    extraction?.material ?? '',
    extraction?.producator ?? '',
    extraction?.companie ?? '',
    extraction?.distribuitor ?? '',
    extraction?.adresa_distribuitor ?? '',
    formatDate(extraction?.data_expirare ?? null),
    formatDate(doc.uploaded_at),
  ]);

  const csvContent = [headers, ...rows]
    .map((row) =>
      row.map((cell) => {
        // Escape cells containing commas, quotes, or newlines
        if (/[",\n\r]/.test(cell)) {
          return '"' + cell.replace(/"/g, '""') + '"';
        }
        return cell;
      }).join(',')
    )
    .join('\n');

  // Add BOM for proper UTF-8 handling in Excel
  const bom = '\uFEFF';
  const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}
