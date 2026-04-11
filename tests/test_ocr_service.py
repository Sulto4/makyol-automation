"""
Unit tests for OCRService.

Tests cover text extraction, confidence calculation, error handling,
and configuration options for OCR processing.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import pytesseract

from src.services.ocr_service import OCRService


class TestOCRServiceInitialization:
    """Test OCRService initialization and configuration."""

    def test_default_initialization(self):
        """Test OCRService initializes with default parameters."""
        service = OCRService()

        assert service.tesseract_lang == 'eng'
        assert service.dpi == 300
        assert service.confidence_threshold == 0.85

    def test_custom_initialization(self):
        """Test OCRService initializes with custom parameters."""
        service = OCRService(tesseract_lang='fra', dpi=600, confidence_threshold=0.90)

        assert service.tesseract_lang == 'fra'
        assert service.dpi == 600
        assert service.confidence_threshold == 0.90


class TestGetPageAsImage:
    """Test PDF page to image conversion."""

    @patch('src.services.ocr_service.convert_from_path')
    def test_successful_page_conversion(self, mock_convert):
        """Test successful conversion of PDF page to image."""
        # Setup
        mock_image = Mock(spec=Image.Image)
        mock_convert.return_value = [mock_image]
        service = OCRService()

        # Execute
        result = service.get_page_as_image('test.pdf', 1)

        # Verify
        assert result == mock_image
        mock_convert.assert_called_once_with(
            'test.pdf',
            dpi=300,
            first_page=1,
            last_page=1
        )

    @patch('src.services.ocr_service.convert_from_path')
    def test_custom_dpi_conversion(self, mock_convert):
        """Test page conversion with custom DPI setting."""
        mock_image = Mock(spec=Image.Image)
        mock_convert.return_value = [mock_image]
        service = OCRService(dpi=600)

        result = service.get_page_as_image('test.pdf', 2)

        assert result == mock_image
        mock_convert.assert_called_once_with(
            'test.pdf',
            dpi=600,
            first_page=2,
            last_page=2
        )

    @patch('src.services.ocr_service.convert_from_path')
    def test_invalid_page_number(self, mock_convert):
        """Test error handling for invalid page numbers."""
        service = OCRService()

        with pytest.raises(ValueError, match="Page number must be >= 1"):
            service.get_page_as_image('test.pdf', 0)

        with pytest.raises(ValueError, match="Page number must be >= 1"):
            service.get_page_as_image('test.pdf', -1)

    @patch('src.services.ocr_service.convert_from_path')
    def test_empty_image_list(self, mock_convert):
        """Test handling when no images are generated."""
        mock_convert.return_value = []
        service = OCRService()

        result = service.get_page_as_image('test.pdf', 1)

        assert result is None

    @patch('src.services.ocr_service.convert_from_path')
    def test_file_not_found_error(self, mock_convert):
        """Test handling of missing PDF file."""
        mock_convert.side_effect = FileNotFoundError("PDF not found")
        service = OCRService()

        with pytest.raises(FileNotFoundError):
            service.get_page_as_image('missing.pdf', 1)


class TestExtractTextFromPageImage:
    """Test OCR text extraction from images."""

    @patch('src.services.ocr_service.pytesseract.image_to_string')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    def test_successful_text_extraction(self, mock_image_to_data, mock_image_to_string):
        """Test successful OCR text extraction with confidence."""
        # Setup
        mock_image = Mock(spec=Image.Image)
        mock_image_to_string.return_value = "Test extracted text"
        mock_image_to_data.return_value = {
            'conf': [95, 92, 88, -1, 90]
        }
        service = OCRService()

        # Execute
        text, confidence = service.extract_text_from_page_image(mock_image)

        # Verify
        assert text == "Test extracted text"
        assert 0.0 <= confidence <= 1.0
        mock_image_to_string.assert_called_once_with(mock_image, lang='eng')
        mock_image_to_data.assert_called_once_with(
            mock_image,
            lang='eng',
            output_type=pytesseract.Output.DICT
        )

    @patch('src.services.ocr_service.pytesseract.image_to_string')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    def test_custom_language_extraction(self, mock_image_to_data, mock_image_to_string):
        """Test OCR with custom language setting."""
        mock_image = Mock(spec=Image.Image)
        mock_image_to_string.return_value = "Texte français"
        mock_image_to_data.return_value = {
            'conf': [85, 90]
        }
        service = OCRService(tesseract_lang='fra')

        text, confidence = service.extract_text_from_page_image(mock_image)

        assert text == "Texte français"
        mock_image_to_string.assert_called_once_with(mock_image, lang='fra')
        mock_image_to_data.assert_called_once_with(
            mock_image,
            lang='fra',
            output_type=pytesseract.Output.DICT
        )

    @patch('src.services.ocr_service.pytesseract.image_to_string')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    def test_tesseract_not_found_error(self, mock_image_to_data, mock_image_to_string):
        """Test handling when Tesseract is not installed."""
        mock_image = Mock(spec=Image.Image)
        mock_image_to_data.side_effect = pytesseract.TesseractNotFoundError()
        service = OCRService()

        with pytest.raises(RuntimeError, match="Tesseract OCR is not installed"):
            service.extract_text_from_page_image(mock_image)

    @patch('src.services.ocr_service.pytesseract.image_to_string')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    def test_ocr_extraction_failure(self, mock_image_to_data, mock_image_to_string):
        """Test handling of OCR extraction errors."""
        mock_image = Mock(spec=Image.Image)
        mock_image_to_data.side_effect = Exception("OCR failed")
        service = OCRService()

        with pytest.raises(RuntimeError, match="OCR extraction failed"):
            service.extract_text_from_page_image(mock_image)


class TestCalculateConfidenceScore:
    """Test confidence score calculation."""

    def test_valid_confidence_scores(self):
        """Test confidence calculation with valid scores."""
        service = OCRService()
        ocr_data = {
            'conf': [95, 90, 85, -1, 92, 88]  # -1 should be filtered
        }

        confidence = service.calculate_confidence_score(ocr_data)

        # Average of [95, 90, 85, 92, 88] = 90.0, normalized to 0.90
        assert confidence == pytest.approx(0.90, rel=0.01)

    def test_high_confidence_scores(self):
        """Test confidence calculation with high scores."""
        service = OCRService()
        ocr_data = {
            'conf': [98, 99, 97, 100]
        }

        confidence = service.calculate_confidence_score(ocr_data)

        # Average of [98, 99, 97, 100] = 98.5, normalized to 0.985
        assert confidence == pytest.approx(0.985, rel=0.01)

    def test_low_confidence_scores(self):
        """Test confidence calculation with low scores."""
        service = OCRService()
        ocr_data = {
            'conf': [50, 45, 55, 48]
        }

        confidence = service.calculate_confidence_score(ocr_data)

        # Average of [50, 45, 55, 48] = 49.5, normalized to 0.495
        assert confidence == pytest.approx(0.495, rel=0.01)

    def test_filtered_negative_values(self):
        """Test that -1 values are filtered from confidence calculation."""
        service = OCRService()
        ocr_data = {
            'conf': [-1, -1, 80, -1, 90, -1]
        }

        confidence = service.calculate_confidence_score(ocr_data)

        # Average of [80, 90] = 85.0, normalized to 0.85
        assert confidence == pytest.approx(0.85, rel=0.01)

    def test_all_negative_values(self):
        """Test handling when all confidence values are -1."""
        service = OCRService()
        ocr_data = {
            'conf': [-1, -1, -1]
        }

        confidence = service.calculate_confidence_score(ocr_data)

        assert confidence == 0.0

    def test_empty_confidence_list(self):
        """Test handling of empty confidence list."""
        service = OCRService()
        ocr_data = {
            'conf': []
        }

        confidence = service.calculate_confidence_score(ocr_data)

        assert confidence == 0.0

    def test_missing_conf_key(self):
        """Test handling when 'conf' key is missing."""
        service = OCRService()
        ocr_data = {}

        confidence = service.calculate_confidence_score(ocr_data)

        assert confidence == 0.0

    def test_exception_handling(self):
        """Test error handling in confidence calculation."""
        service = OCRService()
        ocr_data = {
            'conf': ['invalid', 'data']
        }

        confidence = service.calculate_confidence_score(ocr_data)

        # Should return 0.0 on error
        assert confidence == 0.0


class TestProcessPdfPage:
    """Test end-to-end PDF page processing."""

    @patch.object(OCRService, 'get_page_as_image')
    @patch.object(OCRService, 'extract_text_from_page_image')
    def test_successful_page_processing(self, mock_extract, mock_get_image):
        """Test successful end-to-end page processing."""
        # Setup
        mock_image = Mock(spec=Image.Image)
        mock_get_image.return_value = mock_image
        mock_extract.return_value = ("Extracted text content", 0.92)
        service = OCRService(confidence_threshold=0.85)

        # Execute
        result = service.process_pdf_page('test.pdf', 1)

        # Verify
        assert result['text'] == "Extracted text content"
        assert result['confidence'] == 0.92
        assert result['page_number'] == 1
        assert result['requires_review'] is False  # 0.92 >= 0.85

    @patch.object(OCRService, 'get_page_as_image')
    @patch.object(OCRService, 'extract_text_from_page_image')
    def test_low_confidence_requires_review(self, mock_extract, mock_get_image):
        """Test that low confidence pages are flagged for review."""
        mock_image = Mock(spec=Image.Image)
        mock_get_image.return_value = mock_image
        mock_extract.return_value = ("Low quality text", 0.75)
        service = OCRService(confidence_threshold=0.85)

        result = service.process_pdf_page('test.pdf', 2)

        assert result['text'] == "Low quality text"
        assert result['confidence'] == 0.75
        assert result['page_number'] == 2
        assert result['requires_review'] is True  # 0.75 < 0.85

    @patch.object(OCRService, 'get_page_as_image')
    @patch.object(OCRService, 'extract_text_from_page_image')
    def test_custom_threshold(self, mock_extract, mock_get_image):
        """Test processing with custom confidence threshold."""
        mock_image = Mock(spec=Image.Image)
        mock_get_image.return_value = mock_image
        mock_extract.return_value = ("Text content", 0.88)
        service = OCRService(confidence_threshold=0.90)

        result = service.process_pdf_page('test.pdf', 1)

        assert result['confidence'] == 0.88
        assert result['requires_review'] is True  # 0.88 < 0.90

    @patch.object(OCRService, 'get_page_as_image')
    def test_image_conversion_failure(self, mock_get_image):
        """Test handling when image conversion fails."""
        mock_get_image.return_value = None
        service = OCRService()

        with pytest.raises(RuntimeError, match="Failed to convert page .* to image"):
            service.process_pdf_page('test.pdf', 1)

    @patch.object(OCRService, 'get_page_as_image')
    @patch.object(OCRService, 'extract_text_from_page_image')
    def test_extraction_error_propagation(self, mock_extract, mock_get_image):
        """Test that extraction errors are propagated."""
        mock_image = Mock(spec=Image.Image)
        mock_get_image.return_value = mock_image
        mock_extract.side_effect = RuntimeError("OCR failed")
        service = OCRService()

        with pytest.raises(RuntimeError, match="OCR failed"):
            service.process_pdf_page('test.pdf', 1)

    @patch.object(OCRService, 'get_page_as_image')
    @patch.object(OCRService, 'extract_text_from_page_image')
    def test_boundary_confidence_threshold(self, mock_extract, mock_get_image):
        """Test exact threshold boundary behavior."""
        mock_image = Mock(spec=Image.Image)
        mock_get_image.return_value = mock_image
        service = OCRService(confidence_threshold=0.85)

        # Exactly at threshold - should NOT require review
        mock_extract.return_value = ("Text at threshold", 0.85)
        result = service.process_pdf_page('test.pdf', 1)
        assert result['requires_review'] is False

        # Just below threshold - should require review
        mock_extract.return_value = ("Text below threshold", 0.8499)
        result = service.process_pdf_page('test.pdf', 2)
        assert result['requires_review'] is True


class TestOCRServiceIntegration:
    """Integration tests for OCRService workflow."""

    @patch('src.services.ocr_service.convert_from_path')
    @patch('src.services.ocr_service.pytesseract.image_to_string')
    @patch('src.services.ocr_service.pytesseract.image_to_data')
    def test_complete_workflow(self, mock_image_to_data, mock_image_to_string, mock_convert):
        """Test complete OCR workflow from PDF to final result."""
        # Setup
        mock_image = Mock(spec=Image.Image)
        mock_convert.return_value = [mock_image]
        mock_image_to_string.return_value = "Complete workflow test"
        mock_image_to_data.return_value = {
            'conf': [95, 90, 92, -1, 88]
        }
        service = OCRService()

        # Execute
        result = service.process_pdf_page('document.pdf', 1)

        # Verify all steps were called
        mock_convert.assert_called_once()
        mock_image_to_data.assert_called_once()
        mock_image_to_string.assert_called_once()

        # Verify result structure
        assert 'text' in result
        assert 'confidence' in result
        assert 'page_number' in result
        assert 'requires_review' in result
        assert result['text'] == "Complete workflow test"
        assert result['page_number'] == 1
