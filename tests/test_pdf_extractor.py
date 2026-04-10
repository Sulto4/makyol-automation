"""Unit tests for pdf_extractor module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.pdf_extractor import extract_pdf_text, is_scanned_pdf


class TestExtractPdfText:
    """Test text extraction with mocked PDF engines."""

    def test_nonexistent_file_returns_empty(self, tmp_path):
        """Nonexistent file should return empty string."""
        result = extract_pdf_text(tmp_path / "nonexistent.pdf")
        assert result == ""

    @patch("src.pdf_extractor._extract_with_pdfplumber")
    def test_pdfplumber_success(self, mock_plumber, tmp_path):
        """When pdfplumber returns enough text, use it directly."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")

        mock_plumber.return_value = "A" * 100
        result = extract_pdf_text(pdf_file)
        assert result == "A" * 100
        mock_plumber.assert_called_once()

    @patch("src.pdf_extractor._extract_with_ocr")
    @patch("src.pdf_extractor._extract_with_pymupdf")
    @patch("src.pdf_extractor._extract_with_pdfplumber")
    def test_fallback_to_pymupdf(self, mock_plumber, mock_pymupdf, mock_ocr, tmp_path):
        """When pdfplumber returns minimal text, fall back to PyMuPDF."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_plumber.return_value = "short"
        mock_pymupdf.return_value = "B" * 100
        result = extract_pdf_text(pdf_file)
        assert result == "B" * 100
        mock_pymupdf.assert_called_once()
        mock_ocr.assert_not_called()

    @patch("src.pdf_extractor._extract_with_ocr")
    @patch("src.pdf_extractor._extract_with_pymupdf")
    @patch("src.pdf_extractor._extract_with_pdfplumber")
    def test_fallback_to_ocr(self, mock_plumber, mock_pymupdf, mock_ocr, tmp_path):
        """When both pdfplumber and PyMuPDF fail, fall back to OCR."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_plumber.return_value = "short"
        mock_pymupdf.return_value = "also short"
        mock_ocr.return_value = "C" * 100
        result = extract_pdf_text(pdf_file)
        assert result == "C" * 100
        mock_ocr.assert_called_once()

    @patch("src.pdf_extractor._extract_with_ocr")
    @patch("src.pdf_extractor._extract_with_pymupdf")
    @patch("src.pdf_extractor._extract_with_pdfplumber")
    def test_all_methods_fail(self, mock_plumber, mock_pymupdf, mock_ocr, tmp_path):
        """When all methods return minimal text, return whatever OCR gave."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake")

        mock_plumber.return_value = ""
        mock_pymupdf.return_value = ""
        mock_ocr.return_value = "tiny"
        result = extract_pdf_text(pdf_file)
        assert result == "tiny"


class TestIsScannedPdf:
    """Test scanned PDF detection."""

    @patch("src.pdf_extractor.pymupdf")
    @patch("src.pdf_extractor.pdfplumber")
    def test_text_pdf_not_scanned(self, mock_plumber, mock_pymupdf, tmp_path):
        """A PDF with sufficient text is not scanned."""
        pdf_file = tmp_path / "text.pdf"
        pdf_file.write_bytes(b"%PDF-1.4")

        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "A" * 100
        mock_pdf.pages = [mock_page]
        mock_plumber.open.return_value.__enter__ = MagicMock(return_value=mock_pdf)
        mock_plumber.open.return_value.__exit__ = MagicMock(return_value=False)

        assert is_scanned_pdf(pdf_file) is False

    def test_error_handling_returns_false(self, tmp_path):
        """If file doesn't exist or errors, return False."""
        result = is_scanned_pdf(tmp_path / "nonexistent.pdf")
        assert result is False
