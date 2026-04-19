"""Makyol document processing pipeline package."""

import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path

from pipeline.config import settings
from pipeline.text_extraction import extract_text_from_pdf, get_page_count
from pipeline.classification import classify_document
from pipeline.date_normalizer import scan_filename_dates
from pipeline.extraction import (
    CATEGORIES_WITH_DATA_EXPIRARE,
    extract_document_data,
    normalize_extraction_result,
)
from pipeline.normalization import normalize_company_name, normalize_address
from pipeline.validation import validate_extraction
from pipeline.vision_fallback import _pdf_pages_to_base64, extract_with_vision

logger = logging.getLogger(__name__)

# Vision is now applied to every document. Text extraction still runs so the
# classifier has filename + body text to work with, but extraction itself
# always goes through the vision model.
_USE_VISION_FOR_ALL = True

# Categories where we trust a trailing DD_MM_YYYY.pdf as a hint about the
# expiration date — same set that is allowed to carry data_expirare at all.
# (G4) The fallback only fires when the AI returned nothing for data_expirare.
_FILENAME_EXPIRY_CATEGORIES = CATEGORIES_WITH_DATA_EXPIRARE

# Filename-date scanning (numeric + text-month) is delegated to
# pipeline.date_normalizer.scan_filename_dates so the same logic covers
# VLR 004.10_..._24_07_2028.pdf AND
# Fisa tehnica ..._11noiembrie 2024.pdf in one place.

# G5: if an extracted date is in the past by more than this many days AND the
# filename does not corroborate it, we flag the document for review instead
# of silently trusting what the AI returned. Six months is the threshold
# because legitimate expirations that just passed (weeks ago) should still
# be shown as expired without extra friction.
_SUSPICIOUS_PAST_EXPIRY_DAYS = 180

# Categories where the `companie` field on the output represents the
# manufacturer/applicant, not the certifying body. The cert_bodies filter
# inside normalize() guards companie against stray TÜV/SRAC/MDRAP values on
# these categories. Module-level so the companie→producator fallback can
# reuse it.
CATEGORIES_WITH_CERT_BODY_FILTER = {
    "ISO",
    "AVIZ_TEHNIC",
    "AVIZ_TEHNIC_SI_AGREMENT",
    "AGREMENT",
}


def _parse_ddmmyyyy(s: str) -> date | None:
    """Parse a DD.MM.YYYY / DD-MM-YYYY / DD_MM_YYYY string. Returns None on
    any malformed value (including non-date durations like '2 ani')."""
    if not s:
        return None
    m = re.match(r"^\s*(\d{1,2})[._\-/](\d{1,2})[._\-/](\d{4})\s*$", s)
    if not m:
        return None
    d, mo, y = (int(g) for g in m.groups())
    try:
        return date(y, mo, d)
    except ValueError:
        return None


def _filename_expiry_candidates(filename: str) -> list[date]:
    """Pull every plausible expiry date out of a filename.

    Covers both numeric (DD_MM_YYYY) and text-month variants
    ("11noiembrie2024", "21nov2027"). Filters out anything older than
    last year so document-code dates stamped in filenames don't
    accidentally become candidate expirations.
    """
    cutoff_year = datetime.now().year - 1
    out: list[date] = []
    for d in scan_filename_dates(filename):
        if d.year < cutoff_year:
            continue
        out.append(d)
    return out


