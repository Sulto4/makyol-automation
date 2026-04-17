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


def get_page_count(pdf_path: str) -> int:
    """Return the number of pages in a PDF, or 0 if it can't be opened.

    Used by the pipeline orchestrator for classification heuristics so it
    doesn't have to import fitz directly or duplicate the open-then-close
    boilerplate.
    """
    try:
        doc = fitz.open(pdf_path)
        try:
            return len(doc)
        finally:
            doc.close()
    except Exception:
        return 0


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


def _run_engine(engine_name: str, fn, pdf_path: str, engine_attempts: list[dict]) -> str:
    """Run a text extraction engine and record its timing/outcome.

    Returns the extracted text (empty string on failure). Side-effect:
    appends an attempt dict to `engine_attempts`. Keeping this helper
    makes the race in extract_text_from_pdf read top-to-bottom without
    repeating the try/except/timing pattern three times.
    """
    import time as _time
    t0 = _time.time()
    try:
        text = fn(pdf_path) or ""
        engine_attempts.append({
            "engine": engine_name, "ok": True,
            "text_length": len(text),
            "duration_ms": round((_time.time() - t0) * 1000, 1),
        })
        return text
    except Exception as e:
        engine_attempts.append({
            "engine": engine_name, "ok": False,
            "error": str(e),
            "duration_ms": round((_time.time() - t0) * 1000, 1),
        })
        logger.warning("%s failed for %s: %s", engine_name, pdf_path, e,
                       extra={"extra_data": {
                           "step": "text_extraction",
                           "engine": engine_name, "error": str(e),
                       }})
        return ""


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF using multi-engine strategy.

    Strategy:
    1. Race pdfplumber and PyMuPDF in parallel (both are fast, ms–100s of
       ms; running them concurrently costs no extra latency on the happy
       path and halves the worst case when pdfplumber is slow).
    2. Apply preference: pdfplumber wins if it returned ≥MIN_TEXT_LENGTH;
       otherwise take whichever produced more text. Preserves the prior
       ordering so there's no quality regression vs the serial version.
    3. Only if both fast engines gave insufficient text do we pay for OCR.

    Both the text engine race and the OCR fallback submit into the
    process-wide pools from pipeline.thread_pools so total concurrent
    work is bounded even under heavy batch load.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text string. May be empty if all engines fail.
    """
    from pipeline.thread_pools import TEXT_ENGINE_POOL

    filename = os.path.basename(pdf_path)
    engine_attempts: list[dict] = []

    # Engines 1 + 2 in parallel: pdfplumber and PyMuPDF.
    plumber_fut = TEXT_ENGINE_POOL.submit(
        _run_engine, "pdfplumber", _extract_with_pdfplumber, pdf_path, engine_attempts,
    )
    pymupdf_fut = TEXT_ENGINE_POOL.submit(
        _run_engine, "pymupdf", _extract_with_pymupdf, pdf_path, engine_attempts,
    )
    text_plumber = plumber_fut.result()
    text_pymupdf = pymupdf_fut.result()

    # Preference mirrors the old serial logic: pdfplumber wins when it
    # produced usable text; otherwise take the longer of the two.
    if len(text_plumber.strip()) >= MIN_TEXT_LENGTH:
        text, engine = text_plumber, "pdfplumber"
    elif len(text_pymupdf.strip()) > len(text_plumber.strip()):
        text, engine = text_pymupdf, "pymupdf"
    else:
        text, engine = text_plumber, ("pdfplumber" if text_plumber else "none")

    # Engine 3: OCR fallback — only if neither cheap engine produced enough.
    if len(text.strip()) < MIN_TEXT_LENGTH:
        text_ocr = _run_engine("ocr", _extract_with_ocr, pdf_path, engine_attempts)
        if len(text_ocr.strip()) > len(text.strip()):
            text, engine = text_ocr, "ocr"

    metrics = _extraction_metrics(pdf_path, text, engine)
    metrics["engine_attempts"] = engine_attempts
    logger.info("Text extraction result for %s", filename,
                extra={"extra_data": metrics})
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
    """Extract text using OCR (Tesseract) via PyMuPDF page rendering.

    Pages are rendered + OCR'd through the process-wide OCR_POOL, so the
    total number of concurrent Tesseract invocations is capped regardless
    of how many docs the backend is feeding us. Each 300-DPI page pixmap
    is ~5–15 MB in memory during OCR and Tesseract holds a CPU for 1–3 s
    per page, so unbounded per-doc parallelism was the root cause of the
    CPU saturation we saw at concurrency=5.
    """
    from pipeline.thread_pools import OCR_POOL

    doc = fitz.open(pdf_path)
    try:
        page_count = len(doc)
        if page_count == 0:
            return ""

        def _ocr_one(idx: int) -> str:
            pix = doc[idx].get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            return pytesseract.image_to_string(image, lang=OCR_LANGUAGES) or ""

        pages_text = list(OCR_POOL.map(_ocr_one, range(page_count)))
    finally:
        doc.close()
    return "\n".join(pages_text)
