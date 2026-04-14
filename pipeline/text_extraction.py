"""Text extraction from PDF files using multi-engine strategy.

Extraction priority: pdfplumber → PyMuPDF → OCR (Tesseract).
Moved verbatim from clasificare_documente_final.py.
"""

import logging
import io
import os
import re

import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image

from pipeline.config import TESSERACT_CMD, OCR_LANGUAGES, MIN_TEXT_LENGTH

# Configure Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Suppress pdfminer log noise
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfpage").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfinterp").setLevel(logging.WARNING)
logging.getLogger("pdfminer.converter").setLevel(logging.WARNING)
logging.getLogger("pdfminer.pdfdocument").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def _extraction_metrics(pdf_path: str, text: str, engine: str) -> dict:
    """Compute structured metrics for text extraction logging.

    Args:
        pdf_path: Path to the PDF file.
        text: Extracted text content.
        engine: Name of the engine that produced the text.

    Returns:
        Dict of structured metrics for logging.
    """
    filename = os.path.basename(pdf_path)

    # Count pages in PDF
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()
    except Exception:
        page_count = 0

    # Detect Chinese characters (\u4e00-\u9fff range)
    has_chinese_chars = bool(re.search(r'[\u4e00-\u9fff]', text))

    # Average word length (OCR quality indicator — short avg suggests garbled text)
    words = text.split()
    avg_word_length = round(
        sum(len(w) for w in words) / len(words), 1
    ) if words else 0.0

    return {
        "filename": filename,
        "engine": engine,
        "text_length": len(text),
        "page_count": page_count,
        "has_chinese_chars": has_chinese_chars,
        "avg_word_length": avg_word_length,
    }


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF using multi-engine strategy.

    Strategy:
    1. Try pdfplumber (best for digitally-created PDFs)
    2. If insufficient text, try PyMuPDF
    3. If still insufficient, try OCR via Tesseract

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text string. May be empty if all engines fail.
    """
    text = ""
    engine = "none"

    # Engine 1: pdfplumber
    try:
        text = _extract_with_pdfplumber(pdf_path)
        if text.strip():
            engine = "pdfplumber"
        if len(text.strip()) >= MIN_TEXT_LENGTH:
            logger.info("Text extraction result for %s",
                        os.path.basename(pdf_path),
                        extra={"extra_data": _extraction_metrics(
                            pdf_path, text, engine)})
            return text
    except Exception as e:
        logger.warning("pdfplumber failed for %s: %s", pdf_path, e)

    # Engine 2: PyMuPDF
    try:
        text_pymupdf = _extract_with_pymupdf(pdf_path)
        if len(text_pymupdf.strip()) > len(text.strip()):
            text = text_pymupdf
            engine = "pymupdf"
        if len(text.strip()) >= MIN_TEXT_LENGTH:
            logger.info("Text extraction result for %s",
                        os.path.basename(pdf_path),
                        extra={"extra_data": _extraction_metrics(
                            pdf_path, text, engine)})
            return text
    except Exception as e:
        logger.warning("PyMuPDF failed for %s: %s", pdf_path, e)

    # Engine 3: OCR via Tesseract
    try:
        text_ocr = _extract_with_ocr(pdf_path)
        if len(text_ocr.strip()) > len(text.strip()):
            text = text_ocr
            engine = "ocr"
    except Exception as e:
        logger.warning("OCR failed for %s: %s", pdf_path, e)

    logger.info("Text extraction result for %s", os.path.basename(pdf_path),
                extra={"extra_data": _extraction_metrics(
                    pdf_path, text, engine)})
    return text


def extract_full_text(pdf_path: str) -> str:
    """Extract full text from all pages of a PDF.

    Alias/convenience wrapper that returns the complete extracted text.
    Used by the pipeline orchestrator.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Full extracted text from the document.
    """
    return extract_text_from_pdf(pdf_path)


def is_scanned_pdf(text: str) -> bool:
    """Detect if PDF is likely scanned (insufficient extracted text).

    Args:
        text: Extracted text from the PDF.

    Returns:
        True if text length is below threshold (likely scanned).
    """
    return len(text.strip()) < MIN_TEXT_LENGTH


def _extract_with_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber.

    CRITICAL: pdfplumber.extract_text() returns None on empty pages,
    always guard with 'or ""'.
    """
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # CRITICAL: guard against None return
            page_text = page.extract_text() or ""
            pages_text.append(page_text)
    return "\n".join(pages_text)


def _extract_with_pymupdf(pdf_path: str) -> str:
    """Extract text using PyMuPDF (fitz)."""
    pages_text = []
    doc = fitz.open(pdf_path)
    try:
        for page in doc:
            page_text = page.get_text() or ""
            pages_text.append(page_text)
    finally:
        doc.close()
    return "\n".join(pages_text)


def _extract_with_ocr(pdf_path: str) -> str:
    """Extract text using OCR (Tesseract) via PyMuPDF page rendering."""
    pages_text = []
    doc = fitz.open(pdf_path)
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            page_text = pytesseract.image_to_string(image, lang=OCR_LANGUAGES)
            pages_text.append(page_text)
    finally:
        doc.close()
    return "\n".join(pages_text)
