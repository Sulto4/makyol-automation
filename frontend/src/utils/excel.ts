import ExcelJS from 'exceljs';
import type { Document, ExtractionResult } from '../types';
import { getCategoryLabel } from './categories';
import { formatDate } from './dates';

interface DocumentWithExtraction {
  document: Document;
  extraction: ExtractionResult | null;
}

/**
 * Export filtered document data as a downloadable Excel file with formatting.
 */
export async function exportToExcel(
  items: DocumentWithExtraction[],
  filename: string = 'documente-makyol.xlsx'
): Promise<void> {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Documente Makyol');

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
    'Data Expirare',
    'Pagini',
    'Încărcat La',
  ];

  // Add header row
  const headerRow = worksheet.addRow(headers);
  headerRow.eachCell((cell) => {
    cell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
    cell.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FF1F4E79' },
    };
  });

  // Freeze top row
  worksheet.views = [{ state: 'frozen' as const, ySplit: 1 }];

  // Add data rows
  items.forEach(({ document: doc, extraction }) => {
    const dateExpirare = formatDate(extraction?.data_expirare ?? null);
    const dateUploaded = formatDate(doc.uploaded_at);

    worksheet.addRow([
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
      dateExpirare === '—' ? '' : dateExpirare,
      doc.page_count ?? '',
      dateUploaded === '—' ? '' : dateUploaded,
    ]);
  });

  // Alternating row colors (starting from row 2)
  for (let i = 2; i <= worksheet.rowCount; i++) {
    const row = worksheet.getRow(i);
    if (i % 2 === 0) {
      row.eachCell({ includeEmpty: true }, (cell) => {
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: 'FFF2F2F2' },
        };
      });
    }
  }

  // Auto-fit column widths
  worksheet.columns.forEach((column, index) => {
    let maxLength = headers[index].length;
    column.eachCell?.({ includeEmpty: false }, (cell) => {
      const cellValue = cell.value ? String(cell.value) : '';
      if (cellValue.length > maxLength) {
        maxLength = cellValue.length;
      }
    });
    column.width = Math.max(10, Math.min(50, maxLength + 2));
  });

  // Auto-filter on all columns
  worksheet.autoFilter = {
    from: { row: 1, column: 1 },
    to: { row: 1, column: headers.length },
  };

  // Generate and download
  const buffer = await workbook.xlsx.writeBuffer();
  const blob = new Blob([buffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = URL.createObjectURL(blob);

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();

  URL.revokeObjectURL(url);
}
