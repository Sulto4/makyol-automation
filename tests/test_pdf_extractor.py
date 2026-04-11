"""
Integration tests for PDFExtractor with OCR functionality.

Tests cover end-to-end extraction from scanned PDFs, mixed documents,
and confidence scoring.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from pathlib import Path

from src.services.pdf_extractor import PDFExtractor, PDFExtractionError


class TestPDFExtractorInitialization:
    """Test PDFExtractor initialization."""

    def test_default_initialization(self):
        """Test PDFExtractor initializes with default parameters."""
        extractor = PDFExtractor()

        assert extractor.min_text_threshold == 10
        assert extractor._ocr_service is None

    def test_custom_threshold(self):
        """Test PDFExtractor with custom text threshold."""
        extractor = PDFExtractor(min_text_threshold=20)

        assert extractor.min_text_threshold == 20

    def test_custom_ocr_service(self):
        """Test PDFExtractor with injected OCR service."""
        mock_ocr = Mock()
        extractor = PDFExtractor(ocr_service=mock_ocr)

        assert extractor._ocr_service is mock_ocr


class TestScannedPDFExtraction:
    """Integration tests for scanned PDF extraction with OCR."""

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_scanned_pdf_extraction(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """
        Test end-to-end extraction of text from a scanned PDF.

        This integration test verifies:
        1. Scanned pages are detected (no text layer)
        2. Pages are routed to OCR service
        3. OCR text is extracted with confidence scores
        4. Metadata is properly generated
        """
        # Setup mock PDF with scanned page (no text)
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # No text = scanned page
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup mock OCR results
        mock_image = Mock()
        mock_convert.return_value = [mock_image]

        # Mock Tesseract OCR data with confidence scores
        mock_img_to_data.return_value = {
            'conf': ['95', '92', '88', '-1'],  # -1 is ignored by Tesseract
            'text': ['CERTIFICATE', 'OF', 'COMPLIANCE', '']
        }

        # Mock extracted text
        expected_text = """CERTIFICATE OF COMPLIANCE

This is to certify that:

Acme Manufacturing Ltd.
123 Industrial Drive

Has been audited and found to be in conformance with
ISO 9001:2015 Quality Management System

