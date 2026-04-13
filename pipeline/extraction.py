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

import requests

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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# EXTRACTION_SCHEMA — 14 categories, defines expected fields per category
# ---------------------------------------------------------------------------

EXTRACTION_SCHEMA = {
    "ISO": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "CE": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "FISA_TEHNICA": {
        "fields": ["companie", "material", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "AGREMENT": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "AVIZ_TEHNIC": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "AVIZ_SANITAR": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "DECLARATIE_CONFORMITATE": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "CERTIFICAT_CALITATE": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "AUTORIZATIE_DISTRIBUTIE": {
        "fields": ["companie", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie"],
    },
    "CUI": {
        "fields": ["companie", "adresa_producator"],
        "required": ["companie"],
    },
    "CERTIFICAT_GARANTIE": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "DECLARATIE_PERFORMANTA": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "AVIZ_TEHNIC_SI_AGREMENT": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": ["companie", "material"],
    },
    "ALTELE": {
        "fields": ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"],
        "required": [],
    },
}

# ---------------------------------------------------------------------------
# Extraction system prompt (tuned across 5 iterations — DO NOT MODIFY)
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM_PROMPT = """Esti un expert in extragerea datelor din documente din domeniul constructiilor si materialelor de constructii din Romania.

Analizeaza urmatorul text extras dintr-un document PDF clasificat ca "{category}" si extrage urmatoarele informatii:

1. **companie** — Numele companiei principale mentionate in document (producator sau emitent).
   - Extrage DOAR numele companiei, fara CUI, adresa, sau alte detalii.
   - Daca sunt mai multe companii, alege compania PRINCIPALA (emitentul/producatorul).
   - NU include liste separate prin virgula cu mai multe companii.
   - Maxim {max_company} caractere.

2. **material** — Descrierea materialului/produsului.
   - Extrage o descriere CONCISA a materialului sau produsului principal.
   - Include tipul produsului, dimensiunile relevante, standardele (daca sunt mentionate scurt).
   - NU include descrieri generice precum "Produse", "Materiale", "Diverse".
   - NU repeta informatii deja prezente in alte campuri.
   - Maxim {max_material} caractere.

3. **data_expirare** — Data de expirare a documentului.
   - Format: DD.MM.YYYY (ex: 31.12.2025).
   - Daca documentul mentioneaza o durata de valabilitate (ex: "valabil 5 ani de la 01.01.2020"),
     calculeaza data de expirare: 01.01.2020 + 5 ani = 01.01.2025.
   - Daca nu exista data de expirare clara, returneaza null.
   - NU inventa date — daca nu este clar, returneaza null.

4. **producator** — Numele producatorului (daca este diferit de companie).
   - Daca producatorul este acelasi cu compania, returneaza null.
   - Maxim {max_company} caractere.

5. **distribuitor** — Numele distribuitorului (daca este mentionat).
   - Returneaza null daca nu este mentionat un distribuitor.
   - Maxim {max_company} caractere.

6. **adresa_producator** — Adresa producatorului sau a companiei.
   - Extrage adresa completa daca este disponibila.
   - Include strada, numar, oras, judet, cod postal daca sunt mentionate.
   - Maxim {max_address} caractere.

REGULI IMPORTANTE:
- Raspunde DOAR cu un JSON valid, fara explicatii sau text suplimentar.
- Foloseste null pentru campurile care nu pot fi determinate din text.
- NU inventa informatii care nu sunt in text.
- NU include caractere chinezesti in raspuns — daca textul original contine caractere chinezesti
  amestecate cu text latin, extrage DOAR textul latin.
- Daca textul este prea scurt sau ilizibil, returneaza un JSON cu toate campurile null.
- Corecteaza GRESELI EVIDENTE de OCR (ex: "lndustrie" → "Industrie", "TERAPIA" → "TERAPLAST"
  daca contextul indica clar compania TERAPLAST).

Format raspuns:
{{
    "companie": "Numele Companiei" sau null,
    "material": "Descrierea materialului" sau null,
    "data_expirare": "DD.MM.YYYY" sau null,
    "producator": "Numele Producatorului" sau null,
    "distribuitor": "Numele Distribuitorului" sau null,
    "adresa_producator": "Adresa completa" sau null
}}

Textul documentului ({category}):
{text}"""

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
        return {
            "companie": None,
            "material": None,
            "data_expirare": None,
            "producator": None,
            "distribuitor": None,
            "adresa_producator": None,
        }

    normalized = {}

    # Process each expected field
    schema = EXTRACTION_SCHEMA.get(category, EXTRACTION_SCHEMA["ALTELE"])
    all_fields = ["companie", "material", "data_expirare", "producator", "distribuitor", "adresa_producator"]

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
            # Validate date format DD.MM.YYYY
            date_match = re.match(r"^(\d{1,2})[./](\d{1,2})[./](\d{4})$", value)
            if date_match:
                # Normalize to DD.MM.YYYY format
                day = date_match.group(1).zfill(2)
                month = date_match.group(2).zfill(2)
                year = date_match.group(3)
                value = f"{day}.{month}.{year}"
            else:
                # Try to calculate from duration patterns in original text
                calculated = _calculate_expiry_date(text) if text else None
                if calculated:
                    value = calculated
                else:
                    # Keep non-standard date strings (e.g., "nelimitat", "permanent")
                    # but truncate to reasonable length
                    if len(value) > 50:
                        value = value[:50]

        elif field == "adresa_producator":
            # Truncate address
            if len(value) > MAX_ADDRESS_LENGTH:
                value = value[:MAX_ADDRESS_LENGTH].rsplit(" ", 1)[0]

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

    return normalized


def extract_data_with_ai(text: str, category: str, filename: str = "") -> dict | None:
    """Extract structured data from document text using AI.

    Sends text to OpenRouter API with category-specific extraction prompt.
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

    prompt = _EXTRACTION_SYSTEM_PROMPT.format(
        category=category,
        text=truncated_text,
        max_company=MAX_COMPANY_LENGTH,
        max_material=MAX_MATERIAL_LENGTH,
        max_address=MAX_ADDRESS_LENGTH,
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": AI_TEMPERATURE,  # 0.0 — NON-NEGOTIABLE
        "max_tokens": AI_MAX_TOKENS,
    }

    response_body = None
    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=120
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
                "timeout_seconds": 120,
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

    normalized = normalize_extraction_result(raw_result, category, text)

    # Merge regex results into normalized: fill None fields with regex values
    regex_result = regex_extract(text, category)
    for field, regex_value in regex_result.items():
        if normalized.get(field) is None and regex_value is not None:
            logger.info("Filling field %s from regex for category %s", field, category)
            normalized[field] = regex_value

    # Set extraction_model AFTER normalization so it doesn't get wiped
    normalized["extraction_model"] = extraction_model

    return normalized
