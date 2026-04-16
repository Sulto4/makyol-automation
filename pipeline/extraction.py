"""AI-powered data extraction from classified documents.

Moved verbatim from clasificare_documente_final.py.
Includes: EXTRACTION_SCHEMA (14 categories), extraction system prompt,
normalize_extraction_result() with OCR error fixes, diacritics normalization,
company name cleanup, date calculation, and truncation rules.
"""

import re
import json
import logging
from datetime import datetime, timedelta

import requests  # noqa: F401  -- used below in extract_data_with_ai

from pipeline.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    AI_MODEL,
    AI_TEMPERATURE,
    AI_MAX_TOKENS,
    MAX_COMPANY_LENGTH,
    MAX_MATERIAL_LENGTH,
    MAX_ADDRESS_LENGTH,
)
from pipeline.date_normalizer import normalize_data_expirare

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# EXTRACTION_SCHEMA — 14 categories, defines expected fields per category
# ---------------------------------------------------------------------------

EXTRACTION_SCHEMA = {
    "AUTORIZATIE_DISTRIBUTIE": {
        "fields": ["distribuitor", "producator", "data_emitere", "valabilitate", "data_expirare", "material", "adresa_producator"],
        "instructions": "Extract: distributor company, producer company, issue date, validity period, expiration date, material/product, producer address. The material is the product authorized for distribution (e.g., 'tevi si fitinguri PEID', 'vane industriale'). If the authorization is generic ('produsele achizitionate'), write 'Produse diverse (autorizatie generala)'. If no explicit expiration date but has validity period, CALCULATE it. If validity = 'pe durata contractului', write 'Pe durata contractului'.",
    },
    "AGREMENT": {
        "fields": ["producator", "data_expirare", "material", "companie", "adresa_producator"],
        "instructions": "Extract: producer name, expiration date of the AGREMENT TEHNIC (NOT the aviz tehnic), material/product name, company that holds the agrement, producer address. IMPORTANT: These documents contain BOTH an agrement date and an aviz tehnic date. Extract the AGREMENT expiration — look for 'Valabilitate agrement tehnic:' or 'agrementul tehnic este valabil până la data de'. The agrement date is usually LATER (more years) than the aviz tehnic date.",
    },
    "AVIZ_TEHNIC_SI_AGREMENT": {
        "fields": ["producator", "data_expirare", "material", "companie", "adresa_producator"],
        "instructions": "Extract: producer name, expiration date, material/product, company name, producer address. This is a combined Aviz Tehnic + Agrement document. For data_expirare, extract the LATER date (the agrement date, not the aviz tehnic date). Look for 'Valabilitate agrement tehnic:' — that is the primary expiration.",
    },
    "AVIZ_TEHNIC": {
        "fields": ["producator", "data_expirare", "material", "companie", "adresa_producator"],
        "instructions": "Extract: producer name, expiration date of the AVIZ TEHNIC (NOT the agrement), material/product, company (the certification body or the producer). IMPORTANT: These documents may also mention an agrement date. Extract ONLY the aviz tehnic expiration — look for 'AVIZ TEHNIC este valabil până la' or 'Valabilitate aviz tehnic:'.",
    },
    "AVIZ_SANITAR": {
        "fields": ["companie", "material", "data_expirare", "producator", "adresa_producator"],
        "instructions": "Extract: company holding the sanitary approval, material/product, expiration date, producer, producer address. Look very carefully for expiration - check for 'valabil', 'expira', 'pana la', and also check if the approval number contains a year-based validity. If no expiration is stated anywhere, use null.",
    },
    "ISO": {
        "fields": ["companie", "data_expirare", "standard_iso", "adresa_producator"],
        "instructions": "Extract: certified company name, certificate expiration date, ISO standard number (e.g., 'ISO 9001:2015'), company address. NOTE: Do NOT put the ISO standard in the 'material' field - ISO certifies management systems, not physical materials. For 'nume_document', write 'Certificat ISO [standard]' (e.g., 'Certificat ISO 9001').",
    },
    "DECLARATIE_PERFORMANTA": {
        "fields": ["material", "producator", "adresa_producator"],
        "instructions": "Extract: product/material name (full description with specs), producer name, producer address. Keep material name concise but specific (max 100 chars).",
    },
    "FISA_TEHNICA": {
        "fields": ["producator", "material", "adresa_producator"],
        "instructions": "Extract: producer name, product/material name (full name with type, e.g., 'Tevi PE100 PEHD pentru apa'), producer address.",
    },
    "CERTIFICAT_GARANTIE": {
        "fields": ["material", "producator", "adresa_producator", "data_expirare"],
        "instructions": "Extract: product/material under warranty (keep CONCISE, max 80 chars - summarize if the list is long, e.g., 'Tevi si fitinguri PVC, PP, PE, PEX'), producer name, producer address, warranty period/expiration. For data_expirare: extract the warranty DURATION (e.g., '2 ani de la receptie', '24 luni'). If multiple warranty periods exist, extract the main/longest one.",
    },
    "DECLARATIE_CONFORMITATE": {
        "fields": ["material", "producator", "companie", "adresa_producator"],
        "instructions": "Extract: product/material name (the actual product - if generic like 'produse pentru constructii', keep it as is but add any specifics from the document context), producer name, declaring company, producer address.",
    },
    "CE": {
        "fields": ["producator", "companie", "material", "data_expirare", "adresa_producator"],
        "instructions": "Extract data from this CE/PED certificate. IMPORTANT distinction: 'producator' = the manufacturer of the product (e.g., Hebei Huayang Steel Pipe). 'companie' = the CERTIFICATION BODY that issued the certificate (e.g., TÜV Rheinland, TÜV SUD, Bureau Veritas, Lloyd's). These are DIFFERENT entities. Also extract material/product, expiration date, producer address. For 'nume_document', write 'Certificat CE PED' or 'Certificat CE'.",
    },
    "CERTIFICAT_CALITATE": {
        "fields": ["material", "producator", "companie"],
        "instructions": "Extract: product/material name - the PHYSICAL PRODUCT being certified. Look for pipe type (PEHD, PVC, PE100), dimensions (DN, PN, SDR), and product description. Common materials: 'Teava PEHD PE100', 'Teava PVC multistrat', 'Fitinguri PEID'. If the product field is empty (template document) but a standard reference exists, DEDUCE the material from the standard: EN 12201 = 'Teava PE pentru apa (conform EN 12201)', EN 13476 = 'Teava PVC multistrat (conform EN 13476)', EN 1452 = 'Teava PVC-U presiune (conform EN 1452)', EN 10204 = 'Tevi/produse din otel (conform EN 10204)'. Also extract producer and company.",
    },
    "CUI": {
        "fields": ["companie", "cui_number", "adresa_producator"],
        "instructions": "Extract: company name (EXACTLY as registered - common companies: TERAPLAST, VALROM INDUSTRIE, TEHNO WORLD, ZAKPREST CONSTRUCT), CUI number (just digits), registered address. For 'nume_document', use 'Certificat de Inregistrare'.",
    },
    "ALTELE": {
        "fields": ["companie", "material"],
        "instructions": "Extract: any company name and material/product mentioned.",
    },
}

