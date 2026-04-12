"""Fuzzy company name matching and normalization against knowledge_base.json."""

import json
import re
from typing import Dict, Optional, Tuple

from rapidfuzz import fuzz

from pipeline.config import KNOWLEDGE_BASE_PATH

# ---------------------------------------------------------------------------
# Load knowledge base at import time
# ---------------------------------------------------------------------------

def _load_knowledge_base() -> dict:
    """Load and return the knowledge base JSON."""
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_KB = _load_knowledge_base()

# Pre-build alias → canonical lookup
ALIAS_TO_CANONICAL: Dict[str, str] = {}
_ADDRESS_ALIASES: Dict[str, str] = {}

for _key, _company in _KB.get("companies", {}).items():
    canonical = _company["canonical"]
    for alias in _company.get("aliases", []):
        ALIAS_TO_CANONICAL[alias.upper().strip()] = canonical
    # Address aliases → canonical address
    canonical_addr = _company.get("canonical_address", "")
    if canonical_addr:
        for addr_alias in _company.get("address_aliases", []):
            _ADDRESS_ALIASES[addr_alias.upper().strip()] = canonical_addr

# Fuzzy match threshold (Levenshtein / WRatio)
MATCH_THRESHOLD = 85

# ---------------------------------------------------------------------------
# Helper patterns
# ---------------------------------------------------------------------------

_CHINESE_CHARS_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]+")
_CUI_PATTERN_RE = re.compile(r"\b(RO)?\d{5,10}\b", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")


def strip_chinese_chars(text: str) -> str:
    """Remove Chinese/CJK characters from text."""
    return _CHINESE_CHARS_RE.sub("", text).strip()


def _strip_cui(text: str) -> str:
    """Remove CUI patterns (e.g. RO3094980, 3094980) from text."""
    return _CUI_PATTERN_RE.sub("", text).strip()


def _clean_name(name: str) -> str:
    """Normalize whitespace after stripping."""
    return _WHITESPACE_RE.sub(" ", name).strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_company_name(raw_name: str) -> Tuple[str, bool]:
    """Normalize a company name against the knowledge base.

    Returns:
        (normalized_name, was_matched) — was_matched is True when the name
        was resolved via exact or fuzzy match against the knowledge base.
    """
    if not raw_name or not raw_name.strip():
        return (raw_name or "", False)

    # Pre-process: strip Chinese chars, CUI, clean whitespace
    cleaned = strip_chinese_chars(raw_name)
    cleaned = _strip_cui(cleaned)
    cleaned = _clean_name(cleaned)

    if not cleaned:
        return (raw_name.strip(), False)

    # 1. Exact match (case-insensitive)
    upper_cleaned = cleaned.upper()
    if upper_cleaned in ALIAS_TO_CANONICAL:
        return (ALIAS_TO_CANONICAL[upper_cleaned], True)

    # 2. Fuzzy match against all aliases
    best_score = 0.0
    best_canonical: Optional[str] = None

    for alias_upper, canonical in ALIAS_TO_CANONICAL.items():
        score = fuzz.WRatio(upper_cleaned, alias_upper)
        if score > best_score:
            best_score = score
            best_canonical = canonical

    if best_score >= MATCH_THRESHOLD and best_canonical is not None:
        return (best_canonical, True)

    # No match — return cleaned version
    return (cleaned, False)


def normalize_address(raw_address: str) -> Tuple[str, bool]:
    """Normalize an address against known address aliases.

    Returns:
        (normalized_address, was_matched)
    """
    if not raw_address or not raw_address.strip():
        return (raw_address or "", False)

    cleaned = _clean_name(raw_address)
    upper = cleaned.upper()

    # Exact alias match
    if upper in _ADDRESS_ALIASES:
        return (_ADDRESS_ALIASES[upper], True)

    # Fuzzy match
    best_score = 0.0
    best_addr: Optional[str] = None

    for alias_upper, canonical_addr in _ADDRESS_ALIASES.items():
        score = fuzz.WRatio(upper, alias_upper)
        if score > best_score:
            best_score = score
            best_addr = canonical_addr

    if best_score >= MATCH_THRESHOLD and best_addr is not None:
        return (best_addr, True)

    return (cleaned, False)
