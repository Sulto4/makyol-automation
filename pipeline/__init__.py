"""Makyol document processing pipeline package."""

import logging
import os
import time
from pathlib import Path

import fitz  # PyMuPDF — used to get page_count for classification

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
        logger.error("Text extraction failed for %s: %s", filename, e,
                     extra={"extra_data": {"filename": filename, "error": str(e)}})
        result["error"] = f"Text extraction failed: {e}"
        return result
    finally:
        duration_ms = (time.time() - t0) * 1000
        logger.info("Text extraction complete", extra={"extra_data": {
            "step": "text_extraction", "filename": filename,
            "duration_ms": round(duration_ms, 1),
            "text_length": len(text) if "text" in dir() else 0,
            "engine_used": "multi-engine",
        }})

    # Step 2: Vision fallback if text is too short
    vision_extraction = None
    if len(text.strip()) < _MIN_TEXT_LENGTH:
        logger.info("Text too short, trying vision fallback", extra={"extra_data": {
            "filename": filename, "text_length": len(text.strip()),
        }})
        result["used_vision"] = True

    # Step 3: Classification
    t0 = time.time()
    try:
        # Extract page_count for text-based classification heuristics
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
        except Exception:
            page_count = 0
        has_tables = False  # Table detection not in pipeline text extractor

        category, confidence, method = classify_document(filename, text, page_count, has_tables)
        result["classification"] = category
        result["confidence"] = confidence
        result["method"] = method
    except Exception as e:
        logger.error("Classification failed for %s: %s", filename, e,
                     extra={"extra_data": {"filename": filename, "error": str(e)}})
        result["error"] = f"Classification failed: {e}"
        return result
    finally:
        duration_ms = (time.time() - t0) * 1000
        logger.info("Classification complete", extra={"extra_data": {
            "step": "classification", "filename": filename,
            "duration_ms": round(duration_ms, 1),
            "category": result.get("classification"),
            "confidence": result.get("confidence"),
            "method": result.get("method"),
        }})

    # Step 4: Extraction (vision fallback or text-based)
    t0 = time.time()
    try:
        if result["used_vision"]:
            vision_extraction = extract_with_vision(pdf_path, category)

        if vision_extraction is not None:
            extraction = vision_extraction
        else:
            extraction = extract_document_data(text, category, filename=filename)
    except Exception as e:
        logger.error("Extraction failed for %s: %s", filename, e,
                     extra={"extra_data": {"filename": filename, "error": str(e)}})
        result["error"] = f"Extraction failed: {e}"
        return result
    finally:
        duration_ms = (time.time() - t0) * 1000
        ext = extraction if "extraction" in dir() else {}
        non_null = len([v for v in ext.values() if v is not None]) if isinstance(ext, dict) else 0
        logger.info("Extraction complete", extra={"extra_data": {
            "step": "extraction", "filename": filename,
            "duration_ms": round(duration_ms, 1),
            "non_null_fields": non_null,
            "total_fields": len(ext) if isinstance(ext, dict) else 0,
        }})

    # Step 4b: Retry extraction if all values are null
    _check_fields = ("companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator")
    try:
        all_null = all(extraction.get(f) is None for f in _check_fields)
        if all_null and len(text.strip()) >= 50:
            logger.warning(
                "First extraction returned all null for %s, retrying...", filename
            )
            extraction = extract_document_data(text, category, filename=filename)
            all_null = all(extraction.get(f) is None for f in _check_fields)
    except Exception as e:
        logger.error("Extraction retry failed for %s: %s", filename, e)

    # If still all-null after retry, flag for review
    if all(extraction.get(f) is None for f in _check_fields):
        logger.warning("All extraction fields are null for %s", filename)
        result["error"] = "AI extraction returned all null fields"
        result["review_status"] = "NEEDS_CHECK"

    # Step 5: Normalize company names and addresses
    t0 = time.time()
    try:
        for field in ("companie", "producator", "distribuitor"):
            raw = extraction.get(field)
            if raw and raw.strip():
                # Hallucination check: verify company name appears in document text
                raw_words = [w for w in raw.strip().lower().split() if len(w) > 3]
                if raw_words:
                    found = sum(1 for w in raw_words if w in text.lower())
                    if found == 0:
                        logger.warning(
                            "Company hallucination detected: '%s' (%s) not found in text — setting to None",
                            raw.strip()[:60], field,
                            extra={"extra_data": {"field": field, "hallucinated_value": raw.strip()[:80]}},
                        )
                        extraction[field] = None
                        continue

                # Garbage check: reject values that look like sentence fragments, not company names
                val = raw.strip()
                val_lower = val.lower()
                val_words = val.split()

                # Reject certification bodies extracted as "companie" on ISO docs
                cert_bodies = [
                    "international management", "management certification",
                    "bureau veritas", "tuv rheinland", "tuv sud", "lloyd",
                    "sgs ", "dekra", "dnv", "eurocert", "iqnet", "srac",
                    "certind", "aeroq", "qualitas", "organism de certificare",
                ]
                if field == "companie" and category == "ISO":
                    if any(cb in val_lower for cb in cert_bodies):
                        logger.warning(
                            "Certification body extracted as companie on ISO doc: '%s' — setting to None",
                            val[:60],
                        )
                        extraction[field] = None
                        continue

                garbage_words = {
                    "pentru", "care", "este", "sunt", "această", "aceasta", "acest",
                    "prin", "dintre", "efectuează", "efectueaza", "importante",
                    "suplimentar", "obligatoriu", "conform", "privind", "referitoare",
                    "persoanele", "persoane", "drumuri", "șosele", "sosele",
                }
                garbage_count = sum(1 for w in val_words if w.lower() in garbage_words)
                if len(val_words) > 6 or garbage_count >= 1:
                    logger.warning(
                        "Garbage company name detected: '%s' (%s) — looks like sentence fragment",
                        val[:60], field,
                        extra={"extra_data": {"field": field, "garbage_value": val[:80]}},
                    )
                    extraction[field] = None
                    continue

                normalized, _ = normalize_company_name(raw)
                extraction[field] = normalized

        for field in ("adresa_producator",):
            raw = extraction.get(field)
            if raw and raw.strip():
                # Hallucination check: verify address actually appears in document text
                raw_lower = raw.strip().lower()
                # Check first meaningful part (before first comma) in document text
                first_part = raw_lower.split(",")[0].strip()
                if len(first_part) > 5 and first_part not in text.lower():
                    logger.warning(
                        "Address hallucination detected: '%s' not found in document text — setting to None",
                        raw.strip()[:60],
                        extra={"extra_data": {"field": field, "hallucinated_value": raw.strip()[:80]}},
                    )
                    extraction[field] = None
                    continue

                normalized, was_matched = normalize_address(raw)
                if was_matched and normalized.lower() != raw.strip().lower():
                    logger.info(
                        "Address mismatch: document says '%s', KB says '%s' — keeping document value",
                        raw.strip()[:60], normalized[:60],
                        extra={"extra_data": {"field": field, "document_value": raw.strip(), "kb_value": normalized}},
                    )
                else:
                    extraction[field] = normalized
        # Date hallucination check: verify extracted date appears in text
        date_val = extraction.get("data_expirare")
        if date_val and text:
            import re as _re
            date_str = str(date_val).strip()
            # Skip non-date values like "2 ani de la receptie", "Pe durata contractului"
            date_match = _re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
            if date_match:
                d, mo, y = date_match.groups()
                _months = {
                    "01": "ianuarie", "02": "februarie", "03": "martie", "04": "aprilie",
                    "05": "mai", "06": "iunie", "07": "iulie", "08": "august",
                    "09": "septembrie", "10": "octombrie", "11": "noiembrie", "12": "decembrie",
                }
                variants = [
                    f"{d}.{mo}.{y}", f"{d}/{mo}/{y}",
                    f"{int(d)}.{int(mo)}.{y}", f"{d.zfill(2)}.{mo.zfill(2)}.{y}",
                    f"{int(d)} {_months.get(mo.zfill(2), '')} {y}",
                ]
                text_lower = text.lower()
                if not any(v.lower() in text_lower for v in variants if v):
                    logger.warning(
                        "Date hallucination detected: '%s' not found in document text — setting to None",
                        date_str,
                        extra={"extra_data": {"hallucinated_date": date_str, "filename": filename}},
                    )
                    extraction["data_expirare"] = None

    except Exception as e:
        logger.warning("Normalization error for %s: %s", filename, e,
                       extra={"extra_data": {"filename": filename, "error": str(e)}})
    finally:
        duration_ms = (time.time() - t0) * 1000
        logger.info("Normalization complete", extra={"extra_data": {
            "step": "normalization", "filename": filename,
            "duration_ms": round(duration_ms, 1),
        }})

    # Step 6: Validation
    t0 = time.time()
    try:
        extraction, review_status = validate_extraction(extraction, category)
    except Exception as e:
        logger.warning("Validation error for %s: %s", filename, e,
                       extra={"extra_data": {"filename": filename, "error": str(e)}})
        review_status = "REVIEW"
    finally:
        duration_ms = (time.time() - t0) * 1000
        logger.info("Validation complete", extra={"extra_data": {
            "step": "validation", "filename": filename,
            "duration_ms": round(duration_ms, 1),
        }})

    result["extraction"] = extraction
    result["review_status"] = review_status
    result["error"] = None

    # Pipeline-complete summary
    total_duration_ms = round((time.time() - pipeline_start) * 1000, 1)
    result["total_duration_ms"] = total_duration_ms
    field_count = len(extraction) if isinstance(extraction, dict) else 0
    non_null_count = len([v for v in extraction.values() if v is not None]) if isinstance(extraction, dict) else 0
    logger.info("Pipeline complete", extra={"extra_data": {
        "step": "pipeline_complete", "filename": filename,
        "total_duration_ms": total_duration_ms,
        "review_status": result["review_status"],
        "used_vision": result["used_vision"],
        "has_error": result["error"] is not None,
        "field_count": field_count,
        "non_null_fields": non_null_count,
        "category": result["classification"],
        "method": result["method"],
    }})

    return result