# ---------------------------------------------------------------------------
# Extraction system prompt — ported from MVP (clasificare_documente_final.py)
# 13 rules: MVP rules 1-8, rules 9-13
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = """You are a precise data extraction system for Romanian construction industry documents.
Extract ONLY the requested fields from the document text. Follow these rules strictly:

1. Return ONLY valid JSON with the exact field names requested
2. If a field is not found in the document, use null (not empty string)
3. For dates, use format DD.MM.YYYY when possible
4. For "data_expirare" (EXPIRATION DATE, not issue date): CRITICAL — do not confuse issue date with expiration date.
   - Look EXPLICITLY for: "valabil pana la", "valid until", "data expirarii", "valabilitate",
     "expires on", "expiry date", "termen de valabilitate", "expira la".
   - Issue date markers ("Data", "Emis la", "Date of issue", "Data intocmirii",
     "Data emiterii") are NOT expiration dates — do NOT return them as data_expirare.
   - If ONLY issue date + validity period exist (e.g., "issued 01.01.2024, valid 3 years"),
     CALCULATE the expiration: 01.01.2027.
   - If the document does NOT explicitly mention an expiration date, validity period,
     or duration, return null. Do NOT pick up random dates (document code dates,
     revision dates, test dates, letter dates) and label them as expiry.
   - Do NOT invent dates. Null is better than a wrong date.
5. For "material": extract the ACTUAL PRODUCT/MATERIAL name, NOT standard references.
   - CORRECT: "Tevi PEHD PE100 RC SDR11 DN110-DN630", "Fitinguri PVC-U PN10/PN16"
   - WRONG: "Executat dupa EN 12201-2" (this is a standard reference, not a material)
   - If the document is about a specific product, extract its commercial name and specifications
   - Include dimensions, standards references AFTER the product name if present
6. For "producator": the manufacturer/producer of the product.
   - Fix obvious OCR errors in company names (e.g., "TERAPIA" should be "TERAPLAST" if context shows Teraplast)
   - For well-known Romanian companies, use the correct name: TERAPLAST, VALROM, TEHNO WORLD
7. For "distribuitor": the company authorized to distribute the product
8. For "companie": if the company is neither clearly a producer nor distributor, use this field. For ISO certs, this is the certified company.
   - Same OCR correction rules as producator
9. For "adresa_producator": full address of the producer/manufacturer. Fix obvious OCR errors in addresses.
10. For "cui_number": just the numeric CUI code
11. For "standard_iso": the ISO standard number (e.g., "ISO 9001:2015", "ISO 14001:2015")
12. Fix obvious OCR errors in ALL extracted values:
    - "lndustrie" → "Industrie", "ser,;ce" → "Service", "TUV" → "TÜV"
    - "Să'ațel" → "Sărățel", "TERAPIA" → "TERAPLAST" (when context shows Teraplast)
    - Interpret Romanian diacritics: "Ţ" = "Ț", "ş" = "ș", "ã" = "ă"
13. For "nume_document": extract ONLY the document type/title, MAX 40 characters.
    - CORRECT examples: "Agrement Tehnic", "Aviz Sanitar", "Certificat CE PED", "Certificat ISO 9001", "Certificat de Inregistrare", "Fisa Tehnica Produs", "Declaratie de Performanta"
    - Do NOT include document numbers, dates, reference codes, or descriptions
    - Do NOT include newlines
    - For CE/PED certificates: use "Certificat CE PED"
    - For ISO certificates: use "Certificat ISO [standard]" (e.g., "Certificat ISO 9001")
    - WRONG: "Certificat Sistem de management al calității pentru Producător" (too long, includes description)

Respond with ONLY the JSON object, no markdown, no explanation."""

