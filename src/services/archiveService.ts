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
   * Build the Excel workbook with the 13-column schema and hyperlinks.
   */
  private buildWorkbook(records: ArchiveDocumentRecord[]): ExcelJS.Workbook {
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
    for (const { document: doc, extraction, relativePath } of records) {
      const row = worksheet.addRow([
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
        formatDateValue(extraction?.data_expirare),
        formatDateValue(doc.uploaded_at),
      ]);

      // Replace column B with HYPERLINK formula
      const encodedPath = encodeHyperlinkPath(relativePath.replace(/\\/g, '/'));
      const filenameCell = row.getCell(2);
      filenameCell.value = {
        formula: `HYPERLINK("./${encodedPath}","${doc.original_filename.replace(/"/g, '""')}")`,
      } as ExcelJS.CellFormulaValue;
      filenameCell.font = {
        color: { argb: 'FF0563C1' },
        underline: true,
      };
    }

    // Alternating row colors (starting from row 2)
    for (let i = 2; i <= worksheet.rowCount; i++) {
      const row = worksheet.getRow(i);
      if (i % 2 === 0) {
        row.eachCell({ includeEmpty: true }, (cell) => {
          // Preserve hyperlink font styling on column B
          if (cell.address.startsWith('B')) {
            cell.fill = {
              type: 'pattern',
              pattern: 'solid',
              fgColor: { argb: 'FFF2F2F2' },
            };
            return;
          }
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

    return workbook;
  }
}
