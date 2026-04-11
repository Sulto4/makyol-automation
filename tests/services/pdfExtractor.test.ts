import * as fs from 'fs/promises';
import * as path from 'path';
import { PDFExtractorService } from '../../src/services/pdfExtractor';
import {
  PDFNotFoundError,
  PDFPermissionDeniedError,
  PDFCorruptedError,
  PDFEncryptedError,
  PDFScannedError,
  PDFInvalidFormatError,
  PDFInvalidInputError,
  PDFParsingError,
} from '../../src/utils/errors';

describe('PDFExtractorService', () => {
  let extractor: PDFExtractorService;
  const samplePdfPath = path.join(__dirname, '../fixtures/sample.pdf');

  beforeEach(() => {
    extractor = new PDFExtractorService();
  });

  describe('extractFromFile', () => {
    it('should successfully extract text from a valid PDF file', async () => {
      const result = await extractor.extractFromFile(samplePdfPath);

      expect(result).toBeDefined();
      expect(result.text).toBeDefined();
      expect(typeof result.text).toBe('string');
      expect(result.numPages).toBeGreaterThan(0);
      expect(result.text.length).toBeGreaterThan(0);
    });

    it('should throw PDFNotFoundError when file does not exist', async () => {
      const nonExistentPath = path.join(__dirname, '../fixtures/nonexistent.pdf');

      await expect(extractor.extractFromFile(nonExistentPath)).rejects.toThrow(PDFNotFoundError);
      await expect(extractor.extractFromFile(nonExistentPath)).rejects.toThrow(/not found/);
    });

    it('should extract text content from sample PDF', async () => {
      const result = await extractor.extractFromFile(samplePdfPath);

      // Check that extracted text contains expected content
      expect(result.text).toContain('sample');
      expect(result.text).toContain('testing');
    });

    it('should return metadata about the PDF', async () => {
      const result = await extractor.extractFromFile(samplePdfPath);

      expect(result.numPages).toBe(1);
      expect(result.info).toBeDefined();
    });
  });

  describe('extractFromBuffer', () => {
    let sampleBuffer: Buffer;

    beforeEach(async () => {
      sampleBuffer = await fs.readFile(samplePdfPath);
    });

    it('should successfully extract text from a valid PDF buffer', async () => {
      const result = await extractor.extractFromBuffer(sampleBuffer);

      expect(result).toBeDefined();
      expect(result.text).toBeDefined();
      expect(typeof result.text).toBe('string');
      expect(result.numPages).toBeGreaterThan(0);
    });

    it('should throw PDFInvalidInputError when buffer is not a Buffer', async () => {
      await expect(extractor.extractFromBuffer('not a buffer' as any)).rejects.toThrow(PDFInvalidInputError);
      await expect(extractor.extractFromBuffer('not a buffer' as any)).rejects.toThrow(/expected a Buffer/);
    });

    it('should throw PDFInvalidInputError when buffer is empty', async () => {
      const emptyBuffer = Buffer.from([]);

      await expect(extractor.extractFromBuffer(emptyBuffer)).rejects.toThrow(PDFInvalidInputError);
      await expect(extractor.extractFromBuffer(emptyBuffer)).rejects.toThrow(/empty/);
    });

    it('should throw PDFInvalidInputError when buffer is too small', async () => {
      const tinyBuffer = Buffer.from([1, 2, 3]);

      await expect(extractor.extractFromBuffer(tinyBuffer)).rejects.toThrow(PDFInvalidInputError);
      await expect(extractor.extractFromBuffer(tinyBuffer)).rejects.toThrow(/too small/);
    });

    it('should throw PDFInvalidFormatError when buffer does not have PDF signature', async () => {
      const invalidBuffer = Buffer.from('This is not a PDF file, just plain text content here');

      await expect(extractor.extractFromBuffer(invalidBuffer)).rejects.toThrow(PDFInvalidFormatError);
      await expect(extractor.extractFromBuffer(invalidBuffer)).rejects.toThrow(/valid PDF signature/);
    });

    it('should throw PDFCorruptedError when PDF is missing EOF marker', async () => {
      // Create a buffer with PDF signature but no EOF marker
      const corruptedBuffer = Buffer.from('%PDF-1.4\nSome content without EOF');

      await expect(extractor.extractFromBuffer(corruptedBuffer)).rejects.toThrow(PDFCorruptedError);
      await expect(extractor.extractFromBuffer(corruptedBuffer)).rejects.toThrow(/EOF marker/);
    });

    it('should extract same text from buffer as from file', async () => {
      const fileResult = await extractor.extractFromFile(samplePdfPath);
      const bufferResult = await extractor.extractFromBuffer(sampleBuffer);

      expect(bufferResult.text).toBe(fileResult.text);
      expect(bufferResult.numPages).toBe(fileResult.numPages);
    });

    it('should throw PDFScannedError when PDF has minimal extractable text', async () => {
      // Create a minimal PDF with very little text (simulating scanned PDF)
      const scannedPdf = `%PDF-1.4
1 0 obj
<</Type /Catalog /Pages 2 0 R>>
endobj
2 0 obj
<</Type /Pages /Kids [3 0 R] /Count 1>>
endobj
3 0 obj
<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>>
endobj
4 0 obj
<</Length 10>>
stream
BT
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000217 00000 n
trailer
<</Size 5 /Root 1 0 R>>
startxref
280
%%EOF`;

      const scannedBuffer = Buffer.from(scannedPdf);

      await expect(extractor.extractFromBuffer(scannedBuffer)).rejects.toThrow(PDFScannedError);
      await expect(extractor.extractFromBuffer(scannedBuffer)).rejects.toThrow(/scanned/);
    });

    it('should include error details for PDFInvalidFormatError', async () => {
      const invalidBuffer = Buffer.from('INVALID CONTENT HERE FOR TESTING');

      try {
        await extractor.extractFromBuffer(invalidBuffer);
        fail('Expected error to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(PDFInvalidFormatError);
        expect((error as PDFInvalidFormatError).details).toBeDefined();
        expect((error as PDFInvalidFormatError).details.expectedSignature).toBe('%PDF-');
        expect((error as PDFInvalidFormatError).details.actualHeader).toBeDefined();
      }
    });

    it('should include error details for PDFScannedError', async () => {
      const scannedPdf = `%PDF-1.4
1 0 obj
<</Type /Catalog /Pages 2 0 R>>
endobj
2 0 obj
<</Type /Pages /Kids [3 0 R] /Count 1>>
endobj
3 0 obj
<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>>
endobj
4 0 obj
<</Length 10>>
stream
BT
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000217 00000 n
trailer
<</Size 5 /Root 1 0 R>>
startxref
280
%%EOF`;

      try {
        await extractor.extractFromBuffer(Buffer.from(scannedPdf));
        fail('Expected error to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(PDFScannedError);
        expect((error as PDFScannedError).details).toBeDefined();
        expect((error as PDFScannedError).details.numPages).toBeDefined();
        expect((error as PDFScannedError).details.avgCharsPerPage).toBeDefined();
        expect((error as PDFScannedError).details.requiresOCR).toBe(true);
      }
    });
  });

  describe('isValidPDF', () => {
    it('should return true for valid PDF file', async () => {
      const isValid = await extractor.isValidPDF(samplePdfPath);

      expect(isValid).toBe(true);
    });

    it('should return false for non-existent file', async () => {
      const nonExistentPath = path.join(__dirname, '../fixtures/nonexistent.pdf');
      const isValid = await extractor.isValidPDF(nonExistentPath);

      expect(isValid).toBe(false);
    });

    it('should return false for file without PDF signature', async () => {
      // Create a temporary non-PDF file
      const tempFilePath = path.join(__dirname, '../fixtures/temp-not-pdf.txt');
      await fs.writeFile(tempFilePath, 'This is not a PDF file');

      try {
        const isValid = await extractor.isValidPDF(tempFilePath);
        expect(isValid).toBe(false);
      } finally {
        // Clean up
        await fs.unlink(tempFilePath).catch(() => {});
      }
    });

    it('should return false for file that is too small', async () => {
      // Create a temporary file that's too small
      const tempFilePath = path.join(__dirname, '../fixtures/temp-tiny.pdf');
      await fs.writeFile(tempFilePath, 'tiny');

      try {
        const isValid = await extractor.isValidPDF(tempFilePath);
        expect(isValid).toBe(false);
      } finally {
        // Clean up
        await fs.unlink(tempFilePath).catch(() => {});
      }
    });
  });

  describe('extractAndDetectScanned', () => {
    it('should extract text and detect that sample PDF is not scanned', async () => {
      const result = await extractor.extractAndDetectScanned(samplePdfPath);

      expect(result).toBeDefined();
      expect(result.text).toBeDefined();
      expect(result.isScanned).toBe(false);
      expect(result.numPages).toBeGreaterThan(0);
      expect(result.avgCharsPerPage).toBeGreaterThan(100);
    });

    it('should detect scanned PDFs based on low character count', async () => {
      // Create a minimal PDF simulating scanned document
      const scannedPdfPath = path.join(__dirname, '../fixtures/temp-scanned.pdf');
      const scannedPdf = `%PDF-1.4
1 0 obj
<</Type /Catalog /Pages 2 0 R>>
endobj
2 0 obj
<</Type /Pages /Kids [3 0 R] /Count 1>>
endobj
3 0 obj
<</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>>
endobj
4 0 obj
<</Length 10>>
stream
BT
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000217 00000 n
trailer
<</Size 5 /Root 1 0 R>>
startxref
280
%%EOF`;

      await fs.writeFile(scannedPdfPath, scannedPdf);

      try {
        await extractor.extractAndDetectScanned(scannedPdfPath);
        fail('Expected PDFScannedError to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(PDFScannedError);
        expect((error as PDFScannedError).details.numPages).toBe(1);
        expect((error as PDFScannedError).details.avgCharsPerPage).toBeLessThan(50);
      } finally {
        // Clean up
        await fs.unlink(scannedPdfPath).catch(() => {});
      }
    });

    it('should throw PDFNotFoundError when file does not exist', async () => {
      const nonExistentPath = path.join(__dirname, '../fixtures/nonexistent.pdf');

      await expect(extractor.extractAndDetectScanned(nonExistentPath)).rejects.toThrow(PDFNotFoundError);
    });
  });

  describe('getMetadata', () => {
    it('should extract metadata without full text extraction', async () => {
      const metadata = await extractor.getMetadata(samplePdfPath);

      expect(metadata).toBeDefined();
      expect(metadata.numPages).toBe(1);
      expect(metadata.info).toBeDefined();
    });

    it('should throw PDFNotFoundError when file does not exist', async () => {
      const nonExistentPath = path.join(__dirname, '../fixtures/nonexistent.pdf');

      await expect(extractor.getMetadata(nonExistentPath)).rejects.toThrow(PDFNotFoundError);
    });

    it('should be faster than full text extraction', async () => {
      // This is more of a conceptual test - getMetadata should be faster
      const metadataStart = Date.now();
      await extractor.getMetadata(samplePdfPath);
      const metadataTime = Date.now() - metadataStart;

      const fullStart = Date.now();
      await extractor.extractFromFile(samplePdfPath);
      const fullTime = Date.now() - fullStart;

      // Metadata extraction should generally be faster or comparable
      // This is a soft check since small files might not show difference
      expect(metadataTime).toBeLessThanOrEqual(fullTime + 50); // Allow 50ms margin
    });

    it('should return same page count as full extraction', async () => {
      const metadata = await extractor.getMetadata(samplePdfPath);
      const fullResult = await extractor.extractFromFile(samplePdfPath);

      expect(metadata.numPages).toBe(fullResult.numPages);
    });
  });

  describe('error handling', () => {
    it('should properly serialize error to JSON', async () => {
      const nonExistentPath = path.join(__dirname, '../fixtures/nonexistent.pdf');

      try {
        await extractor.extractFromFile(nonExistentPath);
        fail('Expected error to be thrown');
      } catch (error) {
        const json = (error as PDFNotFoundError).toJSON();

        expect(json).toBeDefined();
        expect(json.name).toBe('PDFNotFoundError');
        expect(json.code).toBe('PDF_NOT_FOUND');
        expect(json.message).toBeDefined();
        expect(json.details).toBeDefined();
        expect(json.details.filePath).toBe(nonExistentPath);
      }
    });

    it('should maintain error code in custom errors', async () => {
      const invalidBuffer = Buffer.from('Not a PDF');

      try {
        await extractor.extractFromBuffer(invalidBuffer);
        fail('Expected error to be thrown');
      } catch (error) {
        expect((error as PDFInvalidFormatError).code).toBe('PDF_INVALID_FORMAT');
      }
    });

    it('should include detailed context in error messages', async () => {
      const emptyBuffer = Buffer.from([]);

      try {
        await extractor.extractFromBuffer(emptyBuffer);
        fail('Expected error to be thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(PDFInvalidInputError);
        expect((error as PDFInvalidInputError).message).toContain('empty');
        expect((error as PDFInvalidInputError).details.reason).toBeDefined();
      }
    });
  });

  describe('options handling', () => {
    it('should respect maxPages option', async () => {
      const result = await extractor.extractFromFile(samplePdfPath, { maxPages: 1 });

      expect(result).toBeDefined();
      expect(result.text).toBeDefined();
    });

    it('should respect pageRange option', async () => {
      const result = await extractor.extractFromFile(samplePdfPath, {
        pageRange: { start: 1, end: 1 }
      });

      expect(result).toBeDefined();
      expect(result.text).toBeDefined();
    });
  });
});