# ---------------------------------------------------------------------------
# OCR error corrections
# ---------------------------------------------------------------------------

_OCR_FIXES = [
    ("TERAPIA", "TERAPLAST"),
    ("lndustrie", "Industrie"),
    ("lndustrial", "Industrial"),
    ("lnternational", "International"),
    ("lnstalatii", "Instalatii"),
    ("lzolatii", "Izolatii"),
    ("lmperm", "Imperm"),
    ("ser,;ce", "Service"),
    ("ser;ce", "Service"),
    ("lron", "Iron"),
    ("PEÎD", "PEID"),
    ("PEÎ D", "PEID"),
]

# ---------------------------------------------------------------------------
# Diacritics normalization (common OCR/encoding issues)
# ---------------------------------------------------------------------------

_DIACRITICS_MAP = {
    "Ţ": "Ț",
    "ţ": "ț",
    "Ş": "Ș",
    "ş": "ș",
    "ã": "ă",  # Portuguese a-tilde → Romanian a-breve (common OCR confusion)
}

# ---------------------------------------------------------------------------
# Null-like values to treat as None
# ---------------------------------------------------------------------------

_NULL_VALUES = {
    "", "null", "none", "n/a", "n.a.", "n/a.", "-", "--", "---",
    "nu se aplica", "nu este cazul", "nu este disponibil",
    "nedeterminat", "necunoscut", "neprecizat",
}

