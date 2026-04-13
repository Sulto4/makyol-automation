"""Document classification using 3-level cascade.

Level 1: Filename regex matching (71% of documents, confidence=0.95)
Level 2: Text content multi-marker scoring (13%, confidence=0.85)
Level 3: AI classification via OpenRouter (16%, confidence varies)

Moved verbatim from clasificare_documente_final.py.
FIX: classify_by_ai() temperature changed from 0.1 to 0.0.
"""

import re
import json
import logging

import requests

from pipeline.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    AI_MODEL,
    AI_TEMPERATURE,
    AI_MAX_TOKENS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Valid categories (14 total)
# ---------------------------------------------------------------------------

VALID_CATEGORIES = [
    "ISO",
    "CE",
    "FISA_TEHNICA",
    "AGREMENT",
    "AVIZ_TEHNIC",
    "AVIZ_SANITAR",
    "DECLARATIE_CONFORMITATE",
    "CERTIFICAT_CALITATE",
    "AUTORIZATIE_DISTRIBUTIE",
    "CUI",
    "CERTIFICAT_GARANTIE",
    "DECLARATIE_PERFORMANTA",
    "AVIZ_TEHNIC_SI_AGREMENT",
    "ALTELE",
]

# ---------------------------------------------------------------------------
# Level 1: Filename regex rules (37 patterns)
# Each entry: (compiled_regex_pattern, category_string)
# ---------------------------------------------------------------------------

FILENAME_RULES = [
    # ISO certificates (various standards)
    (r"(?i)ISO\s*9001", "ISO"),
    (r"(?i)ISO\s*14001", "ISO"),
    (r"(?i)ISO\s*45001", "ISO"),
    (r"(?i)ISO\s*50001", "ISO"),
    (r"(?i)ISO\s*22000", "ISO"),
    (r"(?i)ISO\s*13485", "ISO"),
    (r"(?i)ISO\s*27001", "ISO"),
    (r"(?i)\bISO\b.*(?:certificat|certificate)", "ISO"),
    # CE / PED certificates
    (r"(?i)\bCE\b.*(?:certificat|certificate|PED)", "CE"),
    (r"(?i)\bPED\b", "CE"),
    (r"(?i)certificat.*\bCE\b", "CE"),
    # Fisa tehnica / Technical data sheets
    (r"(?i)(?:\bFT\b.*\bPEHD\b|\bFT\b.*\bteav|fisa\s*tehnica|\bFT\b.*\bfiting|data\s*sheet)", "FISA_TEHNICA"),
    (r"(?i)fi[sș][aă]\s*tehnic[aă]", "FISA_TEHNICA"),
    (r"(?i)technical\s*data\s*sheet", "FISA_TEHNICA"),
    # Agrement tehnic
    (r"(?i)(?:\bAGT\b|agrement\s*tehnic|\bAT\b.*\d{3})", "AGREMENT"),
    (r"(?i)aviz.*agrement.*tehnic", "AVIZ_TEHNIC_SI_AGREMENT"),
    (r"(?i)agrement.*aviz", "AVIZ_TEHNIC_SI_AGREMENT"),
    # Aviz tehnic
    (r"(?i)(?:\bAVT\b|aviz\s*tehnic)", "AVIZ_TEHNIC"),
    # Aviz sanitar
    (r"(?i)(?:\bAVS\b|aviz\s*sanitar)", "AVIZ_SANITAR"),
    # Declaratie de conformitate
    (r"(?i)(?:\bDC\b(?!\s*-)|declarati[ea]\s*de\s*conformitate)", "DECLARATIE_CONFORMITATE"),
    (r"(?i)declara[tț]i[ea]\s*conformitate", "DECLARATIE_CONFORMITATE"),
    # Certificat de calitate / conformitate
    (r"(?i)(?:\bCC\b|certificat\s*de\s*calitate)", "CERTIFICAT_CALITATE"),
    (r"(?i)certificat\s*de\s*conformitate", "CERTIFICAT_CALITATE"),
    (r"(?i)certificat.*P1R", "CERTIFICAT_CALITATE"),
    (r"(?i)certificat.*CERT", "CERTIFICAT_CALITATE"),
    # Certificat de garantie
    (r"(?i)(?:\bCG\b|certificat\s*de\s*garantie|certificat\s*garan[tț]ie)", "CERTIFICAT_GARANTIE"),
    # Autorizatie distributie
    (r"(?i)autorizati[ea]\s*(?:de\s*)?distributi[ea]", "AUTORIZATIE_DISTRIBUTIE"),
    (r"(?i)\bAD\b.*autorizati", "AUTORIZATIE_DISTRIBUTIE"),
    # CUI / Company registration
    (r"(?i)\bCUI\b", "CUI"),
    (r"(?i)certificat\s*(?:de\s*)?inregistrare", "CUI"),
    (r"(?i)certificat\s*constatator", "CUI"),
    # Declaratie de performanta
    (r"(?i)declara[tț]i[ea]\s*(?:de\s*)?performan[tț][aă]", "DECLARATIE_PERFORMANTA"),
    (r"(?i)\bDoP\b", "DECLARATIE_PERFORMANTA"),
    (r"(?i)\bDP\b.*performan", "DECLARATIE_PERFORMANTA"),
    # Combined aviz + agrement
    (r"(?i)aviz.*agrement", "AVIZ_TEHNIC_SI_AGREMENT"),
    # CUI - ONRC / registrul comertului
    (r"(?i)\bONRC\b", "CUI"),
    (r"(?i)registrul\s*comer[tț]ului", "CUI"),
    (r"(?i)certificat\s*(?:de\s*)?[iî]nregistrare\s*fiscal[aă]", "CUI"),
    # Certificat calitate - lab reports
    (r"(?i)buletin\s*(?:de\s*)?analiz[aă]", "CERTIFICAT_CALITATE"),
    (r"(?i)raport\s*(?:de\s*)?[iî]ncerc(?:are|[aă]ri)", "CERTIFICAT_CALITATE"),
    (r"(?i)test\s*report", "CERTIFICAT_CALITATE"),
    # Generic approval patterns (fallback to ALTELE)
    (r"(?i)(?:aprobare.*teav|aprobare.*PEID|aprobare.*produc)", "ALTELE"),
    (r"(?i)aprobare\s*de\s*tip", "ALTELE"),
]

