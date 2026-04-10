"""Configuration constants, document type mappings, and regex patterns.

Ported from the prototype (proceseaza_documente.py) with fixes:
- Tehnoworld and Zakprest folders populate the distributor field
- DocumentType enum values used for classification targets
"""

from src.models import DocumentType


# ---------------------------------------------------------------------------
# Document classification: filename-based patterns
# ---------------------------------------------------------------------------
# Each entry: (regex_pattern, DocumentType)

FILENAME_PATTERNS: list[tuple[str, DocumentType]] = [
    (r'(?i)(?:\bFT\b.*\bPEHD\b|\bFT\b.*\bteav|fisa\s*tehnica|\bFT\b.*\bfiting|data\s*sheet)', DocumentType.FISA_TEHNICA),
    (r'(?i)ISO\s*9001', DocumentType.ISO_9001),
    (r'(?i)ISO\s*14001', DocumentType.ISO_14001),
    (r'(?i)ISO\s*45001', DocumentType.ISO_45001),
    (r'(?i)ISO\s*50001', DocumentType.ISO_50001),
    (r'(?i)(?:\bAVS\b|aviz\s*sanitar)', DocumentType.AVIZ_SANITAR),
    (r'(?i)(?:\bAVT\b|aviz\s*tehnic)', DocumentType.AVIZ_TEHNIC),
    (r'(?i)(?:\bAGT\b|agrement\s*tehnic|\bAT\b.*\d{3}|aviz.*agrement)', DocumentType.AGREMENT_TEHNIC),
    (r'(?i)(?:\bDC\b(?!\s*-)|declarati[ea]\s*de\s*conformitate)', DocumentType.DECLARATIE_CONFORMITATE),
    (r'(?i)(?:\bCC\b|certificat\s*de\s*calitate|certificat\s*de\s*conformitate)', DocumentType.CERTIFICAT_CONFORMITATE),
    (r'(?i)(?:\bCG\b|certificat\s*de\s*garantie)', DocumentType.CERTIFICAT_GARANTIE),
    (r'(?i)(?:certificat.*P1R|certificat.*CERT)', DocumentType.CERTIFICAT_CONFORMITATE),
    (r'(?i)(?:aprobare.*teav|aprobare.*PEID|aprobare.*produc)', DocumentType.OTHER),
]

# ---------------------------------------------------------------------------
# Document classification: text content-based patterns
# ---------------------------------------------------------------------------

TEXT_PATTERNS: list[tuple[str, DocumentType]] = [
    (r'(?i)(?:fi[sș][aă]\s*tehnic[aă]|data\s*sheet|technical\s*data)', DocumentType.FISA_TEHNICA),
    (r'(?i)ISO\s*9001', DocumentType.ISO_9001),
    (r'(?i)ISO\s*14001', DocumentType.ISO_14001),
    (r'(?i)ISO\s*45001', DocumentType.ISO_45001),
    (r'(?i)ISO\s*50001', DocumentType.ISO_50001),
    (r'(?i)aviz\s*sanitar', DocumentType.AVIZ_SANITAR),
    (r'(?i)aviz\s*tehnic', DocumentType.AVIZ_TEHNIC),
    (r'(?i)agrement\s*tehnic', DocumentType.AGREMENT_TEHNIC),
    (r'(?i)declara[tț]i[ea]\s*de\s*conformitate', DocumentType.DECLARATIE_CONFORMITATE),
    (r'(?i)certificat\s*de\s*calitate', DocumentType.CERTIFICAT_CONFORMITATE),
    (r'(?i)certificat\s*de\s*garan[tț]ie', DocumentType.CERTIFICAT_GARANTIE),
    (r'(?i)certificat\s*de\s*conformitate', DocumentType.CERTIFICAT_CONFORMITATE),
    (r'(?i)supervizorul\s*aprob[aă]', DocumentType.OTHER),
]

# ---------------------------------------------------------------------------
# Known producers (folder name key, upper-cased -> full company name)
# ---------------------------------------------------------------------------

KNOWN_PRODUCERS: dict[str, str] = {
    'TERAPLAST': 'TERAPLAST SA',
    'VALROM': 'VALROM INDUSTRIE SRL',
    'TEHNOWORLD': 'TEHNO WORLD SRL',
    'TEHNO WORLD': 'TEHNO WORLD SRL',
    'ZAKPREST': 'SC ZAKPREST CONSTRUCT SRL',
}

# ---------------------------------------------------------------------------
# Known materials (folder name key, upper-cased -> default material)
# ---------------------------------------------------------------------------

KNOWN_MATERIALS: dict[str, str] = {
    'TERAPLAST': 'Tevi PEHD PE100 pentru apa',
    'VALROM': 'Tevi PEHD PE100/PE100RC pentru apa',
    'TEHNOWORLD': 'Tevi PEHD PE100 pentru apa',
    'TEHNO WORLD': 'Tevi PEHD PE100 pentru apa',
    'ZAKPREST': 'Materiale constructii',
}

