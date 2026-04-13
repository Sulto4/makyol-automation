"""Makyol document processing pipeline package."""

import logging
import os
import time
from pathlib import Path

from pipeline.text_extraction import extract_text_from_pdf
from pipeline.classification import classify_document
from pipeline.extraction import extract_document_data
from pipeline.normalization import normalize_company_name, normalize_address
from pipeline.validation import validate_extraction
from pipeline.vision_fallback import extract_with_vision

logger = logging.getLogger(__name__)

# Minimum text length before triggering vision fallback
_MIN_TEXT_LENGTH = 20


def process_document(pdf_path: str, filename: str = "") -> dict:
    """Orchestrate the full document processing pipeline.

    Flow:
        1. Extract text from PDF (multi-engine: pdfplumber → PyMuPDF → OCR)
        2. If text < 20 chars → vision fallback via Gemini
        3. Classify document (filename → text → AI cascade)
        4. Extract structured data with AI
        5. Normalize company names via knowledge base fuzzy matching
        6. Validate extraction against schema constraints
        7. Return structured result dict

    Args:
        pdf_path: Path to the PDF file.
        filename: Original filename (used for classification). If empty,
                  derived from pdf_path.

    Returns:
        Dict with keys: classification, confidence, method, extraction,
        review_status, used_vision, error (if any).
    """
    pipeline_start = time.time()

    if not filename:
        filename = os.path.basename(pdf_path)

    result = {
        "filename": filename,
        "classification": None,
        "confidence": 0.0,
        "method": None,
        "extraction": {},
        "review_status": "FAILED",
        "used_vision": False,
        "error": None,
    }

    # Step 1: Text extraction
    t0 = time.time()
    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        logger.error("Text extraction failed for %s: %s", filename, e)
        result["error"] = f"Text extraction failed: {e}"
        return result
    finally:
        logger.info("pipeline.text_extraction took %.0f ms for %s",
                     (time.time() - t0) * 1000, filename)

    # Step 2: Vision fallback if text is too short
    vision_extraction = None
    if len(text.strip()) < _MIN_TEXT_LENGTH:
        logger.info("Text too short (%d chars) for %s, trying vision fallback",
                     len(text.strip()), filename)
        result["used_vision"] = True

    # Step 3: Classification
    t0 = time.time()
    try:
        category, confidence, method = classify_document(filename, text)
        result["classification"] = category
        result["confidence"] = confidence
        result["method"] = method
    except Exception as e:
        logger.error("Classification failed for %s: %s", filename, e)
        result["error"] = f"Classification failed: {e}"
        return result
    finally:
        logger.info("pipeline.classification took %.0f ms for %s",
                     (time.time() - t0) * 1000, filename)

    # Step 4: Extraction (vision fallback or text-based)
    t0 = time.time()
    try:
        if result["used_vision"]:
            vision_extraction = extract_with_vision(pdf_path, category)

        if vision_extraction is not None:
            extraction = vision_extraction
        else:
            extraction = extract_document_data(text, category)
    except Exception as e:
        logger.error("Extraction failed for %s: %s", filename, e)
        result["error"] = f"Extraction failed: {e}"
        return result
    finally:
        logger.info("pipeline.extraction took %.0f ms for %s",
                     (time.time() - t0) * 1000, filename)

    # Step 5: Normalize company names and addresses
    t0 = time.time()
    try:
        for field in ("companie", "producator", "distribuitor"):
            raw = extraction.get(field)
            if raw and raw.strip():
                normalized, _ = normalize_company_name(raw)
                extraction[field] = normalized

        for field in ("adresa_producator", "adresa_distribuitor"):
            raw = extraction.get(field)
            if raw and raw.strip():
                normalized, _ = normalize_address(raw)
                extraction[field] = normalized
    except Exception as e:
        logger.warning("Normalization error for %s: %s", filename, e)
    finally:
        logger.info("pipeline.normalization took %.0f ms for %s",
                     (time.time() - t0) * 1000, filename)

    # Step 6: Validation
    t0 = time.time()
    try:
        extraction, review_status = validate_extraction(extraction, category)
    except Exception as e:
        logger.warning("Validation error for %s: %s", filename, e)
        review_status = "REVIEW"
    finally:
        logger.info("pipeline.validation took %.0f ms for %s",
                     (time.time() - t0) * 1000, filename)

    result["extraction"] = extraction
    result["review_status"] = review_status
    result["error"] = None

    # Pipeline-complete summary
    total_duration_ms = (time.time() - pipeline_start) * 1000
    field_count = len(extraction) if isinstance(extraction, dict) else 0
    logger.info(
        "pipeline.complete file=%s total_duration_ms=%.0f review_status=%s "
        "used_vision=%s has_error=%s field_count=%d",
        filename, total_duration_ms, result["review_status"],
        result["used_vision"], result["error"] is not None, field_count,
    )

    return result