# ---------------------------------------------------------------------------
# Level 2: Text content markers for multi-marker scoring
# Each entry: (regex_pattern, category, weight)
# ---------------------------------------------------------------------------

TEXT_MARKERS = [
    # ISO
    (r"(?i)ISO\s*9001", "ISO", 3),
    (r"(?i)ISO\s*14001", "ISO", 3),
    (r"(?i)ISO\s*45001", "ISO", 3),
    (r"(?i)ISO\s*50001", "ISO", 3),
    (r"(?i)management\s*system\s*certificate", "ISO", 2),
    (r"(?i)certificat\s*de\s*management", "ISO", 2),
    # CE / PED
    (r"(?i)declara[tț]i[ea]\s*CE", "CE", 3),
    (r"(?i)directiva.*echipamente.*presiune", "CE", 2),
    (r"(?i)pressure\s*equipment\s*directive", "CE", 2),
    (r"(?i)marcaj\s*CE", "CE", 2),
    # Fisa tehnica
    (r"(?i)fi[sș][aă]\s*tehnic[aă]", "FISA_TEHNICA", 3),
    (r"(?i)technical\s*data\s*sheet", "FISA_TEHNICA", 3),
    (r"(?i)data\s*sheet", "FISA_TEHNICA", 2),
    (r"(?i)caracteristici\s*tehnice", "FISA_TEHNICA", 2),
    (r"(?i)propriet[aă][tț]i\s*(?:fizice|mecanice)", "FISA_TEHNICA", 2),
    # Agrement
    (r"(?i)agrement\s*tehnic", "AGREMENT", 3),
    (r"(?i)agrementul\s*tehnic", "AGREMENT", 3),
    (r"(?i)agrement.*european", "AGREMENT", 2),
    # Aviz tehnic
    (r"(?i)aviz\s*tehnic", "AVIZ_TEHNIC", 3),
    (r"(?i)avizul\s*tehnic", "AVIZ_TEHNIC", 2),
    # Aviz sanitar
    (r"(?i)aviz\s*sanitar", "AVIZ_SANITAR", 3),
    (r"(?i)ministerul\s*s[aă]n[aă]t[aă][tț]ii", "AVIZ_SANITAR", 2),
    (r"(?i)ap[aă]\s*potabil[aă]", "AVIZ_SANITAR", 1),
    # Declaratie conformitate
    (r"(?i)declara[tț]i[ea]\s*de\s*conformitate", "DECLARATIE_CONFORMITATE", 3),
    (r"(?i)declaration\s*of\s*conformity", "DECLARATIE_CONFORMITATE", 3),
    (r"(?i)conform\s*cu\s*cerin[tț]ele", "DECLARATIE_CONFORMITATE", 1),
    # Certificat calitate
    (r"(?i)certificat\s*de\s*calitate", "CERTIFICAT_CALITATE", 3),
    (r"(?i)certificat\s*de\s*conformitate", "CERTIFICAT_CALITATE", 2),
    (r"(?i)quality\s*certificate", "CERTIFICAT_CALITATE", 3),
    # Autorizatie distributie
    (r"(?i)autorizati[ea]\s*(?:de\s*)?distributi[ea]", "AUTORIZATIE_DISTRIBUTIE", 3),
    (r"(?i)distribu[tț]ie\s*autorizat[aă]", "AUTORIZATIE_DISTRIBUTIE", 2),
    # CUI
    (r"(?i)certificat\s*(?:de\s*)?[iî]nregistrare", "CUI", 3),
    (r"(?i)certificat\s*constatator", "CUI", 3),
    (r"(?i)registrul\s*comer[tț]ului", "CUI", 2),
    # Certificat garantie
    (r"(?i)certificat\s*de\s*garan[tț]ie", "CERTIFICAT_GARANTIE", 3),
    (r"(?i)warranty\s*certificate", "CERTIFICAT_GARANTIE", 3),
    (r"(?i)garan[tț]ie.*ani", "CERTIFICAT_GARANTIE", 1),
    # Declaratie performanta
    (r"(?i)declara[tț]i[ea]\s*(?:de\s*)?performan[tț][aă]", "DECLARATIE_PERFORMANTA", 3),
    (r"(?i)declaration\s*of\s*performance", "DECLARATIE_PERFORMANTA", 3),
    # Combined aviz + agrement
    (r"(?i)aviz\s*tehnic.*agrement", "AVIZ_TEHNIC_SI_AGREMENT", 3),
    (r"(?i)agrement.*aviz\s*tehnic", "AVIZ_TEHNIC_SI_AGREMENT", 3),
    # ISO - additional markers
    (r"(?i)\bASRO\b", "ISO", 2),
    (r"(?i)SR\s*EN\s*\d+", "ISO", 2),
    (r"(?i)\bIQNet\b", "ISO", 2),
    (r"(?i)\bCERTIND\b", "ISO", 2),
    # CE - additional markers
    (r"(?i)organism\s*notificat", "CE", 2),
    (r"(?i)regulament\s*UE", "CE", 2),
    # Agrement - additional markers
    (r"(?i)ETA-\d+", "AGREMENT", 2),
    (r"(?i)\bEOTA\b", "AGREMENT", 2),
    (r"(?i)\bINCERC\b", "AGREMENT", 2),
    (r"(?i)ministerul\s*dezvolt[aă]rii", "AGREMENT", 2),
    # CUI - additional markers
    (r"(?i)punct\s*de\s*lucru", "CUI", 1),
    (r"(?i)capital\s*social", "CUI", 1),
    (r"(?i)\badministrator\b", "CUI", 1),
]

