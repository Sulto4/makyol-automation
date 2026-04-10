"""Dual-engine PDF text extraction with OCR fallback.

Extraction strategy:
1. pdfplumber (best for text-based PDFs with tables)
2. PyMuPDF basic text extraction (fallback)
3. PyMuPDF OCR extraction with Romanian language support (last resort)
"""

import logging
from pathlib import Path

import pymupdf
import pdfplumber

logger = logging.getLogger(__name__)

# Maximum pages to process per PDF
MAX_PAGES = 10

# Minimum characters to consider extraction successful
MIN_TEXT_LENGTH = 50


def is_scanned_pdf(pdf_path: Path) -> bool:
    """Detect whether a PDF is scanned (image-based) rather than text-based.

    A PDF is considered scanned if pdfplumber extracts very little text
    but the pages contain images.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:MAX_PAGES]
            total_text = "".join(
                (page.extract_text() or "") for page in pages
            ).strip()

            if len(total_text) >= MIN_TEXT_LENGTH:
                return False

        # Check for images via PyMuPDF
        doc = pymupdf.open(pdf_path)
        try:
            for page_num in range(min(len(doc), MAX_PAGES)):
                page = doc[page_num]
                if page.get_images(full=True):
                    return True
        finally:
            doc.close()

        return False
    except Exception:
        logger.exception("Error detecting scanned PDF: %s", pdf_path)
        return False


def _extract_with_pdfplumber(pdf_path: Path) -> str:
    """Extract text using pdfplumber."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:MAX_PAGES]
            texts = []
            for page in pages:
                text = page.extract_text() or ""
                if text.strip():
                    texts.append(text)
            return "\n".join(texts)
    except Exception:
        logger.exception("pdfplumber extraction failed: %s", pdf_path)
        return ""


def _extract_with_pymupdf(pdf_path: Path) -> str:
    """Extract text using PyMuPDF basic text extraction."""
    try:
        doc = pymupdf.open(pdf_path)
        try:
            texts = []
            for page_num in range(min(len(doc), MAX_PAGES)):
                page = doc[page_num]
                text = page.get_text() or ""
                if text.strip():
                    texts.append(text)
            return "\n".join(texts)
        finally:
            doc.close()
    except Exception:
        logger.exception("PyMuPDF basic extraction failed: %s", pdf_path)
        return ""


def _extract_with_ocr(pdf_path: Path) -> str:
    """Extract text using PyMuPDF OCR with Romanian language support."""
    try:
        doc = pymupdf.open(pdf_path)
        try:
            texts = []
            for page_num in range(min(len(doc), MAX_PAGES)):
                page = doc[page_num]
                try:
                    tp = page.get_textpage_ocr(language="ron", dpi=300)
                    text = page.get_text(textpage=tp) or ""
                    if text.strip():
                        texts.append(text)
                except Exception:
                    logger.warning(
                        "OCR failed on page %d of %s", page_num + 1, pdf_path
                    )
            return "\n".join(texts)
        finally:
            doc.close()
    except Exception:
        logger.exception("PyMuPDF OCR extraction failed: %s", pdf_path)
        return ""


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF using a multi-engine fallback strategy.

    Strategy:
        1. Try pdfplumber first (best for structured/text PDFs).
        2. If result is empty/minimal, try PyMuPDF basic extraction.
        3. If still empty, attempt OCR via PyMuPDF (Romanian language).
        4. Return whatever text was found, or empty string on total failure.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text content, or empty string if all methods fail.
    """
    if not pdf_path.exists():
        logger.error("PDF file not found: %s", pdf_path)
        return ""

    logger.info("Extracting text from: %s", pdf_path)

    # Strategy 1: pdfplumber
    text = _extract_with_pdfplumber(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        logger.info(
            "pdfplumber succeeded for %s (%d chars)", pdf_path.name, len(text)
        )
        return text

    logger.debug("pdfplumber returned minimal text for %s, trying PyMuPDF", pdf_path.name)

    # Strategy 2: PyMuPDF basic
    text = _extract_with_pymupdf(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        logger.info(
            "PyMuPDF basic succeeded for %s (%d chars)", pdf_path.name, len(text)
        )
        return text

    logger.debug("PyMuPDF basic returned minimal text for %s, trying OCR", pdf_path.name)

    # Strategy 3: OCR
    text = _extract_with_ocr(pdf_path)
    if len(text.strip()) >= MIN_TEXT_LENGTH:
        logger.info(
            "OCR succeeded for %s (%d chars)", pdf_path.name, len(text)
        )
        return text

    logger.warning("All extraction methods returned minimal text for %s", pdf_path.name)
    return text
