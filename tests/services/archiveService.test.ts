import { ArchiveService, ArchiveDocumentRecord } from '../../src/services/archiveService';
import ExcelJS from 'exceljs';
import type { Document } from '../../src/models/Document';
import type { ExtractionResult } from '../../src/models/ExtractionResult';

// Mock archiver and response — we only test the workbook via reflection
jest.mock('archiver', () => {
  const mockArchive = {
    on: jest.fn(),
    pipe: jest.fn(),
    append: jest.fn(),
    file: jest.fn(),
    finalize: jest.fn().mockResolvedValue(undefined),
  };
  return jest.fn(() => mockArchive);
});

/**
 * Helper to access the private buildWorkbook method for unit testing
 */
function buildWorkbook(service: ArchiveService, records: ArchiveDocumentRecord[]): ExcelJS.Workbook {
  return (service as any).buildWorkbook(records);
}

function makeDocument(overrides: Partial<Document> = {}): Document {
  return {
    id: 1,
    filename: 'abc123.pdf',
    original_filename: 'certificat.pdf',
    file_path: '/uploads/abc123.pdf',
    file_size: 1024,
    mime_type: 'application/pdf',
    processing_status: 'completed' as any,
    error_message: null,
    uploaded_at: new Date('2024-03-15'),
    processing_started_at: null,
    processing_completed_at: null,
    categorie: 'CERTIFICAT_CALITATE',
    confidence: 0.95,
    metoda_clasificare: 'vision',
    review_status: null,
    created_at: new Date('2024-03-15'),
    updated_at: new Date('2024-03-15'),
    ...overrides,
  };
}

function makeExtraction(overrides: Partial<ExtractionResult> = {}): ExtractionResult {
  return {
    id: 1,
    document_id: 1,
    extracted_text: 'Sample text',
    metadata: {} as any,
    confidence_score: 0.95,
    extraction_status: 'completed' as any,
    error_details: null,
    material: 'Ciment',
    data_expirare: '2025-12-31',
    companie: 'ACME SRL',
    producator: 'Holcim',
    distribuitor: 'Distrib SRL',
    adresa_producator: null,
    extraction_model: 'gpt-4o',
    created_at: new Date('2024-03-15'),
    ...overrides,
  } as ExtractionResult;
}

function makeRecord(overrides: Partial<ArchiveDocumentRecord> = {}): ArchiveDocumentRecord {
  return {
    document: makeDocument(),
    extraction: makeExtraction(),
    relativePath: 'Certificat/certificat.pdf',
    absolutePath: 'C:\\uploads\\abc123.pdf',
    ...overrides,
  };
}