# ---------------------------------------------------------------------------
# Categories where data_expirare is meaningful.
#
# Certificate types that are either time-limited authorizations or warranties:
# these genuinely expire and the field should be kept when extracted.
#
# Everything else (FISA_TEHNICA, CUI, DECLARATIE_PERFORMANTA, CERTIFICAT_
# CALITATE, ALTELE) is a point-in-time document, a permanent registration,
# or a product spec. The AI tends to hallucinate expirations on these by
# picking up issue/revision dates from the page, which then makes documents
# appear "expired" in the UI. We drop data_expirare for those categories.
#
# DECLARATIE_CONFORMITATE is kept because some DC documents do state an
# explicit validity period ("valabil până la DD.MM.YYYY") or contract
# duration — those are legitimate. Over-extraction on DC is caught by the
# prompt rule (G2) rather than a hard blacklist.
# ---------------------------------------------------------------------------

CATEGORIES_WITH_DATA_EXPIRARE = frozenset({
    "ISO",
    "CE",
    "AGREMENT",
    "AVIZ_TEHNIC",
    "AVIZ_TEHNIC_SI_AGREMENT",
    "AVIZ_SANITAR",
    "AUTORIZATIE_DISTRIBUTIE",
    "CERTIFICAT_GARANTIE",
    "DECLARATIE_CONFORMITATE",
})


def smart_truncate(text: str, max_chars: int = 6000) -> str:
    """Truncate long text while preserving header, middle, and footer sections."""
    if len(text) <= max_chars:
        return text
    header = text[:2500]
    mid_start = len(text) // 2 - 1000
    middle = text[mid_start:mid_start + 2000]
    footer = text[-1500:]
    return header + "\n\n[...]\n\n" + middle + "\n\n[...]\n\n" + footer


def _fix_ocr_errors(text: str) -> str:
    """Fix common OCR errors in extracted text."""
    for wrong, correct in _OCR_FIXES:
        text = text.replace(wrong, correct)
    return text


def _fix_diacritics(text: str) -> str:
    """Normalize diacritics to standard Romanian forms."""
    for wrong, correct in _DIACRITICS_MAP.items():
        text = text.replace(wrong, correct)
    return text


