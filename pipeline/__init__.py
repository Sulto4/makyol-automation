"""Makyol document processing pipeline package."""

import logging
import os
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
    try:
        text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        logger.error("Text extraction failed for %s: %s", filename, e)
        result["error"] = f"Text extraction failed: {e}"
        return result

    # Step 2: Vision fallback if text is too short
    vision_extraction = None
    if len(text.strip()) < _MIN_TEXT_LENGTH:
        logger.info("Text too short (%d chars) for %s, trying vision fallback",
                     len(text.strip()), filename)
        result["used_vision"] = True

    # Step 3: Classification
    try:
        category, confidence, method = classify_document(filename, text)
        result["classification"] = category
        result["confidence"] = confidence
        result["method"] = method
    except Exception as e:
        logger.error("Classification failed for %s: %s", filename, e)
        result["error"] = f"Classification failed: {e}"
        return result

    # Step 4: Extraction (vision fallback or text-based)
    try:
        if result["used_vision"]:
            vision_extraction = extract_with_vision(pdf_path, category)

        if vision_extraction is not None:
            extraction = vision_extraction
        else:
            extraction = extract_document_data(text, category, filename=filename)
    except Exception as e:
        logger.error("Extraction failed for %s: %s", filename, e)
        result["error"] = f"Extraction failed: {e}"
        return result

    # Step 4b: All-null detection — if AI returned nothing useful, flag for review
    _check_fields = ("companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator")
    if all(extraction.get(f) is None for f in _check_fields):
        logger.warning("All extraction fields are null for %s", filename)
        result["extraction"] = extraction
        result["error"] = "AI extraction returned all null fields"
        result["review_status"] = "NEEDS_CHECK"
        return result

    # Step 5: Normalize company names and addresses
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

    # Step 6: Validation
    try:
        extraction, review_status = validate_extraction(extraction, category)
    except Exception as e:
        logger.warning("Validation error for %s: %s", filename, e)
        review_status = "REVIEW"

    result["extraction"] = extraction
    result["review_status"] = review_status
    result["error"] = None

    return result