# ---------------------------------------------------------------------------
# Supplier roles: producer vs distributor per folder
# FIX: Tehnoworld and Zakprest are distributors, not producers.
# ---------------------------------------------------------------------------

SUPPLIER_ROLES: dict[str, dict[str, str]] = {
    'TERAPLAST': {
        'producer': 'TERAPLAST SA',
    },
    'VALROM': {
        'producer': 'VALROM INDUSTRIE SRL',
    },
    'Tehnoworld': {
        'distributor': 'TEHNO WORLD SRL',
    },
    'Zakprest': {
        'distributor': 'SC ZAKPREST CONSTRUCT SRL',
    },
}

# ---------------------------------------------------------------------------
# Romanian month name mapping (for date normalisation)
# ---------------------------------------------------------------------------

MONTH_MAP_RO: dict[str, str] = {
    'ianuarie': '01',
    'februarie': '02',
    'martie': '03',
    'aprilie': '04',
    'mai': '05',
    'iunie': '06',
    'iulie': '07',
    'august': '08',
    'septembrie': '09',
    'octombrie': '10',
    'noiembrie': '11',
    'decembrie': '12',
}

# ---------------------------------------------------------------------------
# Date extraction patterns (expiry / validity dates)
# ---------------------------------------------------------------------------

DATE_PATTERNS: list[str] = [
    r'(?i)valabil[aă]?\s*(?:pân[aă]\s*(?:la|in)|până\s*(?:la|în))\s*(?:data\s*de\s*)?(\d{1,2}[./]\d{1,2}[./]\d{4})',
    r'(?i)valabil[aă]?\s*(?:pân[aă]\s*(?:la|in)|până\s*(?:la|în))\s*(?:data\s*de\s*)?(\d{1,2}\s+\w+\s+\d{4})',
    r'(?i)valid\s*(?:until|până)\s*(?:la\s*)?(?:data\s*)?(\d{4}-\d{2}-\d{2})',
    r'(?i)valabil[aă]?\s*p[aâ]n[aă]\s*la\s*data\s*de\s*(\d{1,2}[./]\d{1,2}[./]\d{4})',
    r'(?i)p[aâ]n[aă]\s*(?:la|in|în)\s*(\d{1,2}\s+\w+\s+\d{4})',
    r'(?i)valabil[aă]?\s*p[aâ]n[aă]\s*la\s*data\s*(\d{4}-\d{2}-\d{2})',
    r'(?i)valabil\s*din\s*[\d.]+\s*p[aâ]n[aă]\s*[iî]n\s*(\d{1,2}[./]\d{1,2}[./]\d{4})',
]

# ---------------------------------------------------------------------------
# Material extraction patterns
# ---------------------------------------------------------------------------

MATERIAL_PATTERNS: list[str] = [
    r'(?i)((?:tevi|țevi)\s+(?:din\s+)?PE(?:ID|HD)\s+(?:PE\s*100\s*(?:RC|CERT)?)?(?:\s+(?:pentru|pt\.?)\s+(?:ap[aă]|instalat))?[^\n]{0,30})',
    r'(?i)((?:tevi|țevi)\s+(?:și|si)\s+fitinguri\s+[^\n]{0,50})',
    r'(?i)DENUMIRE\s*PRODUS[:\s]*([^\n]+)',
    r'(?i)Produs[:\s]+((?:Tevi|Țevi)[^\n]+)',
]

# ---------------------------------------------------------------------------
# Producer extraction patterns (from PDF text content)
# ---------------------------------------------------------------------------

PRODUCER_PATTERNS: list[str] = [
    r'(?i)produc[aă]tor[:\s]+([A-Z][A-Z\s.]+(?:S\.?R\.?L\.?|S\.?A\.?))',
    r'(?i)titularul\s*certificatului[:\s]+([A-Z][A-Z\s.]+(?:S\.?R\.?L\.?|S\.?A\.?))',
    r'(?i)fabricant(?:ul)?[:\s]+(?:S\.?C\.?\s*)?([A-Z][A-Z\s.]+(?:S\.?R\.?L\.?|S\.?A\.?))',
]

# ---------------------------------------------------------------------------
# Distributor extraction patterns (from PDF text content)
# ---------------------------------------------------------------------------

DISTRIBUTOR_PATTERNS: list[str] = [
    r'(?i)distribuit(?:or)?[:\s]+(?:S\.?C\.?\s*)?([A-Z][A-Z\s.]+(?:S\.?R\.?L\.?|S\.?A\.?))',
    r'(?i)furnizor[:\s]+(?:S\.?C\.?\s*)?([A-Z][A-Z\s.]+(?:S\.?R\.?L\.?|S\.?A\.?))',
]