describe('ArchiveService', () => {
  let service: ArchiveService;

  beforeEach(() => {
    service = new ArchiveService();
  });

  describe('buildWorkbook - headers', () => {
    it('should have correct 13-column headers matching the schema', () => {
      const workbook = buildWorkbook(service, []);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      expect(worksheet).toBeDefined();

      const expectedHeaders = [
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

      const headerRow = worksheet.getRow(1);
      const actualHeaders: string[] = [];
      headerRow.eachCell((cell) => {
        actualHeaders.push(String(cell.value));
      });

      expect(actualHeaders).toEqual(expectedHeaders);
      expect(actualHeaders).toHaveLength(13);
    });
  });

  describe('buildWorkbook - HYPERLINK formula', () => {
    it('should generate HYPERLINK formula with relative path', () => {
      const record = makeRecord({
        relativePath: 'Certificat/certificat.pdf',
        document: makeDocument({ original_filename: 'certificat.pdf' }),
      });
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);
      const cellValue = cell.value as ExcelJS.CellFormulaValue;

      expect(cellValue.formula).toBe(
        'HYPERLINK("./Certificat/certificat.pdf","certificat.pdf")'
      );
    });

    it('should generate HYPERLINK with nested subfolder paths', () => {
      const record = makeRecord({
        relativePath: 'Certificat/subfolder/deep/file.pdf',
        document: makeDocument({ original_filename: 'file.pdf' }),
      });
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);
      const cellValue = cell.value as ExcelJS.CellFormulaValue;

      expect(cellValue.formula).toBe(
        'HYPERLINK("./Certificat/subfolder/deep/file.pdf","file.pdf")'
      );
    });
  });

  describe('buildWorkbook - hyperlink styling', () => {
    it('should have blue (#FF0563C1) and underline font on hyperlink cells', () => {
      const record = makeRecord();
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);

      expect(cell.font?.color?.argb).toBe('FF0563C1');
      expect(cell.font?.underline).toBe(true);
    });
  });

  describe('buildWorkbook - special characters in filenames', () => {
    it('should handle spaces in filenames (kept as spaces per encodeHyperlinkPath)', () => {
      const record = makeRecord({
        relativePath: 'Certificat/my file name.pdf',
        document: makeDocument({ original_filename: 'my file name.pdf' }),
      });
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);
      const cellValue = cell.value as ExcelJS.CellFormulaValue;

      // encodeHyperlinkPath encodes then replaces %20 back to space
      expect(cellValue.formula).toContain('my file name.pdf');
    });

    it('should URL-encode diacritics in paths', () => {
      const record = makeRecord({
        relativePath: 'Certificat/certificat-în-română.pdf',
        document: makeDocument({ original_filename: 'certificat-în-română.pdf' }),
      });
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);
      const cellValue = cell.value as ExcelJS.CellFormulaValue;

      // Extract the path portion (between first pair of quotes)
      const pathMatch = cellValue.formula!.match(/HYPERLINK\("([^"]+)"/);
      expect(pathMatch).not.toBeNull();
      const hyperlinkPath = pathMatch![1];

      // Diacritics should be URL-encoded in the path
      expect(hyperlinkPath).not.toContain('î');
      expect(hyperlinkPath).not.toContain('ă');
      expect(hyperlinkPath).toContain('%');
    });

    it('should escape double quotes in filenames', () => {
      const record = makeRecord({
        relativePath: 'Certificat/file"name.pdf',
        document: makeDocument({ original_filename: 'file"name.pdf' }),
      });
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);
      const cellValue = cell.value as ExcelJS.CellFormulaValue;

      // Double quotes escaped as "" in Excel formula
      expect(cellValue.formula).toContain('file""name.pdf');
    });
  });

  describe('buildWorkbook - forward slashes', () => {
    it('should use forward slashes in all hyperlink paths', () => {
      const record = makeRecord({
        relativePath: 'Certificat\\subfolder\\file.pdf',
        document: makeDocument({ original_filename: 'file.pdf' }),
      });
      const workbook = buildWorkbook(service, [record]);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      const cell = worksheet.getRow(2).getCell(2);
      const cellValue = cell.value as ExcelJS.CellFormulaValue;

      expect(cellValue.formula).not.toContain('\\');
      expect(cellValue.formula).toContain('/');
    });
  });

  describe('buildWorkbook - empty document list', () => {
    it('should produce valid workbook with headers but no data rows', () => {
      const workbook = buildWorkbook(service, []);
      const worksheet = workbook.getWorksheet('Documente Makyol')!;

      expect(worksheet).toBeDefined();
      expect(worksheet.rowCount).toBe(1); // Only header row

      // Verify headers still present
      const headerRow = worksheet.getRow(1);
      expect(headerRow.getCell(1).value).toBe('ID');
      expect(headerRow.getCell(13).value).toBe('Încărcat La');
    });
  });

  describe('generateArchive - Excel placement', () => {
    it('should add Excel file at archive root as documente-makyol.xlsx', async () => {
      const archiver = require('archiver');
      const mockArchive = archiver();

      // Reset mocks
      mockArchive.append.mockClear();
      mockArchive.file.mockClear();

      const mockRes = {
        setHeader: jest.fn(),
      } as any;

      await service.generateArchive([], mockRes, 'test.zip');

      // Excel should be appended at root
      expect(mockArchive.append).toHaveBeenCalledWith(
        expect.any(Buffer),
        { name: 'documente-makyol.xlsx' }
      );
    });
  });
});
