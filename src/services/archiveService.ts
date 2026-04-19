import archiver from 'archiver';
import ExcelJS from 'exceljs';
import type { Response } from 'express';
import type { Document } from '../models/Document';
import type { ExtractionResult } from '../models/ExtractionResult';

/**
 * Input record for archive generation
 */
export interface ArchiveDocumentRecord {
  document: Document;
  extraction: ExtractionResult | null;
  /** Relative path within the archive (forward slashes, e.g. "Certificat/file.pdf") */
  relativePath: string;
  /** Absolute path on disk to the source PDF */
  absolutePath: string;
}

/**
 * Category label mapping (mirrors frontend/src/utils/categories.ts)
 */
const CATEGORY_LABELS: Record<string, string> = {
  CERTIFICAT_CALITATE: 'Certificat de Calitate',
  DECLARATIE_PERFORMANTA: 'Declarație de Performanță',
  CERTIFICAT_CONFORMITATE: 'Certificat de Conformitate',
  FISA_TEHNICA: 'Fișă Tehnică',
  AGREMENTARE: 'Agrementare Tehnică',
  CERTIFICARE_ISO: 'Certificare ISO',
  UNKNOWN: 'Necunoscut',
};

function getCategoryLabel(category: string | null): string {
  if (!category) return CATEGORY_LABELS['UNKNOWN'] ?? 'Necunoscut';
  return CATEGORY_LABELS[category] ?? category;
}

/**
 * Format a date value for Excel display
 */
function formatDateValue(value: string | Date | null | undefined): string {
  if (!value) return '';
  const date = value instanceof Date ? value : new Date(value);
  if (isNaN(date.getTime())) return '';
  return date.toLocaleDateString('ro-RO');
}

/**
 * Try to parse a data_expirare value as a real date.
 * Accepts ISO ("2027-06-15"), Romanian (DD.MM.YYYY / DD/MM/YYYY / DD-MM-YYYY)
 * and yyyy/MM/dd. Returns null for duration phrases like "Pe durata
 * contractului" so we don't redden rows we don't actually know are expired.
 */
function parseExpirareDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const trimmed = String(value).trim();
  if (!trimmed) return null;

  const iso = new Date(trimmed);
  if (!isNaN(iso.getTime()) && /^\d{4}-\d{2}-\d{2}/.test(trimmed)) return iso;

  const m = trimmed.match(/^(\d{1,2})[./-](\d{1,2})[./-](\d{4})$/);
  if (m) {
    const [, dd, mm, yyyy] = m;
    const d = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
    if (!isNaN(d.getTime())) return d;
  }

  const m2 = trimmed.match(/^(\d{4})\/(\d{1,2})\/(\d{1,2})$/);
  if (m2) {
    const [, yyyy, mm, dd] = m2;
    const d = new Date(Number(yyyy), Number(mm) - 1, Number(dd));
    if (!isNaN(d.getTime())) return d;
  }

  return null;
}

function isExpired(date: Date | null): boolean {
  if (!date) return false;
  // Compare at start-of-day so "today's expiry" is still considered valid.
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  return date.getTime() < now.getTime();
}

const EXPIRED_FILL_ARGB = 'FFFFC7CE';
const EXPIRED_FONT_ARGB = 'FF9C0006';
const ALT_ROW_FILL_ARGB = 'FFF2F2F2';
const SEPARATOR_FILL_ARGB = 'FF4472C4';
const ROOT_FOLDER_LABEL = '(rădăcină)';

function folderOf(relativePath: string): string {
  const normalized = relativePath.replace(/\\/g, '/');
  const idx = normalized.lastIndexOf('/');
  return idx === -1 ? '' : normalized.slice(0, idx);
}

/**
 * URL-encode special characters in a path segment for Excel HYPERLINK formula
 */
function encodeHyperlinkPath(relativePath: string): string {
  return relativePath
    .split('/')
    .map((segment) => encodeURIComponent(segment).replace(/%20/g, ' '))
    .join('/');
}

/**
 * Archive Service
 *
 * Generates a ZIP archive containing PDFs organized by folder structure
 * and an Excel summary workbook with hyperlinks to each file.
 */
export class ArchiveService {
  /**
   * Generate a ZIP archive and stream it to the Express response.
   *
   * @param records - Document records with extraction data and paths
   * @param res - Express response object to stream the ZIP into
   * @param archiveFilename - Filename for the Content-Disposition header
   */
  async generateArchive(
    records: ArchiveDocumentRecord[],
    res: Response,
    archiveFilename: string = 'documente-makyol.zip'
  ): Promise<void> {
    const workbook = this.buildWorkbook(records);
    const excelBuffer = await workbook.xlsx.writeBuffer();

    res.setHeader('Content-Type', 'application/zip');
    res.setHeader(
      'Content-Disposition',
      `attachment; filename="${encodeURIComponent(archiveFilename)}"`
    );

    const archive = archiver('zip', { zlib: { level: 6 } });

    archive.on('error', (err: Error) => {
      throw err;
    });

    archive.pipe(res);

    // Add Excel at the archive root
    archive.append(Buffer.from(excelBuffer), { name: 'documente-makyol.xlsx' });

    // Add each PDF at its relative path
    for (const record of records) {
      const archivePath = record.relativePath.replace(/\\/g, '/');
      archive.file(record.absolutePath, { name: archivePath });
    }

    await archive.finalize();
  }