Certificate Number: ISO-9001-2024-001
Issue Date: January 15, 2024
Expiry Date: January 14, 2027"""

        mock_img_to_string.return_value = expected_text

        # Execute extraction
        extractor = PDFExtractor()
        result = extractor.extract_text('scanned_certificate.pdf')

        # Verify results
        assert 'full_text' in result
        assert 'ocr_pages' in result
        assert 'page_confidence_scores' in result
        assert 'total_pages' in result

        # Verify OCR was used for the scanned page
        assert len(result['ocr_pages']) == 1
        assert 1 in result['ocr_pages']

        # Verify confidence score was calculated
        assert 1 in result['page_confidence_scores']
        confidence = result['page_confidence_scores'][1]
        assert 0.0 <= confidence <= 1.0

        # Verify text was extracted
        assert len(result['full_text']) > 0
        assert 'CERTIFICATE' in result['full_text'] or expected_text in result['full_text']

        # Verify total pages
        assert result['total_pages'] == 1

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_high_confidence_extraction(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """Test scanned PDF with high OCR confidence (>0.85)."""
        # Setup mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup high-confidence OCR
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_img_to_data.return_value = {
            'conf': ['98', '96', '95', '97'],
            'text': ['HIGH', 'QUALITY', 'SCAN', '!']
        }
        mock_img_to_string.return_value = "HIGH QUALITY SCAN!"

        # Execute
        extractor = PDFExtractor()
        result = extractor.extract_text('high_quality.pdf')
        metadata = extractor.get_extraction_metadata(result)

        # Verify high confidence, no manual review needed
        assert metadata['is_ocr_processed'] is True
        confidence = extractor.calculate_aggregate_confidence(result)
        assert confidence > 0.85
        assert metadata['requires_manual_review'] is False

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_low_confidence_extraction(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """Test scanned PDF with low OCR confidence (<0.85) requiring manual review."""
        # Setup mock PDF
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup low-confidence OCR (poor quality scan)
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_img_to_data.return_value = {
            'conf': ['60', '55', '70', '65'],  # Low confidence scores
            'text': ['Poor', 'Quality', 'Scan', '!']
        }
        mock_img_to_string.return_value = "Poor Quality Scan!"

        # Execute
        extractor = PDFExtractor()
        result = extractor.extract_text('low_quality.pdf')
        metadata = extractor.get_extraction_metadata(result)

        # Verify low confidence flagged for manual review
        assert metadata['is_ocr_processed'] is True
        confidence = extractor.calculate_aggregate_confidence(result)
        assert confidence < 0.85
        assert metadata['requires_manual_review'] is True
        assert 'review_reason' in metadata
        assert 'Low OCR confidence' in metadata['review_reason']


class TestMixedDocumentExtraction:
    """Tests for documents with both text-based and scanned pages."""

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_mixed_document(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """
        Test mixed document with both text-based and scanned pages.

        Verifies:
        1. Text pages are extracted normally
        2. Scanned pages are routed to OCR
        3. Combined text maintains page order
        4. Metadata correctly identifies mixed document type
        """
        # Setup mock PDF with 5 pages: text, scanned, text, scanned, text
        mock_pdf = MagicMock()

        # Page 0: Text-based (50 chars)
        page0 = MagicMock()
        page0.extract_text.return_value = "This is a text-based page with extractable text."

        # Page 1: Scanned (no text)
        page1 = MagicMock()
        page1.extract_text.return_value = ""

        # Page 2: Text-based
        page2 = MagicMock()
        page2.extract_text.return_value = "Another text-based page with normal extraction."

        # Page 3: Scanned (no text)
        page3 = MagicMock()
        page3.extract_text.return_value = ""

        # Page 4: Text-based
        page4 = MagicMock()
        page4.extract_text.return_value = "Final text-based page in the document."

        mock_pdf.pages = [page0, page1, page2, page3, page4]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup OCR for scanned pages
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_img_to_data.return_value = {
            'conf': ['90', '88', '92'],
            'text': ['OCR', 'Extracted', 'Text']
        }

        # Different OCR text for each call
        ocr_texts = [
            "This is OCR extracted text from page 2.",
            "This is OCR extracted text from page 4."
        ]
        mock_img_to_string.side_effect = ocr_texts

        # Execute
        extractor = PDFExtractor(min_text_threshold=10)
        result = extractor.extract_text('mixed_doc.pdf')

        # Verify OCR pages
        assert len(result['ocr_pages']) == 2
        assert 2 in result['ocr_pages']  # Page 2 (1-indexed)
        assert 4 in result['ocr_pages']  # Page 4 (1-indexed)

        # Verify total pages
        assert result['total_pages'] == 5

        # Verify confidence scores for OCR pages only
        assert 2 in result['page_confidence_scores']
        assert 4 in result['page_confidence_scores']

        # Verify combined text contains both text and OCR content
        full_text = result['full_text']
        assert 'text-based page' in full_text.lower()
        assert 'ocr extracted text' in full_text.lower()

        # Verify metadata
        metadata = extractor.get_extraction_metadata(result)
        assert metadata['document_type'] == 'mixed'
        assert metadata['text_pages_count'] == 3
        assert metadata['ocr_pages_count'] == 2
        assert metadata['total_pages'] == 5
        assert metadata['is_ocr_processed'] is True

        # Verify aggregate confidence calculation
        aggregate_confidence = extractor.calculate_aggregate_confidence(result)
        # Should be weighted average: (ocr_scores + 3*1.0) / 5
        # With high OCR scores (~0.90), total should be > 0.85
        assert aggregate_confidence > 0.85

    @patch('src.services.pdf_extractor.pdfplumber.open')
    def test_text_only_document(self, mock_pdfplumber):
        """Test document with only text-based pages (no OCR needed)."""
        # Setup mock PDF with all text pages
        mock_pdf = MagicMock()
        page1 = MagicMock()
        page1.extract_text.return_value = "First text page with plenty of text."
        page2 = MagicMock()
        page2.extract_text.return_value = "Second text page with plenty of text."

        mock_pdf.pages = [page1, page2]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Execute
        extractor = PDFExtractor()
        result = extractor.extract_text('text_only.pdf')

        # Verify no OCR was used
        assert len(result['ocr_pages']) == 0
        assert len(result['page_confidence_scores']) == 0
        assert result['total_pages'] == 2

        # Verify metadata
        metadata = extractor.get_extraction_metadata(result)
        assert metadata['document_type'] == 'text'
        assert metadata['is_ocr_processed'] is False
        assert metadata['text_pages_count'] == 2
        assert metadata['ocr_pages_count'] == 0

        # No manual review needed for text-only documents
        assert 'requires_manual_review' not in metadata or metadata['requires_manual_review'] is False


class TestErrorHandling:
    """Test error handling in PDF extraction."""

    def test_file_not_found(self):
        """Test handling of non-existent PDF file."""
        extractor = PDFExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract_text('nonexistent.pdf')

    @patch('src.services.pdf_extractor.pdfplumber.open')
    def test_invalid_page_number(self, mock_pdfplumber):
        """Test error handling for invalid page numbers."""
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock()]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        extractor = PDFExtractor()

        with pytest.raises(PDFExtractionError, match="Invalid page number"):
            extractor.is_page_scanned('test.pdf', 10)

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    def test_ocr_failure_handling(self, mock_convert, mock_pdfplumber):
        """Test graceful handling of OCR failures."""
        # Setup mock PDF with scanned page
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # OCR fails
        mock_convert.side_effect = Exception("Tesseract not found")

        # Execute - should not crash, but return empty text with 0 confidence
        extractor = PDFExtractor()
        result = extractor.extract_text('test.pdf')

        # Verify graceful degradation
        assert result is not None
        assert result['ocr_pages'] == [1]
        assert result['page_confidence_scores'][1] == 0.0


class TestMetadataGeneration:
    """Test metadata generation for various document types."""

    def test_metadata_for_scanned_document(self):
        """Test metadata generation for fully scanned document."""
        extraction_result = {
            'total_pages': 3,
            'ocr_pages': [1, 2, 3],
            'page_confidence_scores': {1: 0.92, 2: 0.88, 3: 0.90}
        }

        extractor = PDFExtractor()
        metadata = extractor.get_extraction_metadata(extraction_result)

        assert metadata['document_type'] == 'scanned'
        assert metadata['is_ocr_processed'] is True
        assert metadata['ocr_pages_count'] == 3
        assert metadata['text_pages_count'] == 0
        assert metadata['total_pages'] == 3

        # String keys for JSONB compatibility
        assert '1' in metadata['page_confidence_scores']
        assert '2' in metadata['page_confidence_scores']
        assert '3' in metadata['page_confidence_scores']

    def test_metadata_confidence_calculation(self):
        """Test automatic confidence calculation in metadata."""
        extraction_result = {
            'total_pages': 2,
            'ocr_pages': [1],
            'page_confidence_scores': {1: 0.75}  # Low confidence
        }

        extractor = PDFExtractor()
        metadata = extractor.get_extraction_metadata(extraction_result)

        # Should auto-calculate and flag low confidence
        assert metadata['requires_manual_review'] is True
        assert 'review_reason' in metadata


class TestEndToEndIntegration:
    """
    End-to-end integration tests for the complete OCR processing pipeline.

    Tests the full workflow: Upload -> OCR extraction -> Metadata extraction -> Database storage.
    """

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_scanned_certificate_end_to_end(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """
        End-to-end test: Upload scanned certificate -> OCR extraction -> metadata extraction -> database storage.

        This test verifies the complete pipeline for processing a scanned ISO 9001 certificate:
        1. Upload scanned ISO 9001 certificate PDF
        2. Verify extraction_results.extracted_text contains OCR text
        3. Verify extraction_results.confidence_score reflects OCR quality
        4. Verify metadata.is_ocr_processed = true
        5. Verify metadata extraction finds certificate details from OCR text
        6. Verify data structure is ready for database storage
        """
        # Step 1: Setup mock scanned PDF (ISO 9001 certificate)
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""  # No text layer = scanned document
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup OCR to return realistic ISO 9001 certificate text
        mock_image = Mock()
        mock_convert.return_value = [mock_image]

        # High-quality OCR confidence scores
        mock_img_to_data.return_value = {
            'conf': ['95', '92', '94', '96', '93', '91', '95', '94'],
            'text': ['CERTIFICATE', 'OF', 'COMPLIANCE', 'ISO', '9001', '2015', 'Quality', 'Management']
        }

        # Realistic certificate text with extractable metadata
        certificate_text = """CERTIFICATE OF COMPLIANCE