# AI classification system prompt
_AI_CLASSIFICATION_PROMPT = """Esti un expert in clasificarea documentelor din domeniul constructiilor si materialelor de constructii din Romania.

Analizeaza urmatorul text extras dintr-un document PDF si clasifica-l in EXACT UNA din urmatoarele categorii:

Categorii valide:
- ISO: Certificate ISO (9001, 14001, 45001, 50001, etc.)
- CE: Certificate CE / PED / marcaj CE
- FISA_TEHNICA: Fise tehnice / Technical Data Sheets
- AGREMENT: Agremente tehnice
- AVIZ_TEHNIC: Avize tehnice
- AVIZ_SANITAR: Avize sanitare
- DECLARATIE_CONFORMITATE: Declaratii de conformitate
- CERTIFICAT_CALITATE: Certificate de calitate / conformitate
- AUTORIZATIE_DISTRIBUTIE: Autorizatii de distributie
- CUI: Certificate de inregistrare / certificat constatator
- CERTIFICAT_GARANTIE: Certificate de garantie
- DECLARATIE_PERFORMANTA: Declaratii de performanta / DoP
- AVIZ_TEHNIC_SI_AGREMENT: Documente combinate aviz tehnic + agrement
- ALTELE: Alte documente care nu se incadreaza in categoriile de mai sus

Raspunde DOAR cu un JSON in formatul:
{"categorie": "CATEGORIA", "confidence": 0.XX}

Nu include explicatii sau text suplimentar.

Textul documentului:
{text}"""


