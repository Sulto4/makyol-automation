"""Regex-based data extraction as fallback for AI extraction.

Extracts company names, expiration dates, and addresses from document
text using Romanian-specific patterns. Returns a standard 6-field dict.
"""

import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Company patterns
# ---------------------------------------------------------------------------

_COMPANY_PATTERNS = [
    # S.C. ... S.R.L. / S.A.
    re.compile(
        r'S\.?C\.?\s+(.{3,80}?)\s+S\.?(?:R\.?L|A)\.?',
        re.IGNORECASE,
    ),
    # societatea ... S.R.L. / S.A.
    re.compile(
        r'[Ss]ocietatea\s+(.{3,80}?)\s+S\.?(?:R\.?L|A)\.?',
        re.IGNORECASE,
    ),
]

# ---------------------------------------------------------------------------
# Date patterns
# ---------------------------------------------------------------------------

_DATE_KEYWORD = re.compile(
    r'(?:valabil[aă]?|expir[aă]|valabilitate|data\s+expir[aă]rii)'
    r'[^0-9]{0,30}?'
    r'(\d{2}[./]\d{2}[./]\d{4})',
    re.IGNORECASE,
)

_DATE_STANDALONE = re.compile(r'(\d{2}[./]\d{2}[./]\d{4})')

# ---------------------------------------------------------------------------
# Address patterns
# ---------------------------------------------------------------------------

_ADDRESS_PATTERNS = [
    # keyword (sediul/adresa) followed by address
    re.compile(
        r'(?:sediul|adresa)[:\s]+(.{10,150})',
        re.IGNORECASE,
    ),
    # street prefix patterns
    re.compile(
        r'((?:Str|B-dul|Calea|[SȘș]os|Pia[tț]a)\.?\s+.{5,120})',
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Individual extractors
# ---------------------------------------------------------------------------


def extract_company_regex(text: str) -> Optional[str]:
    """Extract company name using Romanian business entity patterns.

    Looks for S.C. ... S.R.L./S.A. and societatea ... S.R.L. patterns.

    Args:
        text: Document text to search.

    Returns:
        Company name or None.
    """
    for pattern in _COMPANY_PATTERNS:
        match = pattern.search(text)
        if match:
            company = match.group(0).strip()
            logger.debug("Regex company match: %s", company)
            return company
    return None


def extract_date_regex(text: str) -> Optional[str]:
    """Extract expiration date using validity/expiration keywords.

    Looks for valabil/expira/valabilitate keywords near DD.MM.YYYY
    or DD/MM/YYYY dates. Normalizes separators to dots.

    Args:
        text: Document text to search.

    Returns:
        Date string in DD.MM.YYYY format or None.
    """
    match = _DATE_KEYWORD.search(text)
    if match:
        date_str = match.group(1).replace("/", ".")
        logger.debug("Regex date match (keyword): %s", date_str)
        return date_str
    return None


def extract_address_regex(text: str) -> Optional[str]:
    """Extract address using street prefix and keyword patterns.

    Looks for Str/B-dul/Calea/Sos/Piata prefixes and sediul/adresa keywords.

    Args:
        text: Document text to search.

    Returns:
        Address string or None.
    """
    for pattern in _ADDRESS_PATTERNS:
        match = pattern.search(text)
        if match:
            # Use group(1) if capturing group exists, else group(0)
            addr = match.group(1).strip().rstrip(".,;")
            logger.debug("Regex address match: %s", addr)
            return addr
    return None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def regex_extract(text: str, category: str) -> Dict[str, Optional[str]]:
    """Extract standard fields from text using regex patterns.

    Args:
        text: Document text to search.
        category: Document category (e.g. 'ISO').

    Returns:
        Dict with keys: companie, material, data_expirare,
        producator, distribuitor, adresa_producator, adresa_distribuitor.
        material, producator, and adresa_distribuitor are always None.
    """
    logger.info("Running regex extraction for category %s", category)

    result = {
        "companie": extract_company_regex(text),
        "material": None,
        "data_expirare": extract_date_regex(text),
        "producator": None,
        "distribuitor": None,
        "adresa_producator": extract_address_regex(text),
        "adresa_distribuitor": None,
    }

    filled = sum(1 for v in result.values() if v is not None)
    logger.info("Regex extraction found %s/7 fields for %s", filled, category)

    return result