This is to certify that:

Acme Manufacturing Ltd.
123 Industrial Drive, Manufacturing District
Springfield, IL 62701

Has been audited and found to be in conformance with the requirements of:

ISO 9001:2015
Quality Management System

Scope of Certification:
Design, manufacture and supply of industrial components

Certificate Number: ISO-9001-2024-001
Issue Date: January 15, 2024
Expiry Date: January 14, 2027

Certified By: Global Certification Body
Auditor: John Smith, Lead Auditor"""

        mock_img_to_string.return_value = certificate_text

        # Step 2: Execute OCR extraction
        extractor = PDFExtractor()
        extraction_result = extractor.extract_text('scanned_iso9001_certificate.pdf')

        # Step 3: Verify extraction_results.extracted_text contains OCR text
        assert 'full_text' in extraction_result
        extracted_text = extraction_result['full_text']
        assert len(extracted_text) > 0
        assert 'CERTIFICATE OF COMPLIANCE' in extracted_text
        assert 'ISO 9001:2015' in extracted_text
        assert 'Acme Manufacturing Ltd.' in extracted_text

        # Step 4: Verify extraction_results.confidence_score reflects OCR quality
        assert 'page_confidence_scores' in extraction_result
        assert 1 in extraction_result['page_confidence_scores']

        aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
        assert 0.0 <= aggregate_confidence <= 1.0
        assert aggregate_confidence > 0.85  # High quality scan

        # Step 5: Verify metadata.is_ocr_processed = true
        metadata = extractor.get_extraction_metadata(extraction_result)
        assert metadata['is_ocr_processed'] is True
        assert metadata['document_type'] == 'scanned'
        assert metadata['ocr_pages_count'] == 1
        assert metadata['total_pages'] == 1

        # Step 6: Verify metadata extraction finds certificate details from OCR text
        # Simulate metadata extraction patterns (regex matching on extracted text)
        import re

        # Extract certificate number
        cert_number_match = re.search(r'Certificate Number:\s*([A-Z0-9-]+)', extracted_text)
        assert cert_number_match is not None
        certificate_number = cert_number_match.group(1)
        assert certificate_number == 'ISO-9001-2024-001'

        # Extract issue date
        issue_date_match = re.search(r'Issue Date:\s*([A-Za-z]+\s+\d+,\s+\d{4})', extracted_text)
        assert issue_date_match is not None
        issue_date = issue_date_match.group(1)
        assert issue_date == 'January 15, 2024'

        # Extract expiry date
        expiry_date_match = re.search(r'Expiry Date:\s*([A-Za-z]+\s+\d+,\s+\d{4})', extracted_text)
        assert expiry_date_match is not None
        expiry_date = expiry_date_match.group(1)
        assert expiry_date == 'January 14, 2027'

        # Extract standard/compliance type
        standard_match = re.search(r'ISO\s+(\d+):(\d+)', extracted_text)
        assert standard_match is not None
        standard = f"ISO {standard_match.group(1)}:{standard_match.group(2)}"
        assert standard == 'ISO 9001:2015'

        # Extract company name
        company_match = re.search(r'certify that:\s*\n\s*\n\s*([^\n]+)', extracted_text)
        assert company_match is not None
        company_name = company_match.group(1).strip()
        assert company_name == 'Acme Manufacturing Ltd.'

        # Step 7: Verify data structure is ready for database storage
        # Simulate database record structure
        database_record = {
            'document_id': 'doc-123',
            'file_path': 'scanned_iso9001_certificate.pdf',
            'extracted_text': extracted_text,
            'confidence_score': aggregate_confidence,
            'metadata': {
                # OCR-specific metadata
                'is_ocr_processed': metadata['is_ocr_processed'],
                'ocr_pages': metadata['ocr_pages'],
                'page_confidence_scores': metadata['page_confidence_scores'],
                'document_type': metadata['document_type'],
                'requires_manual_review': metadata.get('requires_manual_review', False),

                # Extracted certificate metadata
                'certificate_number': certificate_number,
                'issue_date': issue_date,
                'expiry_date': expiry_date,
                'standard': standard,
                'company_name': company_name,
                'certification_type': 'ISO 9001:2015 Quality Management System'
            },
            'extraction_status': 'completed'
        }

        # Verify all required fields are present
        assert database_record['extracted_text'] is not None
        assert database_record['confidence_score'] > 0.85
        assert database_record['metadata']['is_ocr_processed'] is True
        assert database_record['metadata']['certificate_number'] is not None
        assert database_record['metadata']['requires_manual_review'] is False
        assert database_record['extraction_status'] == 'completed'

        # Verify metadata is JSON-serializable (for JSONB storage)
        import json
        try:
            json_metadata = json.dumps(database_record['metadata'])
            assert json_metadata is not None
        except (TypeError, ValueError) as e:
            pytest.fail(f"Metadata is not JSON-serializable: {e}")

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_low_confidence_certificate_flagged_for_review(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """
        End-to-end test: Verify low-confidence documents are flagged for manual review.

        Tests that poor-quality scans with low OCR confidence are properly flagged
        and include appropriate review reasons in the metadata.
        """
        # Setup mock scanned PDF with poor quality
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = ""
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup OCR with low confidence scores (poor quality scan)
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_img_to_data.return_value = {
            'conf': ['65', '58', '62', '70', '55', '68'],  # Low confidence
            'text': ['CERTIFICATE', 'unclear', 'text', 'poor', 'quality', 'scan']
        }

        # Poor quality OCR text with errors
        certificate_text = """CERTIFICATE 0F C0MPLIANCE

