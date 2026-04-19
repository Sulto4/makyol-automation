import ExcelJS from 'exceljs';
import type { Document, ExtractionResult } from '../types';
import { getCategoryLabel } from './categories';
import { formatDate, parseDataExpirare, isExpired } from './dates';

interface DocumentWithExtraction {
  document: Document;
  extraction: ExtractionResult | null;
}

// Column order mirrors DocumentsTable in the UI; status_procesare kept at the
// end so the table reads as data-first, status-after.
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

// Excel "Bad" preset — light pink fill + dark red text. Stays readable.
const EXPIRED_FILL_ARGB = 'FFFFC7CE';
const EXPIRED_FONT_ARGB = 'FF9C0006';
const ALT_ROW_FILL_ARGB = 'FFF2F2F2';

/**
 * Export filtered document data as a downloadable Excel file with formatting.
 * Rows whose data_expirare is past today get a red highlight.
 */
export async function exportToExcel(
  items: DocumentWithExtraction[],
  filename: string = 'documente-makyol.xlsx'
): Promise<void> {
  const workbook = new ExcelJS.Workbook();
  const worksheet = workbook.addWorksheet('Documente Makyol');

  const headerRow = worksheet.addRow(HEADERS);
  headerRow.eachCell((cell) => {
    cell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
    cell.fill = {
      type: 'pattern',
      pattern: 'solid',
      fgColor: { argb: 'FF1F4E79' },
    };
  });

  worksheet.views = [{ state: 'frozen' as const, ySplit: 1 }];

  items.forEach(({ document: doc, extraction }) => {
    const dateExpirareRaw = extraction?.data_expirare ?? null;
    const dateExpirareDate = parseDataExpirare(dateExpirareRaw);
    const dateExpirareDisplay = formatDate(dateExpirareRaw);
    const expired = isExpired(dateExpirareDate);

    const row = worksheet.addRow([
      doc.original_filename,
      getCategoryLabel(doc.categorie),
      extraction?.material ?? '',
      extraction?.producator ?? '',
      extraction?.companie ?? '',
      extraction?.distribuitor ?? '',
      dateExpirareDisplay === '—' ? (dateExpirareRaw ?? '') : dateExpirareDisplay,
      doc.page_count ?? '',
      extraction?.adresa_producator ?? '',
      extraction?.adresa_distribuitor ?? '',
      doc.processing_status,
    ]);

    if (expired) {
      row.eachCell({ includeEmpty: true }, (cell) => {
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: EXPIRED_FILL_ARGB },
        };
        cell.font = { color: { argb: EXPIRED_FONT_ARGB }, bold: true };
      });
    }
  });

  // Alternating row colors — only for non-expired rows so red highlight wins.
  for (let i = 2; i <= worksheet.rowCount; i++) {
    const row = worksheet.getRow(i);
    const firstCell = row.getCell(1);
    const isExpiredRow =
      firstCell.fill &&
      firstCell.fill.type === 'pattern' &&
      (firstCell.fill as ExcelJS.FillPattern).fgColor?.argb === EXPIRED_FILL_ARGB;
    if (isExpiredRow) continue;
    if (i % 2 === 0) {
      row.eachCell({ includeEmpty: true }, (cell) => {
        cell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: ALT_ROW_FILL_ARGB },
        };
      });
    }
  }

  worksheet.columns.forEach((column, index) => {
    let maxLength = HEADERS[index].length;
    column.eachCell?.({ includeEmpty: false }, (cell) => {
      const cellValue = cell.value ? String(cell.value) : '';
      if (cellValue.length > maxLength) {
        maxLength = cellValue.length;
      }
    });
    column.width = Math.max(10, Math.min(50, maxLength + 2));
  });

  worksheet.autoFilter = {
    from: { row: 1, column: 1 },
    to: { row: 1, column: HEADERS.length },
  };

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
