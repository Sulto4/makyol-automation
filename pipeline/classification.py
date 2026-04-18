"""Document classification using 3-level cascade.

Level 1: Filename regex matching with variable confidence (0.70-0.95)
Level 2: Text content priority-ordered rule checks (from MVP)
Level 3: AI classification via OpenRouter (confidence varies)

Ported from clasificare_documente_final.py (MVP) with pipeline improvements.
FIX: classify_by_ai() temperature changed from 0.1 to 0.0.
"""

import re
import json
import logging

import requests

from pipeline.http_client import get_session
from pipeline.config import (
    OPENROUTER_URL,
    AI_MAX_TOKENS,
    settings,
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
# Level 1: Filename regex rules
# Each entry: (regex_pattern, category_string, confidence)
# Confidence varies 0.70-0.95 depending on pattern specificity.
# ---------------------------------------------------------------------------

FILENAME_RULES = [
    # === HIGH PRIORITY: Combined/specific patterns FIRST ===

    # Combined aviz + agrement (MUST be before individual aviz/agrement rules)
    (r"(?i)(?:aviz\s*(?:si|și|\+|&)\s*(?:at|agrement)|aviz[- ]agrement|at\s*\+?\s*agt)", "AVIZ_TEHNIC_SI_AGREMENT", 0.95),

    # Aviz sanitar (before generic aviz)
    (r"(?i)(?:sanitar|\bAVS\b|(?:^|\b)\d+\.\s*AS\b)", "AVIZ_SANITAR", 0.95),

    # CUI in filename
    (r"(?i)\bCUI\b", "CUI", 0.95),
    (r"(?i)certificat\s*(?:de\s*)?inregistrare", "CUI", 0.90),
    (r"(?i)certificat\s*constatator", "CUI", 0.90),
    (r"(?i)\bONRC\b", "CUI", 0.90),
    (r"(?i)registrul\s*comer[tț]ului", "CUI", 0.90),
    (r"(?i)certificat\s*(?:de\s*)?[iî]nregistrare\s*fiscal[aă]", "CUI", 0.90),

    # ISO certificates — [\s_]* handles underscores in filenames
    (r"(?i)(?:ISO[\s_]*\d{4,5}|\bISO\b)", "ISO", 0.90),
    (r"(?i)\b(9001|14001|45001|50001)\b", "ISO", 0.80),

    # CE / PED certificates — ^CE[\s_-] for standalone CE prefix
    (r"(?i)^CE[\s_-]", "CE", 0.90),
    (r"(?i)(?:(?:^|\b)CE(?:\s|[-_]|$)|marcaj\s*CE|CE\s*PED)", "CE", 0.90),
    (r"(?i)\bCE\b.*(?:certificat|certificate|PED)", "CE", 0.90),
    (r"(?i)\bPED\b", "CE", 0.90),
    (r"(?i)certificat.*\bCE\b", "CE", 0.90),
    (r"(?i)excludere.*CE", "CE", 0.90),

    # Declaratie de performanta (before DC)
    (r"(?i)(?:declara[tț]i[ea]\s*(?:de\s*)?performan[tț][aă]|\bDOP\b|^DP[-\s])", "DECLARATIE_PERFORMANTA", 0.95),

    # Declaratie de conformitate (before CC/certificat rules)
    (r"(?i)declara[tț]i[ea]\s*de?\s*conformitate", "DECLARATIE_CONFORMITATE", 0.95),
    (r"(?i)^CC-\d+", "DECLARATIE_CONFORMITATE", 0.90),
    (r"(?i)(?:^|\b)\d+\.\s*DC\b", "DECLARATIE_CONFORMITATE", 0.90),
    (r"(?i)^DC\s+\d", "DECLARATIE_CONFORMITATE", 0.90),
    (r"(?i)certificate?\s*de\s*conformitate", "DECLARATIE_CONFORMITATE", 0.90),
    (r"(?i)\bDC\b(?!\s*-)", "DECLARATIE_CONFORMITATE", 0.85),

    # Certificat de garantie
    (r"(?i)(?:certificat\s*de?\s*garan[tț]ie|\bCG\b)", "CERTIFICAT_GARANTIE", 0.90),

    # Certificat de calitate / Certificate 3.1 (EN 10204)
    (r"(?i)certificat\s*de?\s*calitate", "CERTIFICAT_CALITATE", 0.90),
    (r"(?i)(?:^|\b)\d+\.\s*CC\b", "CERTIFICAT_CALITATE", 0.85),
    (r"(?i)^CC\s+\d", "CERTIFICAT_CALITATE", 0.85),
    (r"(?i)(?:^|\b)\d+\.\s*C\s*3\.1\b", "CERTIFICAT_CALITATE", 0.93),
    (r"(?i)(?:\bMTC\b|mill\s*test\s*cert)", "CERTIFICAT_CALITATE", 0.93),
    (r"(?i)certificat.*P1R", "CERTIFICAT_CALITATE", 0.90),
    (r"(?i)certificat.*CERT", "CERTIFICAT_CALITATE", 0.90),

    # Certificat calitate - lab reports
    (r"(?i)buletin\s*(?:de\s*)?analiz[aă]", "CERTIFICAT_CALITATE", 0.90),
    (r"(?i)raport\s*(?:de\s*)?[iî]ncerc(?:are|[aă]ri)", "CERTIFICAT_CALITATE", 0.90),
    (r"(?i)test\s*report", "CERTIFICAT_CALITATE", 0.90),

    # Agrement tehnic (after combined aviz+agrement)
    (r"(?i)(?:\bagrement\b|\bAGT\b)", "AGREMENT", 0.90),
    (r"(?i)\bAT\b.*\d{3}", "AGREMENT", 0.85),

    # Aviz tehnic (after combined and sanitar)
    (r"(?i)(?:\baviz\s*tehnic\b|\bAVT\b)", "AVIZ_TEHNIC", 0.90),

    # Autorizatie distributie
    (r"(?i)autorizati[ea]\s*(?:de\s*)?distributi[ea]", "AUTORIZATIE_DISTRIBUTIE", 0.95),
    (r"(?i)\bAD\b.*autorizati", "AUTORIZATIE_DISTRIBUTIE", 0.90),
    (r"(?i)(?:autorizat|authorization|autorizare)", "AUTORIZATIE_DISTRIBUTIE", 0.90),

    # Fisa tehnica / Technical data sheets
    (r"(?i)(?:fi[sș][aă]\s*tehnic[aă]|\bFT\b|data\s*sheet|technical\s*data)", "FISA_TEHNICA", 0.90),
    (r"(?i)\bcatalog\b", "FISA_TEHNICA", 0.85),
    # Product-specific filenames that are typically FISA_TEHNICA
    (r"(?i)^(teava|garnitura|cot|teu|reductie|mufa|dop|piesa)\s", "FISA_TEHNICA", 0.70),

    # Generic approval patterns (fallback to ALTELE)
    (r"(?i)(?:aprobare.*teav|aprobare.*PEID|aprobare.*produc)", "ALTELE", 0.50),
    (r"(?i)aprobare\s*de\s*tip", "ALTELE", 0.50),
]

# ---------------------------------------------------------------------------
# Level 2: Text content classification uses priority-ordered rule checks
# (no markers table — logic is in classify_by_text below)
# ---------------------------------------------------------------------------

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
{{"categorie": "CATEGORIA", "confidence": 0.XX}}

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
    for pattern, category, conf in FILENAME_RULES:
        if re.search(pattern, filename):
            if category == "ALTELE":
                continue
            return (category, conf, "filename_regex")
    return None


def classify_by_text(text: str, page_count: int, has_tables: bool) -> tuple[str, float, str] | None:
    """Classify document by text content using priority-ordered rule checks.

    Ported from MVP's classify_by_text. Uses first_500 chars for title
    emphasis. Priority-ordered if/elif checks — first confident match wins.

    Args:
        text: Extracted text from the PDF.
        page_count: Number of pages in the PDF.
        has_tables: Whether the PDF contains tables.

    Returns:
        Tuple of (category, confidence, method) or None if no match.
    """
    if not text or len(text.strip()) < 20:
        return None

    text_lower = text.lower()
    first_500 = text_lower[:500]

    # ---- AVIZ SANITAR: "aviz sanitar" as document TITLE (not just mentioned) ----
    if re.search(r'aviz\s+sanitar', first_500):
        return ("AVIZ_SANITAR", 0.95, "text_rules: Title contains 'Aviz Sanitar'")

    # ---- WRAS APPROVAL (before CE/ISO, because WRAS docs reference ISO/CE in passing) ----
    if re.search(r'\bwras\b', text_lower) and re.search(r'approv|aproba', text_lower):
        return ("CERTIFICAT_CALITATE", 0.92, "text_rules: WRAS material approval certificate")

    # ---- CE MARKING (check BEFORE DC because "EU Certificate of Conformity" for PED = CE) ----
    ce_markers = [
        r'directiva\s+\d{4}/\d+',
        r'directive\s+\d{4}/\d+',
        r'(?<!/)\bce\s+mark(?!\.)',
        r'ped\s+certificate',
        r'pressure\s+equipment\s+directive',
        r'pressure\s+equipment\b',
        r'european\s+conformity',
        r'eu\s+certificate\s+of\s+conformity',
        r'annex\s+iii.*module\s+h',
    ]
    ce_score = sum(1 for p in ce_markers if re.search(p, text_lower))
    if ce_score >= 2:
        return ("CE", 0.92, f"text_rules: CE directive/marking references found ({ce_score} markers)")
    if ce_score == 1 and re.search(r'ce\s+mark|ped\s+certificate|eu\s+certificate|european\s+conformity', text_lower):
        return ("CE", 0.88, "text_rules: Strong CE marker found")

    # ---- DECLARATIE DE PERFORMANTA (before DC, since DC markers are broader) ----
    dp_markers = [
        r'declara[tț]i[ea]\s+de\s+performan[tț][aă]',
        r'declaration\s+of\s+performance',
        r'\bdop\s+nr',
        r'regulamentul.*305/2011',
        r'regulation.*305/2011',
        r'cod\s+unic\s+de\s+identificare\s+al\s+produsului',
    ]
    dp_score = sum(1 for p in dp_markers if re.search(p, text_lower))
    dp_in_title = sum(1 for p in dp_markers if re.search(p, first_500))
    if dp_score >= 2 and dp_in_title >= 1:
        return ("DECLARATIE_PERFORMANTA", 0.92, f"text_rules: Text contains {dp_score} DOP markers ({dp_in_title} in title)")
    if dp_in_title >= 1 and re.search(r'declara[tț]i[ea]\s+de\s+performan', first_500):
        return ("DECLARATIE_PERFORMANTA", 0.88, "text_rules: Title contains 'Declaratie de Performanta'")

    # ---- DECLARATIE DE CONFORMITATE ----
    dc_markers = [
        r'declara[tț]i[ea]\s+de\s+conformitate',
        r'certificat\s+de\s+conformitate',
        r'hg\s*(?:nr\.?)?\s*668',
        r'hot[aă]r[aâ]rea\s+guvernului',
        r'asigur[aă]m.*garantăm.*declar[aă]m',
        r'nu\s+pun\s+[îi]n\s+pericol\s+via[tț]a',
        r'declara[tț]i[ea]\s+nr\.',
        r'certificate?\s+of\s+conformity(?!.*pressure)',
    ]
    dc_score = sum(1 for p in dc_markers if re.search(p, text_lower))
    if dc_score >= 2:
        return ("DECLARATIE_CONFORMITATE", 0.90, f"text_rules: Text contains {dc_score} DC markers")
    if dc_score == 1 and re.search(r'declara[tț]i[ea]\s+de\s+conformitate', first_500):
        return ("DECLARATIE_CONFORMITATE", 0.85, "text_rules: Title contains 'Declaratie de Conformitate'")
    if dc_score == 1 and re.search(r'certificat\s+de\s+conformitate', first_500):
        return ("DECLARATIE_CONFORMITATE", 0.85, "text_rules: Title contains 'Certificat de Conformitate'")

    # ---- FISA TEHNICA (title — BEFORE ISO because ISO logos appear in FT headers) ----
    if re.search(r'fi[sș][aă]\s+tehnic[aă]', first_500):
        return ("FISA_TEHNICA", 0.90, "text_rules: Title: Fisa Tehnica")
    if re.search(r'technical\s+data\s+sheet', first_500):
        return ("FISA_TEHNICA", 0.90, "text_rules: Title: Technical Data Sheet")

    # ---- AGREMENT TEHNIC ----
    agrement_markers = [
        r'agrement\s+tehnic',
        r'ministerul\s+dezvolt[aă]rii',
        r'consiliul\s+tehnic\s+permanent',
        r'grupa\s+specializat[aă]',
    ]
    agr_score = sum(1 for p in agrement_markers if re.search(p, text_lower))
    if agr_score >= 2:
        if re.search(r'aviz\s+tehnic', first_500):
            return ("AVIZ_TEHNIC_SI_AGREMENT", 0.90, "text_rules: Both Aviz Tehnic and Agrement in text")
        return ("AGREMENT", 0.90, f"text_rules: Text contains {agr_score} Agrement markers")

    # ---- AVIZ TEHNIC ----
    if re.search(r'aviz\s+tehnic', first_500) and not re.search(r'agrement', first_500):
        return ("AVIZ_TEHNIC", 0.85, "text_rules: Title contains 'Aviz Tehnic' without Agrement")

    # ---- CERTIFICAT CALITATE ----
    if re.search(r'certificat\s+de\s+calitate', first_500):
        return ("CERTIFICAT_CALITATE", 0.90, "text_rules: Title: Certificat de Calitate")

    # ---- CERTIFICAT GARANTIE ----
    if re.search(r'certificat\s+de\s+garan[tț]ie', first_500):
        return ("CERTIFICAT_GARANTIE", 0.90, "text_rules: Title: Certificat de Garantie")

    # ---- AUTORIZATIE DISTRIBUTIE (before CUI) ----
    autorizatie_markers = [
        r'autoriz[aă]m\s+prin\s+prezenta',
        r's[aă]\s+distribui[ea]',
        r'autorizat\s+s[aă]',
        r'authorization\s+letter',
        r'pe\s+teritoriul\s+rom[aâ]niei',
        r'autorizare\s+de\s+comercializare',
        r'authorized.*distribut',
    ]
    aut_score = sum(1 for p in autorizatie_markers if re.search(p, text_lower))
    if aut_score >= 2:
        return ("AUTORIZATIE_DISTRIBUTIE", 0.90, f"text_rules: Text contains {aut_score} authorization markers")
    if aut_score == 1 and re.search(r'autorizare\s+de\s+comercializare', first_500):
        return ("AUTORIZATIE_DISTRIBUTIE", 0.85, "text_rules: Title contains 'Autorizare de Comercializare'")

    # ---- CUI ----
    cui_indicators = [
        re.search(r'certificat\s+de\s+[îi]nregistrare', text_lower),
        re.search(r'cod\s+unic\s+de\s+[îi]nregistrare', text_lower),
        re.search(r'registrul\s+comer[tț]ului', text_lower),
        re.search(r'oficiul\s+registrului', text_lower),
    ]
    if sum(1 for x in cui_indicators if x) >= 2:
        if not re.search(r'declara[tț]i[ea]\s+de\s+performan', text_lower) and \
           not re.search(r'fi[sș][aă]\s+tehnic[aă]|domeniu\s+de\s+utilizare|specifica[tț]i', text_lower):
            return ("CUI", 0.90, "text_rules: Company registration document (2+ indicators)")
    if sum(1 for x in cui_indicators if x) >= 1:
        if re.search(r'certificat\s+de\s+[îi]nregistrare', first_500):
            return ("CUI", 0.88, "text_rules: Title: Certificat de Inregistrare")

    # ---- DECLARATIE PERFORMANTA (second chance) ----
    if re.search(r'declara[tț]i[ea]\s+de\s+performan[tț][aă]', text_lower) or \
       re.search(r'regulamentul.*305/2011|regulation.*305/2011', text_lower):
        return ("DECLARATIE_PERFORMANTA", 0.90, "text_rules: Declaration of Performance markers found")

    # ---- ISO MANAGEMENT SYSTEM CERTIFICATES ----
    # IMPORTANT: Checked AFTER all specific document types because many documents
    # have ISO certification logos in headers (TÜV, Bureau Veritas, etc.) that
    # produce false ISO matches. A real ISO certificate's PRIMARY content is the
    # certification itself — not a product spec, not a declaration, not a data sheet.
    iso_mgmt_title = re.search(r'iso\s*(9001|14001|45001|50001)', first_500)
    iso_mgmt_body = re.search(r'iso\s*(9001|14001|45001|50001)', text_lower)
    iso_mgmt = iso_mgmt_title or iso_mgmt_body
    if iso_mgmt:
        # Exclude if document is clearly another type (ISO logo in header)
        other_doc_types = [
            r'fi[sș][aă]\s+tehnic[aă]',
            r'certificat\s+de\s+calitate',
            r'certificat\s+de\s+garan[tț]ie',
            r'declara[tț]i[ea]\s+de\s+conformitate',
            r'declara[tț]i[ea]\s+de\s+performan[tț][aă]',
            r'aviz\s+sanitar',
            r'agrement\s+tehnic',
            r'autorizare|autorizati[ea]',
        ]
        is_other_type = any(re.search(p, text_lower) for p in other_doc_types)

        if not is_other_type:
            cert_context = any(w in first_500 for w in [
                'certificate', 'certificat', 'certification', 'certified',
                'scope', 'validity', 'valabil', 'accredit',
                'management system', 'sistem de management'
            ])
            if cert_context and iso_mgmt_title:
                return ("ISO", 0.95, f"text_rules: ISO {iso_mgmt.group(1)} certificate in title")
            if cert_context and not iso_mgmt_title:
                return ("ISO", 0.78, f"text_rules: ISO {iso_mgmt.group(1)} in body with cert context")
            if iso_mgmt_title:
                return ("ISO", 0.80, f"text_rules: ISO {iso_mgmt.group(1)} in title without cert context")

    # ---- FISA TEHNICA (body: DN/PN/SDR markers + tables) ----
    ft_markers = [
        r'fi[sș][aă]\s+tehnic[aă]',
        r'technical\s+data\s+sheet',
        r'domeniu\s+de\s+utilizare',
        r'norma\s+de\s+produs',
        r'specifica[tț]i[ei]\s+tehnic[ei]',
    ]
    ft_score = sum(1 for p in ft_markers if re.search(p, text_lower))

    product_spec_markers = [
        r'\bDN\s*\d+',
        r'\bPN\s*\d+',
        r'\bSDR\s*\d+',
        r'\bDE\s*\d+',
        r'dimensiun[ie]',
        r'greutate',
        r'material[:\s]',
        r'diametr',
        r'grosime.*pere[tț]',
        r'\bmm\b.*\bmm\b',
    ]
    spec_score = sum(1 for p in product_spec_markers if re.search(p, text_lower))

    if ft_score >= 1:
        return ("FISA_TEHNICA", 0.90, f"text_rules: Technical data sheet markers ({ft_score})")
    if spec_score >= 3 and page_count >= 1:
        return ("FISA_TEHNICA", 0.80, f"text_rules: Product specification with {spec_score} technical markers")
    if spec_score >= 2 and has_tables:
        return ("FISA_TEHNICA", 0.75, f"text_rules: Has tables + {spec_score} technical spec markers")

    return None


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
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ai_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": settings.ai_temperature,
        "max_tokens": AI_MAX_TOKENS,
    }

    logger.info(
        "AI classification request starting",
        extra={"extra_data": {
            "text_length": text_length,
            "truncated_to": len(truncated_text) if was_truncated else None,
            "model": settings.ai_model,
            "temperature": settings.ai_temperature,
            "max_tokens": AI_MAX_TOKENS,
        }},
    )

    try:
        response = get_session().post(
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
    filename: str, text: str, page_count: int = 0, has_tables: bool = False
) -> tuple[str, float, str]:
    """Classify document using 3-level cascade.

    Level 1: Filename regex (confidence=0.70-0.95, variable)
    Level 2: Text content priority-ordered rule checks (confidence varies)
    Level 3: AI classification via OpenRouter (confidence varies)
    Fallback: ALTELE (confidence=0.3)

    Args:
        filename: The PDF filename.
        text: Extracted text from the PDF.
        page_count: Number of pages in the PDF.
        has_tables: Whether the PDF contains tables.

    Returns:
        Tuple of (category, confidence, method).
    """
    # Always run both Level 1 and Level 2 upfront
    fn_result = classify_by_filename(filename)
    txt_result = classify_by_text(text, page_count, has_tables)

    both_match = fn_result is not None and txt_result is not None
    fn_only = fn_result is not None and txt_result is None
    txt_only = fn_result is None and txt_result is not None

    # Track cascade outcome for structured logging
    ai_result = None
    final_result = None
    decision_reason = None

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
            final_result = (fn_cat, confidence, "filename+text_agree")
            decision_reason = "filename+text_agree"
        else:
            # Disagreement — filename wins. Humans name files intentionally and
            # filename is the most reliable signal. Text often contains references
            # to other categories (e.g., ISO standards in a DC document) that mislead
            # text scoring. We never override a strong filename match.
            confidence = validate_classification(fn_cat, 0.90, text)
            logger.info(
                "Classified '%s' by filename_wins (fn=%s, txt=%s): %s (%.2f)",
                filename, fn_cat, txt_cat, fn_cat, confidence,
            )
            final_result = (fn_cat, confidence, "filename_wins")
            decision_reason = "filename_wins"

    if final_result is None and fn_only:
        confidence = validate_classification(fn_result[0], fn_result[1], text)
        logger.info(
            "Classified '%s' by filename_regex: %s (%.2f)",
            filename, fn_result[0], confidence,
        )
        final_result = (fn_result[0], confidence, "filename_regex")
        decision_reason = "filename_regex"

    if final_result is None and txt_only:
        confidence = validate_classification(txt_result[0], txt_result[1], text)
        logger.info(
            "Classified '%s' by text_rules: %s (%.2f)",
            filename, txt_result[0], confidence,
        )
        final_result = (txt_result[0], confidence, "text_rules")
        decision_reason = "text_rules"

    # Level 3: AI classification
    if final_result is None:
        ai_result = classify_by_ai(text, filename=filename)
        if ai_result is not None:
            confidence = validate_classification(ai_result[0], ai_result[1], text)
            logger.info("Classified '%s' by AI: %s (%.2f)", filename, ai_result[0], confidence)
            final_result = (ai_result[0], confidence, ai_result[2])
            decision_reason = "ai"

    # Fallback — AI returned None
    if final_result is None:
        logger.warning("AI classification returned None for '%s', falling back to ALTELE", filename)
        final_result = ("ALTELE", 0.3, "fallback")
        decision_reason = "fallback"

    # Structured cascade logging — single comprehensive entry
    logger.info("Classification cascade complete", extra={"extra_data": {
        "step": "classification_cascade",
        "filename": filename,
        "level1_filename": {"category": fn_result[0], "confidence": fn_result[1]} if fn_result else None,
        "level2_text": {"category": txt_result[0], "confidence": txt_result[1]} if txt_result else None,
        "level3_ai": {"category": ai_result[0], "confidence": ai_result[1]} if ai_result else None,
        "final": {
            "category": final_result[0],
            "confidence": final_result[1],
            "method": final_result[2],
        },
        "decision_reason": decision_reason,
    }})

    return final_result