def classify_by_filename(filename: str) -> tuple[str, float, str] | None:
    """Classify document by filename using regex rules.

    Args:
        filename: The PDF filename.

    Returns:
        Tuple of (category, confidence, method) or None if no match.
    """
    for pattern, category in FILENAME_RULES:
        if re.search(pattern, filename):
            if category == "ALTELE":
                continue
            return (category, 0.95, "filename_regex")
    return None


def classify_by_text(text: str) -> tuple[str, float, str] | None:
    """Classify document by text content using multi-marker scoring.

    Scores each category by summing weights of matching markers.
    Returns the highest-scoring category if score >= 3.

    Args:
        text: Extracted text from the PDF.

    Returns:
        Tuple of (category, confidence, method) or None if no match.
    """
    if not text or not text.strip():
        return None

    scores: dict[str, int] = {}
    for pattern, category, weight in TEXT_MARKERS:
        if re.search(pattern, text):
            scores[category] = scores.get(category, 0) + weight

    if not scores:
        return None

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score < 3:
        return None

    # Normalize confidence: score of 3 = 0.85, higher scores cap at 0.95
    confidence = min(0.85 + (best_score - 3) * 0.02, 0.95)
    return (best_category, confidence, "text_rules")


def _get_text_score(text: str, category: str) -> int:
    """Sum TEXT_MARKERS weights for a specific category against given text.

    Args:
        text: Extracted text from the PDF.
        category: Category to score (must be in VALID_CATEGORIES).

    Returns:
        Total score (sum of matching marker weights), or 0 if text is empty
        or category is unknown.
    """
    if not text or not text.strip():
        return 0
    if category not in VALID_CATEGORIES:
        return 0

    score = 0
    for pattern, cat, weight in TEXT_MARKERS:
        if cat == category and re.search(pattern, text):
            score += weight
    return score


# ---------------------------------------------------------------------------
# Post-classification validation patterns
# Each category maps to a list of regex patterns for confidence boosting.
# If >=2 patterns match, confidence is boosted by +0.05 (capped at 0.99).
# ---------------------------------------------------------------------------