Th1s is t0 certify that:

Acme Manufact_ring Ltd.
123 Industrial Dr1ve

lS0 9OO1:2O15 Qual1ty Management System

Cert1f1cate Number: lS0-9OO1-2O24-OO1
lssue Date: January l5, 2O24"""

        mock_img_to_string.return_value = certificate_text

        # Execute extraction
        extractor = PDFExtractor()
        extraction_result = extractor.extract_text('poor_quality_certificate.pdf')

        # Calculate confidence
        aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
        assert aggregate_confidence < 0.85  # Low confidence

        # Generate metadata
        metadata = extractor.get_extraction_metadata(extraction_result)

        # Verify low-confidence flagging
        assert metadata['is_ocr_processed'] is True
        assert metadata['requires_manual_review'] is True
        assert 'review_reason' in metadata
        assert 'Low OCR confidence' in metadata['review_reason']

        # Verify the confidence score is included in the reason
        assert str(aggregate_confidence)[:4] in metadata['review_reason']

        # Verify database record would be flagged
        database_record = {
            'extracted_text': extraction_result['full_text'],
            'confidence_score': aggregate_confidence,
            'metadata': metadata,
            'extraction_status': 'requires_review'  # Different status for flagged documents
        }

        assert database_record['confidence_score'] < 0.85
        assert database_record['metadata']['requires_manual_review'] is True
        assert database_record['extraction_status'] == 'requires_review'

    @patch('src.services.pdf_extractor.pdfplumber.open')
    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    def test_mixed_document_certificate_with_attachments(self, mock_img_to_string, mock_img_to_data, mock_convert, mock_pdfplumber):
        """
        End-to-end test: Mixed document with scanned certificate + text-based attachments.

        Simulates a realistic scenario where a certificate PDF contains:
        - Page 1: Scanned certificate (requires OCR)
        - Page 2: Text-based attachment (normal extraction)
        - Page 3: Scanned annex (requires OCR)
        """
        # Setup mock PDF with mixed pages
        mock_pdf = MagicMock()

        # Page 1: Scanned certificate
        page1 = MagicMock()
        page1.extract_text.return_value = ""

        # Page 2: Text-based attachment
        page2 = MagicMock()
        page2.extract_text.return_value = """ANNEX TO CERTIFICATE