  /**
   * Build the Excel workbook. Column order mirrors the frontend table and
   * the standalone Excel/CSV exports. Filename (col A) becomes a HYPERLINK
   * pointing to the PDF inside the ZIP. Expired rows get a red highlight.
   */
  private buildWorkbook(records: ArchiveDocumentRecord[]): ExcelJS.Workbook {
    const workbook = new ExcelJS.Workbook();
    const worksheet = workbook.addWorksheet('Documente Makyol');

    const headers = [
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

    const headerRow = worksheet.addRow(headers);
    headerRow.eachCell((cell) => {
      cell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
      cell.fill = {
        type: 'pattern',
        pattern: 'solid',
        fgColor: { argb: 'FF1F4E79' },
      };
    });

    worksheet.views = [{ state: 'frozen' as const, ySplit: 1 }];

    // Sort records by [folder, filename] (locale-aware) so that documents
    // coming from the same uploaded subfolder are grouped contiguously.
    const sortedRecords = records.slice().sort((a, b) => {
      const folderCmp = folderOf(a.relativePath).localeCompare(
        folderOf(b.relativePath),
        'ro',
        { numeric: true, sensitivity: 'base' }
      );
      if (folderCmp !== 0) return folderCmp;
      return a.document.original_filename.localeCompare(
        b.document.original_filename,
        'ro',
        { numeric: true, sensitivity: 'base' }
      );
    });

    // Only emit folder-separator rows when the export actually spans a folder
    // structure. Flat uploads (single file or all-at-root) stay unchanged.
    const showSeparators = sortedRecords.some(
      (r) => folderOf(r.relativePath) !== ''
    );

    const expiredRowNumbers = new Set<number>();
    let currentFolder: string | null = null;
    let dataRowIndex = 0;

    for (const { document: doc, extraction, relativePath } of sortedRecords) {
      const folder = folderOf(relativePath);

      if (showSeparators && folder !== currentFolder) {
        const label = folder === '' ? ROOT_FOLDER_LABEL : folder;
        const separatorRow = worksheet.addRow([
          label, '', '', '', '', '', '', '', '', '', '',
        ]);
        worksheet.mergeCells(
          separatorRow.number, 1,
          separatorRow.number, headers.length
        );
        const labelCell = separatorRow.getCell(1);
        labelCell.font = { bold: true, color: { argb: 'FFFFFFFF' } };
        labelCell.fill = {
          type: 'pattern',
          pattern: 'solid',
          fgColor: { argb: SEPARATOR_FILL_ARGB },
        };
        labelCell.alignment = { vertical: 'middle', horizontal: 'left' };
        separatorRow.height = 22;
        currentFolder = folder;
      }

      const dateExpirareRaw = extraction?.data_expirare ?? null;
      const parsedDate = parseExpirareDate(dateExpirareRaw);
      // For real dates, render via Romanian locale; for duration phrases we
      // pass the raw string through so the cell still shows context.
      const dateDisplay = parsedDate
        ? formatDateValue(parsedDate)
        : (dateExpirareRaw ?? '');

      const row = worksheet.addRow([
        doc.original_filename,
        getCategoryLabel(doc.categorie),
        extraction?.material ?? '',
        extraction?.producator ?? '',
        extraction?.companie ?? '',
        extraction?.distribuitor ?? '',
        dateDisplay,
        doc.page_count ?? '',
        extraction?.adresa_producator ?? '',
        extraction?.adresa_distribuitor ?? '',
        doc.processing_status,
      ]);
      dataRowIndex++;

      // Filename is now in column A — point the hyperlink there.
      const encodedPath = encodeHyperlinkPath(relativePath.replace(/\\/g, '/'));
      const filenameCell = row.getCell(1);
      filenameCell.value = {
        formula: `HYPERLINK("./${encodedPath}","${doc.original_filename.replace(/"/g, '""')}")`,
      } as ExcelJS.CellFormulaValue;
      filenameCell.font = {
        color: { argb: 'FF0563C1' },
        underline: true,
      };

      if (isExpired(parsedDate)) {
        expiredRowNumbers.add(row.number);
        row.eachCell({ includeEmpty: true }, (cell) => {
          cell.fill = {
            type: 'pattern',
            pattern: 'solid',
            fgColor: { argb: EXPIRED_FILL_ARGB },
          };
          // Keep hyperlink underline but switch its colour to dark red so
          // the cell stays readable on the pink fill.
          cell.font = { color: { argb: EXPIRED_FONT_ARGB }, bold: true };
        });
        // Re-apply hyperlink underline (the eachCell loop above replaces it)
        filenameCell.font = {
          color: { argb: EXPIRED_FONT_ARGB },
          underline: true,
          bold: true,
        };
      } else if (dataRowIndex % 2 === 0) {
        // Alternating zebra stripe — indexed by data-row position so that
        // separator rows inserted between groups don't break the pattern.
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
      let maxLength = headers[index].length;
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
      to: { row: 1, column: headers.length },
    };

    return workbook;
  }
}