_VALIDATION_PATTERNS: dict[str, list[str]] = {
    "ISO": [
        r"(?i)ISO\s*\d{4,5}",
        r"(?i)management\s*system",
        r"(?i)certificat(?:e|ul)?",
        r"(?i)\bASRO\b",
        r"(?i)\bIQNet\b",
        r"(?i)\bCERTIND\b",
        r"(?i)SR\s*EN\s*\d+",
    ],
    "CE": [
        r"(?i)\bCE\b",
        r"(?i)marcaj\s*CE",
        r"(?i)\bPED\b",
        r"(?i)organism\s*notificat",
        r"(?i)directiva",
    ],
    "FISA_TEHNICA": [
        r"(?i)fi[sș][aă]\s*tehnic[aă]",
        r"(?i)technical\s*data\s*sheet",
        r"(?i)caracteristici\s*tehnice",
        r"(?i)propriet[aă][tț]i",
    ],
    "AGREMENT": [
        r"(?i)agrement\s*tehnic",
        r"(?i)ETA-\d+",
        r"(?i)\bEOTA\b",
        r"(?i)\bINCERC\b",
    ],
    "AVIZ_TEHNIC": [
        r"(?i)aviz\s*tehnic",
        r"(?i)avizul\s*tehnic",
    ],
    "AVIZ_SANITAR": [
        r"(?i)aviz\s*sanitar",
        r"(?i)ministerul\s*s[aă]n[aă]t[aă][tț]ii",
        r"(?i)ap[aă]\s*potabil[aă]",
    ],
    "DECLARATIE_CONFORMITATE": [
        r"(?i)declara[tț]i[ea]\s*de\s*conformitate",
        r"(?i)declaration\s*of\s*conformity",
        r"(?i)conform\s*cu\s*cerin[tț]ele",
    ],
    "CERTIFICAT_CALITATE": [
        r"(?i)certificat\s*de\s*calitate",
        r"(?i)quality\s*certificate",
        r"(?i)certificat\s*de\s*conformitate",
    ],
    "AUTORIZATIE_DISTRIBUTIE": [
        r"(?i)autorizati[ea]\s*(?:de\s*)?distributi[ea]",
        r"(?i)distribu[tț]ie\s*autorizat[aă]",
    ],
    "CUI": [
        r"(?i)certificat\s*(?:de\s*)?[iî]nregistrare",
        r"(?i)certificat\s*constatator",
        r"(?i)registrul\s*comer[tț]ului",
        r"(?i)capital\s*social",
    ],
    "CERTIFICAT_GARANTIE": [
        r"(?i)certificat\s*de\s*garan[tț]ie",
        r"(?i)warranty\s*certificate",
        r"(?i)garan[tț]ie.*ani",
    ],
    "DECLARATIE_PERFORMANTA": [
        r"(?i)declara[tț]i[ea]\s*(?:de\s*)?performan[tț][aă]",
        r"(?i)declaration\s*of\s*performance",
        r"(?i)\bDoP\b",
    ],
    "AVIZ_TEHNIC_SI_AGREMENT": [
        r"(?i)aviz\s*tehnic.*agrement",
        r"(?i)agrement.*aviz\s*tehnic",
    ],
}


def validate_classification(category: str, confidence: float, text: str) -> float:
    """Validate classification by checking text against validation patterns.

    If >=2 patterns match for the given category, boost confidence by +0.05
    (capped at 0.99).

    Args:
        category: The classified category.
        confidence: The current confidence score.
        text: Extracted text from the PDF.

    Returns:
        The (possibly boosted) confidence score.
    """
    patterns = _VALIDATION_PATTERNS.get(category)
    if not patterns or not text:
        return confidence

    match_count = sum(1 for p in patterns if re.search(p, text))

    if match_count >= 2:
        return round(min(confidence + 0.05, 0.99), 2)

    return confidence