Additional Information:
- Scope details
- Site locations
- Contact information"""

        # Page 3: Scanned audit notes
        page3 = MagicMock()
        page3.extract_text.return_value = ""

        mock_pdf.pages = [page1, page2, page3]
        mock_pdf.__enter__ = Mock(return_value=mock_pdf)
        mock_pdf.__exit__ = Mock(return_value=False)
        mock_pdfplumber.return_value = mock_pdf

        # Setup OCR for scanned pages
        mock_image = Mock()
        mock_convert.return_value = [mock_image]
        mock_img_to_data.return_value = {
            'conf': ['94', '92', '95', '93'],
            'text': ['Certificate', 'ISO', '9001', 'Compliance']
        }

        ocr_texts = [
            "CERTIFICATE OF COMPLIANCE\nISO 9001:2015\nCertificate Number: ISO-9001-2024-001",
            "AUDIT NOTES\nCompliance verified on January 15, 2024"
        ]
        mock_img_to_string.side_effect = ocr_texts

        # Execute extraction
        extractor = PDFExtractor()
        extraction_result = extractor.extract_text('mixed_certificate.pdf')

        # Verify mixed document handling
        assert extraction_result['total_pages'] == 3
        assert len(extraction_result['ocr_pages']) == 2
        assert 1 in extraction_result['ocr_pages']
        assert 3 in extraction_result['ocr_pages']

        # Verify combined text includes all pages in order
        full_text = extraction_result['full_text']
        assert 'CERTIFICATE OF COMPLIANCE' in full_text
        assert 'ANNEX TO CERTIFICATE' in full_text
        assert 'AUDIT NOTES' in full_text

        # Verify metadata
        metadata = extractor.get_extraction_metadata(extraction_result)
        assert metadata['document_type'] == 'mixed'
        assert metadata['text_pages_count'] == 1
        assert metadata['ocr_pages_count'] == 2
        assert metadata['is_ocr_processed'] is True

        # Verify aggregate confidence (weighted average of OCR + text pages)
        aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
        # (0.94 + 0.94 + 1.0) / 3 ≈ 0.96
        assert aggregate_confidence > 0.85
        assert metadata['requires_manual_review'] is False

        # Verify metadata extraction works on combined text
        import re
        cert_number_match = re.search(r'Certificate Number:\s*([A-Z0-9-]+)', full_text)
        assert cert_number_match is not None
        assert cert_number_match.group(1) == 'ISO-9001-2024-001'