def _is_null_value(value) -> bool:
    """Check if a value should be treated as None."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in _NULL_VALUES:
        return True
    return False


def _clean_company_name(name: str) -> str:
    """Basic company name cleanup (before fuzzy normalization).

    Removes CUI patterns, trims whitespace, fixes diacritics/OCR.
    The advanced fuzzy normalization happens in normalization.py.
    """
    if not name:
        return name

    # Remove CUI patterns like (CUI: 12345678)
    name = re.sub(r"\(?\s*CUI\s*:?\s*\d+\s*\)?", "", name).strip()

    # Remove leading/trailing quotes
    name = name.strip("\"'")

    # Fix OCR errors and diacritics
    name = _fix_ocr_errors(name)
    name = _fix_diacritics(name)

    # Collapse multiple spaces
    name = re.sub(r"\s+", " ", name).strip()

    # Truncate to max length
    if len(name) > MAX_COMPANY_LENGTH:
        name = name[:MAX_COMPANY_LENGTH].rsplit(" ", 1)[0]

    return name


def _find_issue_date(text: str) -> datetime | None:
    """Search the document text for a plausible issue date.

    Romanian certificates use a fairly stable set of issue-date markers:
    "data emiterii", "data intocmirii", "emis la", "date of issue",
    "valabil incepand cu". Look for a DD.MM.YYYY (or variant) near any of
    these and return the first hit. Falls back to the earliest DD.MM.YYYY
    in the first ~2000 characters — issue dates are always in the header
    area on these docs.
    """
    if not text:
        return None

    markers = [
        r"data\s+emiterii?", r"data\s+[îi]ntocmirii?", r"emis(?:\s+la)?",
        r"data\s+document(?:ului)?", r"date\s+of\s+issue",
        r"data\s+eliber[aă]rii?", r"eliberat(?:\s+la)?",
        r"valabil\s+[iî]ncep[âa]nd\s+(?:cu|de\s+la)",
    ]
    window = 80  # chars on each side of the marker
    text_lc = text.lower()
    date_re = re.compile(r"\b(\d{1,2})[./\-](\d{1,2})[./\-](\d{2,4})\b")

    for marker_pat in markers:
        for m in re.finditer(marker_pat, text_lc):
            start = max(0, m.start() - window)
            end = min(len(text), m.end() + window)
            segment = text[start:end]
            dm = date_re.search(segment)
            if dm:
                d, mo, y = (int(g) for g in dm.groups())
                if y < 100:
                    y += 2000 if y < 70 else 1900
                try:
                    return datetime(y, mo, d)
                except ValueError:
                    continue

    # Fallback: earliest date in the first 2000 chars of the document.
    for dm in date_re.finditer(text[:2000]):
        d, mo, y = (int(g) for g in dm.groups())
        if y < 100:
            y += 2000 if y < 70 else 1900
        try:
            return datetime(y, mo, d)
        except ValueError:
            continue
    return None


def _expiry_from_duration(duration: str, text: str) -> str | None:
    """Given a duration phrase ("5 ani", "Valabil 3 ani") plus the document
    text, try to locate the issue date and compute issue + duration.

    Returns a DD.MM.YYYY string on success, None if we couldn't find an
    issue date or parse the duration. Keeping this separate from the
    existing _calculate_expiry_date (which requires the explicit
    "N ani de la DD.MM.YYYY" pattern in a single sentence) because many
    real documents split issue date and validity period across different
    fields/headers — the AI extracts the duration as data_expirare and we
    need to meet it in the middle.
    """
    if not duration or not text:
        return None

    m = re.search(r"(\d+)\s*(ani?|luni?|zile|zi|years?|months?|days?)", duration, re.IGNORECASE)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2).lower()

    issue = _find_issue_date(text)
    if issue is None:
        return None

    try:
        if unit.startswith("an") or unit.startswith("year"):
            expiry = issue.replace(year=issue.year + n)
        elif unit.startswith("lun") or unit.startswith("month"):
            # naive month add — jump months, clamping day to month length
            month = issue.month + n
            year = issue.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(issue.day, 28)
            expiry = issue.replace(year=year, month=month, day=day)
        elif unit.startswith("zi") or unit.startswith("day"):
            expiry = issue + timedelta(days=n)
        else:
            return None
    except (ValueError, OverflowError):
        return None
    return expiry.strftime("%d.%m.%Y")


def _calculate_expiry_date(text: str) -> str | None:
    """Attempt to calculate expiry date from duration patterns in text.

    Handles patterns like:
    - "valabil 5 ani de la 01.01.2020"
    - "valabilitate: 3 ani incepand cu 15.03.2021"
    """
    # Pattern: N ani de la DD.MM.YYYY
    duration_pattern = re.compile(
        r"(?:valabil(?:itate)?|valid)\s*(?::\s*)?(\d+)\s*ani\s*"
        r"(?:de\s+la|incepand\s+(?:cu|de\s+la)|din)\s*"
        r"(\d{1,2})[./](\d{1,2})[./](\d{4})",
        re.IGNORECASE,
    )
    match = duration_pattern.search(text)
    if match:
        years = int(match.group(1))
        day = int(match.group(2))
        month = int(match.group(3))
        year = int(match.group(4))
        try:
            start_date = datetime(year, month, day)
            expiry_date = start_date.replace(year=start_date.year + years)
            return expiry_date.strftime("%d.%m.%Y")
        except ValueError:
            pass

    return None


def normalize_extraction_result(result: dict, category: str, text: str = "") -> dict:
    """Normalize and clean extraction result.

    Applies:
    - Null-like value handling
    - OCR error fixes
    - Diacritics normalization
    - Company name cleanup
    - Date calculation from duration patterns
    - Field truncation (material=300, address=250, company=80)
    - Document title truncation (50 chars) if present

    Args:
        result: Raw extraction result dict from AI.
        category: Document category for schema lookup.
        text: Original document text (for date calculation fallback).

    Returns:
        Cleaned and normalized extraction dict.
    """
    if not result or not isinstance(result, dict):
        logger.info("Normalization skipped: empty/invalid result", extra={"extra_data": {
            "category": category,
            "result_type": type(result).__name__,
        }})
        return {
            "companie": None,
            "material": None,
            "data_expirare": None,
            "producator": None,
            "distribuitor": None,
            "adresa_producator": None,
            "nume_document": None,
        }

    # Snapshot before-fields for logging
    before_fields = [k for k, v in result.items() if v is not None]

    # Category-specific normalization flags (tracked for logging)
    iso_material_nulled = False
    cui_number_merged = False
    date_calculated = False
    data_expirare_dropped_for_category = False

    # --- Category-specific pre-processing (before per-field loop) ---

    # G1: drop data_expirare for categories where it isn't meaningful. Most
    # misextractions ("expired" docs in the UI) come from FT/CUI/MTC/DoP/
    # ALTELE where the AI picks up an issue or revision date and labels it
    # as expiry. These document types don't expire.
    if category not in CATEGORIES_WITH_DATA_EXPIRARE:
        if result.get("data_expirare"):
            data_expirare_dropped_for_category = True
            result["data_expirare"] = None

    # AUTORIZATIE_DISTRIBUTIE: calculate data_expirare from data_emitere + valabilitate
    if category == "AUTORIZATIE_DISTRIBUTIE":
        if not result.get("data_expirare") and result.get("data_emitere") and result.get("valabilitate"):
            valab = str(result["valabilitate"]).lower()
            if "contract" in valab or "nedeterminat" in valab:
                result["data_expirare"] = "Pe durata contractului"
            else:
                result["data_expirare"] = (
                    f"Emitere: {result['data_emitere']}, "
                    f"Valabilitate: {result['valabilitate']}"
                )

    # CUI: fallback adresa to adresa_producator (merge cui_number happens post-loop)
    if category == "CUI":
        if result.get("adresa") and not result.get("adresa_producator"):
            result["adresa_producator"] = str(result["adresa"]).strip()

    # ISO: null material, set nume_document with standard
    if category == "ISO":
        iso_material_nulled = result.get("material") is not None
        result["material"] = None  # ISO certifies management systems, not materials
        if result.get("standard_iso"):
            std = str(result["standard_iso"]).strip()
            current_name = str(result.get("nume_document") or "").lower()
            if "iso" not in current_name:
                result["nume_document"] = f"Certificat {std}"

    # --- Per-field normalization loop ---

    normalized = {}

    # Process each expected field
    schema = EXTRACTION_SCHEMA.get(category, EXTRACTION_SCHEMA["ALTELE"])
    all_fields = [
        "companie", "material", "data_expirare", "producator",
        "distribuitor", "adresa_producator",
        "nume_document",
    ]

    for field in all_fields:
        value = result.get(field)

        # Handle null-like values
        if _is_null_value(value):
            normalized[field] = None
            continue

        value = str(value).strip()

        # Apply OCR fixes and diacritics normalization to all text fields
        value = _fix_ocr_errors(value)
        value = _fix_diacritics(value)

        # Field-specific processing
        if field in ("companie", "producator", "distribuitor"):
            value = _clean_company_name(value)
            if not value:
                normalized[field] = None
                continue

        elif field == "material":
            # Remove generic-only descriptions
            generic_terms = {"produse", "materiale", "diverse", "altele", "produse diverse"}
            if value.strip().lower() in generic_terms:
                normalized[field] = None
                continue
            # Truncate material
            if len(value) > MAX_MATERIAL_LENGTH:
                value = value[:MAX_MATERIAL_LENGTH].rsplit(" ", 1)[0]

        elif field == "data_expirare":
            # Unified date normalization — handles Romanian month names,
            # any separator, ISO format, 2-digit years, trailing commentary,
            # and recognized duration phrases ("Valabil 5 ani" etc.).
            normalized_date, kind = normalize_data_expirare(value)
            if normalized_date is None:
                normalized[field] = None
                continue
            value = normalized_date
            if kind == "date":
                # Purely numeric DD.MM.YYYY at this point.
                pass
            elif kind == "duration":
                # Try to upgrade the duration into a concrete expiry by
                # looking up the issue date in the document text and
                # adding the duration on top. Keeps the duration string
                # only if that calculation fails (the validator still
                # accepts durations as-is).
                if text:
                    computed = _expiry_from_duration(value, text)
                    if computed:
                        logger.info(
                            "Computed data_expirare from duration + issue date",
                            extra={"extra_data": {
                                "step": "expiry_from_duration",
                                "category": category,
                                "original_duration": value,
                                "computed_expiry": computed,
                            }},
                        )
                        value = computed
                        date_calculated = True
                    elif len(value) > 50:
                        value = value[:50]
                elif len(value) > 50:
                    value = value[:50]
            else:
                # kind == "raw": couldn't parse. Fall back to the pre-
                # existing behaviour — try to compute expiry from a
                # "N ani de la DD.MM.YYYY" pattern in the document text,
                # otherwise keep value but truncate.
                calculated = _calculate_expiry_date(text) if text else None
                if calculated:
                    value = calculated
                    date_calculated = True
                elif len(value) > 50:
                    value = value[:50]

        elif field == "adresa_producator":
            # Truncate address
            if len(value) > MAX_ADDRESS_LENGTH:
                value = value[:MAX_ADDRESS_LENGTH].rsplit(" ", 1)[0]

        elif field == "nume_document":
            # Strip doc numbers/dates (e.g., "Agrement 012-04/123-2024")
            value = re.sub(r'\s+\d{3}[-/]\d{2}[-/]\d+[-/]?\d*$', '', value).strip()
            value = re.sub(r'\s+Nr\.?\s*\d+.*$', '', value).strip()
            # Truncate to max 50 chars at word boundary
            if len(value) > 50:
                cut = value[:50].rfind(' ')
                if cut > 20:
                    value = value[:cut].rstrip(' ,;')
                else:
                    value = value[:50]

        # Remove Chinese characters if Latin text present
        if value and any(ord(c) >= 0x4E00 and ord(c) <= 0x9FFF for c in value):
            import unicodedata
            has_latin = any(
                unicodedata.category(c).startswith("L") and ord(c) < 0x4E00
                for c in value
            )
            if has_latin:
                value = re.sub(r"[\u4e00-\u9fff\u3400-\u4dbf]+", "", value).strip()
                if not value:
                    normalized[field] = None
                    continue

        normalized[field] = value if value else None

    # --- Category-specific post-processing (after per-field cleanup) ---

    # CUI: merge cui_number into companie AFTER company name cleanup
    # (must be post-loop because _clean_company_name strips CUI patterns)
    if category == "CUI" and result.get("cui_number"):
        cui_number_merged = True
        if normalized.get("companie"):
            normalized["companie"] = (
                f"{normalized['companie']} (CUI: {result['cui_number']})"
            )
        else:
            normalized["companie"] = f"CUI: {result['cui_number']}"

    # Log before vs after normalization with category-specific flags
    after_fields = [k for k, v in normalized.items() if v is not None]
    logger.info("Normalization before vs after fields", extra={"extra_data": {
        "category": category,
        "before_fields": before_fields,
        "after_fields": after_fields,
        "before_count": len(before_fields),
        "after_count": len(after_fields),
        "iso_material_nulled": iso_material_nulled,
        "cui_number_merged": cui_number_merged,
        "date_calculated": date_calculated,
        "data_expirare_dropped_for_category": data_expirare_dropped_for_category,
    }})

    return normalized


def extract_data_with_ai(text: str, category: str, filename: str = "") -> dict | None:
    """Extract structured data from document text using AI.

    Uses two-message approach (system + user) matching MVP pattern.
    System prompt contains extraction rules; user prompt contains
    document-specific context (filename, category, fields, text).
    Temperature is 0.0 (NON-NEGOTIABLE).

    Args:
        text: Extracted text from the PDF.
        category: Document category from classification.
        filename: Optional source filename for error logging.

    Returns:
        Raw extraction result dict, or None on failure.
    """
    if not text or not text.strip():
        return None

    # Truncate text to avoid token limits (smart_truncate preserves header+middle+footer)
    text_length = len(text)
    truncated_text = smart_truncate(text)
    was_truncated = text_length > 6000

    logger.info(
        "AI extraction request starting",
        extra={"extra_data": {
            "category": category,
            "filename": filename,
            "text_length": text_length,
            "truncated_to": len(truncated_text) if was_truncated else None,
        }},
    )

    # Build dynamic user prompt from schema (MVP pattern)
    schema = EXTRACTION_SCHEMA.get(category, EXTRACTION_SCHEMA["ALTELE"])
    output_fields = list(set(schema["fields"] + ["nume_document"]))

    user_prompt = (
        f"Document filename: {filename}\n"
        f"Document category: {category}\n"
        f"Required fields: {json.dumps(output_fields)}\n"
        f"\n"
        f"Instructions: {schema['instructions']}\n"
        f"\n"
        f"Also extract:\n"
        f'- "nume_document": the official title of the document as it appears '
        f"in the header/title area\n"
        f"\n"
        f"Document text:\n"
        f"---\n"
        f"{truncated_text}\n"
        f"---\n"
        f"\n"
        f"Return a JSON object with the requested fields. "
        f"Use null for fields not found in the document."
    )

    # DEBUG logging for prompt diagnostics
    logger.debug(
        "Extraction system prompt length: %d chars", len(_EXTRACTION_SYSTEM_PROMPT),
    )
    logger.debug(
        "Extraction user prompt (first 2000 chars): %s", user_prompt[:2000],
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AI_MODEL,
        "messages": [
            {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": AI_TEMPERATURE,  # 0.0 — NON-NEGOTIABLE
        "max_tokens": AI_MAX_TOKENS,
    }

    response_body = None
    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=60
        )
        response.raise_for_status()

        response_body = response.text
        logger.info(
            "AI extraction response received",
            extra={"extra_data": {
                "category": category,
                "status_code": response.status_code,
                "response_length": len(response_body),
                "model": AI_MODEL,
            }},
        )

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # DEBUG logging for raw AI response before parsing
        logger.debug("Raw AI response content: %s", content)

        # Strip markdown code fences if present
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content.strip())

        parsed = json.loads(content)

        non_null_fields = [k for k, v in parsed.items() if v is not None]
        logger.info(
            "AI extraction parsed successfully",
            extra={"extra_data": {
                "category": category,
                "field_names": list(parsed.keys()),
                "non_null_count": len(non_null_fields),
                "non_null_fields": non_null_fields,
            }},
        )

        return parsed

    except requests.exceptions.Timeout:
        logger.error(
            "AI extraction timed out",
            extra={"extra_data": {
                "category": category,
                "filename": filename,
                "text_length": text_length,
                "timeout_seconds": 60,
            }},
        )
        return None
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        response_body = getattr(e.response, "text", None) if hasattr(e, "response") else None
        logger.error(
            "AI extraction request failed",
            extra={"extra_data": {
                "category": category,
                "filename": filename,
                "error": str(e),
                "status_code": status_code,
                "response_body": response_body[:500] if response_body else None,
            }},
        )
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(
            "AI extraction response parsing failed",
            extra={"extra_data": {
                "category": category,
                "filename": filename,
                "error": str(e),
                "error_type": type(e).__name__,
                "response_body": response_body[:500] if response_body else None,
            }},
        )
        return None


def extract_document_data(text: str, category: str, filename: str = "") -> dict:
    """Full extraction pipeline: AI extraction + regex merge + normalization.

    Args:
        text: Extracted text from the PDF.
        category: Document category from classification.
        filename: Optional source filename for error logging.

    Returns:
        Normalized extraction result dict with all expected fields,
        including extraction_model tracking.
    """
    from pipeline.regex_extraction import regex_extract

    raw_result = extract_data_with_ai(text, category, filename=filename)

    if raw_result is None:
        logger.warning("AI extraction returned None for category %s, using regex fallback", category)
        raw_result = regex_extract(text, category)
        extraction_model = "regex_fallback"
    else:
        extraction_model = AI_MODEL

    # Track AI-sourced fields (non-null from AI/regex_fallback result)
    ai_fields = [k for k, v in raw_result.items() if v is not None] if raw_result else []

    normalized = normalize_extraction_result(raw_result, category, text)

    # Merge regex results into normalized: fill None fields with regex values
    regex_filled = []
    regex_result = regex_extract(text, category)
    for field, regex_value in regex_result.items():
        if normalized.get(field) is None and regex_value is not None:
            logger.info("Filling field %s from regex for category %s", field, category)
            normalized[field] = regex_value
            regex_filled.append(field)

    # Set extraction_model AFTER normalization so it doesn't get wiped
    normalized["extraction_model"] = extraction_model

    # Log AI vs regex field sources
    final_non_null = [k for k, v in normalized.items() if v is not None]
    logger.info("AI vs regex field sources", extra={"extra_data": {
        "category": category,
        "filename": filename,
        "ai_fields": ai_fields,
        "regex_filled": regex_filled,
        "final_non_null": final_non_null,
        "extraction_model": extraction_model,
    }})

    return normalized