def classify_by_ai(text: str, filename: str = "") -> tuple[str, float, str] | None:
    """Classify document using AI via OpenRouter API.

    FIX: temperature changed from 0.1 (monolith bug) to 0.0.

    Args:
        text: Extracted text from the PDF.
        filename: Optional filename for logging context.

    Returns:
        Tuple of (category, confidence, method) or None on failure.
    """
    if not text or not text.strip():
        return None

    # Truncate text to avoid token limits
    text_length = len(text)
    truncated_text = text[:4000]
    was_truncated = text_length > 4000
    prompt = _AI_CLASSIFICATION_PROMPT.format(text=truncated_text)

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": AI_TEMPERATURE,  # 0.0 — NON-NEGOTIABLE (fixed from 0.1)
        "max_tokens": AI_MAX_TOKENS,
    }

    logger.info(
        "AI classification request starting",
        extra={"extra_data": {
            "text_length": text_length,
            "truncated_to": len(truncated_text) if was_truncated else None,
            "model": AI_MODEL,
            "temperature": AI_TEMPERATURE,
            "max_tokens": AI_MAX_TOKENS,
        }},
    )

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=120
        )
        response.raise_for_status()

        response_body = response.text
        logger.info(
            "AI classification response received",
            extra={"extra_data": {
                "status_code": response.status_code,
                "response_length": len(response_body),
            }},
        )

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Strip markdown code fences if present
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content.strip())

        parsed = json.loads(content)
        category = parsed.get("categorie", "ALTELE")
        confidence = float(parsed.get("confidence", 0.5))

        if category not in VALID_CATEGORIES:
            logger.warning(
                "AI returned invalid category: %s",
                category,
                extra={"extra_data": {
                    "invalid_category": category,
                    "raw_response": content[:500],
                }},
            )
            return None

        logger.info(
            "AI classification parsed successfully",
            extra={"extra_data": {
                "category": category,
                "confidence": confidence,
            }},
        )

        return (category, confidence, "ai")

    except requests.exceptions.Timeout:
        logger.error(
            "AI classification timed out",
            extra={"extra_data": {
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
            "AI classification request failed",
            extra={"extra_data": {
                "filename": filename,
                "error": str(e),
                "status_code": status_code,
                "response_body": response_body[:500] if response_body else None,
            }},
        )
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(
            "AI classification response parsing failed",
            extra={"extra_data": {
                "filename": filename,
                "error": str(e),
                "error_type": type(e).__name__,
                "raw_content": content[:500] if "content" in dir() else None,
            }},
        )
        return None


def classify_document(
    filename: str, text: str
) -> tuple[str, float, str]:
    """Classify document using 3-level cascade.

    Level 1: Filename regex (confidence=0.95)
    Level 2: Text content multi-marker scoring (confidence=0.85)
    Level 3: AI classification via OpenRouter (confidence varies)
    Fallback: ALTELE (confidence=0.3)

    Args:
        filename: The PDF filename.
        text: Extracted text from the PDF.

    Returns:
        Tuple of (category, confidence, method).
    """
    # Always run both Level 1 and Level 2 upfront
    fn_result = classify_by_filename(filename)
    txt_result = classify_by_text(text)

    both_match = fn_result is not None and txt_result is not None
    fn_only = fn_result is not None and txt_result is None
    txt_only = fn_result is None and txt_result is not None

    if both_match:
        fn_cat = fn_result[0]
        txt_cat = txt_result[0]
        if fn_cat == txt_cat:
            # Both methods agree — high confidence
            confidence = validate_classification(fn_cat, 0.98, text)
            logger.info(
                "Classified '%s' by filename+text_agree: %s (%.2f)",
                filename, fn_cat, confidence,
            )
            return (fn_cat, confidence, "filename+text_agree")
        else:
            # Disagreement — text overrides if strong and non-ALTELE
            text_score = _get_text_score(text, txt_cat)
            if text_score >= 5 and txt_cat != "ALTELE":
                confidence = validate_classification(txt_cat, 0.90, text)
                logger.info(
                    "Classified '%s' by text_override (score=%d, fn=%s, txt=%s): %s (%.2f)",
                    filename, text_score, fn_cat, txt_cat, txt_cat, confidence,
                )
                return (txt_cat, confidence, "text_override")
            else:
                confidence = validate_classification(fn_cat, 0.85, text)
                logger.info(
                    "Classified '%s' by filename_wins (score=%d, fn=%s, txt=%s): %s (%.2f)",
                    filename, text_score, fn_cat, txt_cat, fn_cat, confidence,
                )
                return (fn_cat, confidence, "filename_wins")

    if fn_only:
        confidence = validate_classification(fn_result[0], fn_result[1], text)
        logger.info(
            "Classified '%s' by filename_regex: %s (%.2f)",
            filename, fn_result[0], confidence,
        )
        return (fn_result[0], confidence, "filename_regex")

    if txt_only:
        confidence = validate_classification(txt_result[0], txt_result[1], text)
        logger.info(
            "Classified '%s' by text_rules: %s (%.2f)",
            filename, txt_result[0], confidence,
        )
        return (txt_result[0], confidence, "text_rules")

    # Level 3: AI classification
    result = classify_by_ai(text, filename=filename)
    if result is not None:
        confidence = validate_classification(result[0], result[1], text)
        logger.info("Classified '%s' by AI: %s (%.2f)", filename, result[0], confidence)
        return (result[0], confidence, result[2])

    # Fallback — AI returned None
    logger.warning("AI classification returned None for '%s', falling back to ALTELE", filename)
    return ("ALTELE", 0.3, "fallback")