def _filename_contains_date(filename: str, d: date) -> bool:
    """Check if the filename contains the given date in any common format."""
    stem = filename.lower()
    ddmm = [
        f"{d.day:02d}.{d.month:02d}.{d.year}",
        f"{d.day:02d}_{d.month:02d}_{d.year}",
        f"{d.day:02d}-{d.month:02d}-{d.year}",
        f"{d.day}.{d.month}.{d.year}",
    ]
    return any(s in stem for s in ddmm)


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
        "page_count": None,
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

    # Step 2: Vision is the primary extraction path for every document.
    # Text is kept for classification (filename+body cascade) and for the
    # retry-on-null guard below, but extraction itself always uses vision.
    vision_extraction = None
    text_len = len(text.strip())
    use_vision = _USE_VISION_FOR_ALL
    result["used_vision"] = use_vision

    # Step 2b: Kick off PDF page rendering in the background while we
    # classify on the main thread. Rendering only needs the PDF path, not
    # the category, so the two are independent work and can overlap. For
    # vision-enabled docs this recovers the ~200–600 ms that would
    # otherwise be paid serially between classification end and vision
    # call start.
    page_count = get_page_count(pdf_path)
    result["page_count"] = page_count or None
    _render_executor: ThreadPoolExecutor | None = None
    images_future = None
    if use_vision:
        _render_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="pdf-render")
        images_future = _render_executor.submit(_pdf_pages_to_base64, pdf_path)

    # Step 3: Classification (runs in parallel with page rendering)
    t0 = time.time()
    try:
        has_tables = False  # Table detection not in pipeline text extractor

        category, confidence, method = classify_document(filename, text, page_count, has_tables)
        result["classification"] = category
        result["confidence"] = confidence
        result["method"] = method
    except Exception as e:
        logger.error("Classification failed for %s: %s", filename, e,
                     extra={"extra_data": {"filename": filename, "error": str(e)}})
        result["error"] = f"Classification failed: {e}"
        # Tear down the render executor cleanly on the error path — don't
        # leak the thread or block on a render we'll never use.
        if _render_executor is not None:
            images_future.cancel() if images_future else None
            _render_executor.shutdown(wait=False)
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
            # Wait on the pre-started render; pass images directly to
            # extract_with_vision to avoid a duplicate render.
            try:
                pre_rendered = images_future.result() if images_future else None
            except Exception as render_err:
                logger.warning(
                    "Background page render failed; vision will re-render",
                    extra={"extra_data": {
                        "filename": filename, "error": str(render_err),
                    }},
                )
                pre_rendered = None
            vision_extraction = extract_with_vision(
                pdf_path,
                category,
                images_b64=pre_rendered,
                total_pages=page_count,
            )

        if vision_extraction is not None:
            # Run vision output through the same normalizer as text-based
            # extraction so category-specific rules (ISO material=None,
            # CUI merging, OCR/diacritics, truncation, nume_document) apply.
            extraction = normalize_extraction_result(vision_extraction, category, text)
            # Label the extraction with the model actually invoked, not a
             # frozen string. Prefer what vision_fallback reported; fall back
             # to the live settings value so UI/UX reflect the hot-reloaded
             # model instead of a stale "2.0-flash" from older builds.
            extraction["extraction_model"] = "vision:" + (
                vision_extraction.get("extraction_model")
                or settings.ai_model.replace("google/", "")
            )
        else:
            extraction = extract_document_data(text, category, filename=filename)
    except Exception as e:
        logger.error("Extraction failed for %s: %s", filename, e,
                     extra={"extra_data": {"filename": filename, "error": str(e)}})
        result["error"] = f"Extraction failed: {e}"
        return result
    finally:
        # Release the render executor now that vision is done. wait=False
        # is safe because `.result()` above already joined the future.
        if _render_executor is not None:
            _render_executor.shutdown(wait=False)
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

    # Step 5: Normalize company names and addresses.
    # Hallucination checks compare extracted values against OCR text. On
    # scanned PDFs OCR produces garbled text where real words/addresses
    # never appear verbatim, so vision extractions (which read the image)
    # would be incorrectly flagged. Skip the checks whenever vision is
    # the extraction source.
    skip_hallucination_checks = result.get("used_vision", False)
    t0 = time.time()
    try:
        for field in ("companie", "producator", "distribuitor"):
            raw = extraction.get(field)
            if raw and raw.strip():
                # Hallucination check: verify company name appears in document text
                if not skip_hallucination_checks:
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

                # Reject certification/approval bodies extracted as "companie"
                # on documents where the COMPANY being certified is what we want.
                # Scope covers ISO certificates and Romanian technical approvals
                # (AVIZ_TEHNIC, AVIZ_TEHNIC_SI_AGREMENT, AGREMENT) where MDRAP /
                # INCERC / AXA CERT etc. issue the document but the companie
                # field should hold the manufacturer/applicant.
                cert_bodies = [
                    # International ISO cert bodies
                    "international management", "management certification",
                    "bureau veritas", "tuv rheinland", "tuv sud", "lloyd",
                    "sgs ", "dekra", "dnv", "eurocert", "iqnet",
                    # Romanian ISO cert bodies
                    "srac", "certind", "aeroq", "qualitas",
                    "axa cert", "axa certification",
                    # Romanian aviz/agrement issuing bodies
                    "ministerul dezvolt",         # Ministerul Dezvoltării
                    "mdrap",                      # Ministerul Dezvoltării (abrev.)
                    "consiliul tehnic",           # Consiliul Tehnic Permanent
                    "incerc",                     # Institutul de Cercetări
                    "inspectoratul de stat",      # Inspectoratul de Stat în Construcții
                    "organism de certificare",
                    "grupa specializat",          # Grupa Specializată (agremente)
                ]
                if (
                    field == "companie"
                    and category in CATEGORIES_WITH_CERT_BODY_FILTER
                ):
                    if any(cb in val_lower for cb in cert_bodies):
                        logger.warning(
                            "Certification body extracted as companie on %s doc: '%s' — setting to None",
                            category, val[:60],
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

        # Companie fallback: when the cert-body filter nulls `companie` on
        # ISO/AVT/AGREMENT but the document still has a `producator`, promote
        # it — on those categories the company being certified and the
        # producer are the same entity, so we should surface it somewhere.
        if (
            category in CATEGORIES_WITH_CERT_BODY_FILTER
            and not extraction.get("companie")
            and extraction.get("producator")
        ):
            logger.info(
                "Promoting producator→companie on %s (companie was empty)",
                category,
                extra={"extra_data": {
                    "field_move": "producator->companie",
                    "category": category,
                    "value": extraction["producator"][:60],
                }},
            )
            extraction["companie"] = extraction["producator"]

        for field in ("adresa_producator", "adresa_distribuitor"):
            raw = extraction.get(field)
            if raw and raw.strip():
                # Hallucination check: verify address actually appears in document text
                if not skip_hallucination_checks:
                    raw_lower = raw.strip().lower()
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
        if date_val and text and not skip_hallucination_checks:
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

        # G4: filename-date fallback for data_expirare.
        # Only fires when:
        #   - the category legitimately carries an expiration (allowlist)
        #   - AI produced no date or the hallucination check wiped it
        #   - the filename contains a clean DD.MM.YYYY (or DD_MM_YYYY /
        #     DD-MM-YYYY) pattern with year >= current-1
        # Typical target: VLR 004.10_..._24_07_2028.pdf where Romanian naming
        # convention appends the expiration date as the last token.
        if (
            category in _FILENAME_EXPIRY_CATEGORIES
            and not extraction.get("data_expirare")
        ):
            candidates = _filename_expiry_candidates(filename)
            if candidates:
                # Prefer the latest plausible date — expirations are by
                # definition in the future / most recent one wins.
                chosen = max(candidates)
                chosen_str = chosen.strftime("%d.%m.%Y")
                logger.info(
                    "Filename-date fallback: no AI expiry, using filename date %s",
                    chosen_str,
                    extra={"extra_data": {
                        "step": "filename_date_fallback",
                        "filename": filename,
                        "chosen_date": chosen_str,
                        "candidates": [c.isoformat() for c in candidates],
                    }},
                )
                extraction["data_expirare"] = chosen_str

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
    review_reasons: list[dict] = []
    try:
        extraction, review_status, review_reasons = validate_extraction(extraction, category)
    except Exception as e:
        logger.warning("Validation error for %s: %s", filename, e,
                       extra={"extra_data": {"filename": filename, "error": str(e)}})
        review_status = "REVIEW"
        review_reasons = [{"reason": "validator_exception", "field": "", "message": str(e)}]
    finally:
        duration_ms = (time.time() - t0) * 1000
        logger.info("Validation complete", extra={"extra_data": {
            "step": "validation", "filename": filename,
            "duration_ms": round(duration_ms, 1),
            "review_status": review_status,
            "review_reasons": review_reasons,
            "reason_keys": sorted({r["reason"] for r in review_reasons}),
        }})

    # G5: suspicious-expiry review flag. A data_expirare that sits more
    # than ~6 months in the past is strongly suspicious — probably an issue
    # date the AI mislabelled. Only flag when the filename doesn't contain
    # that same date (which would be positive corroboration that the expiry
    # really is in the past). Keeps the value but nudges a human to double-
    # check in the UI.
    if review_status == "OK":
        d = _parse_ddmmyyyy(extraction.get("data_expirare"))
        if d:
            age_days = (date.today() - d).days
            if age_days > _SUSPICIOUS_PAST_EXPIRY_DAYS and not _filename_contains_date(filename, d):
                logger.warning(
                    "Suspicious expiry: %s is %d days in the past and not in filename — flagging REVIEW",
                    d.isoformat(), age_days,
                    extra={"extra_data": {
                        "step": "suspicious_expiry_guard",
                        "filename": filename,
                        "data_expirare": extraction.get("data_expirare"),
                        "age_days": age_days,
                    }},
                )
                review_status = "REVIEW"
                review_reasons.append({
                    "reason": "suspicious_expiry",
                    "field": "data_expirare",
                    "message": (
                        f"data_expirare '{extraction.get('data_expirare')}' is "
                        f"{age_days} days in the past and filename does not "
                        f"corroborate it — likely an issue date, not expiry"
                    ),
                })

    result["extraction"] = extraction
    result["review_status"] = review_status
    result["review_reasons"] = review_reasons
    result["error"] = None

    # Pipeline-complete summary — includes review reasons + populated field
    # names so a single log line tells you everything about the run without
    # grepping back through per-step entries.
    total_duration_ms = round((time.time() - pipeline_start) * 1000, 1)
    result["total_duration_ms"] = total_duration_ms
    field_count = len(extraction) if isinstance(extraction, dict) else 0
    populated_fields = (
        [k for k, v in extraction.items() if v is not None]
        if isinstance(extraction, dict) else []
    )
    logger.info("Pipeline complete", extra={"extra_data": {
        "step": "pipeline_complete", "filename": filename,
        "total_duration_ms": total_duration_ms,
        "review_status": result["review_status"],
        "review_reasons": review_reasons,
        "reason_keys": sorted({r["reason"] for r in review_reasons}),
        "used_vision": result["used_vision"],
        "has_error": result["error"] is not None,
        "field_count": field_count,
        "non_null_fields": len(populated_fields),
        "populated_fields": populated_fields,
        "category": result["classification"],
        "confidence": result.get("confidence"),
        "method": result["method"],
        "extraction_model": extraction.get("extraction_model") if isinstance(extraction, dict) else None,
    }})

    return result
