"""Fuzzy company name matching and normalization against knowledge_base.json."""

import json
import logging
import re
from typing import Dict, Optional, Tuple

from rapidfuzz import fuzz

from pipeline.config import KNOWLEDGE_BASE_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load knowledge base at import time
# ---------------------------------------------------------------------------

def _load_knowledge_base() -> dict:
    """Load and return the knowledge base JSON."""
    with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


try:
    _KB = _load_knowledge_base()
except (FileNotFoundError, json.JSONDecodeError) as exc:
    logger.critical("Failed to load knowledge base from %s: %s", KNOWLEDGE_BASE_PATH, exc)
    _KB = {"companies": {}}

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

# ---------------------------------------------------------------------------
# Known companies exact-match overrides (ported from MVP)
# ---------------------------------------------------------------------------
# These take priority over fuzzy / knowledge_base matching. Applied AFTER
# SC/S.C. prefix removal and SRL/SA suffix normalization.

KNOWN_COMPANIES: Dict[str, str] = {
    "TERAPLAST": "TERAPLAST SA",
    "TERAPLAST SA": "TERAPLAST SA",
    "TERAPLAST SRL": "TERAPLAST SA",
    "TERAPIA": "TERAPLAST SA",
    "VALROM INDUSTRIE": "VALROM INDUSTRIE SRL",
    "VALROM INDUSTRIE SRL": "VALROM INDUSTRIE SRL",
    "VALROM": "VALROM INDUSTRIE SRL",
    "VALROM INDUSTRIE SA": "VALROM INDUSTRIE SRL",
    "TEHNO WORLD": "TEHNO WORLD SRL",
    "TEHNO WORLD SRL": "TEHNO WORLD SRL",
    "TEHNOWORLD": "TEHNO WORLD SRL",
    "TEHNOWORLD SRL": "TEHNO WORLD SRL",
    "ZAKPREST CONSTRUCT": "ZAKPREST CONSTRUCT SRL",
    "ZAKPREST CONSTRUCT SRL": "ZAKPREST CONSTRUCT SRL",
}

# Fuzzy match threshold (Levenshtein / WRatio)
MATCH_THRESHOLD = 85

# ---------------------------------------------------------------------------
# Helper patterns
# ---------------------------------------------------------------------------

_CHINESE_CHARS_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]+")
_CUI_PATTERN_RE = re.compile(r"\b(RO)?\d{5,10}\b", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

# SC/S.C. prefix removal (archaic Romanian legal prefix)
_SC_PREFIX_RE = re.compile(r"^S\.?\s*C\.?\s+", re.IGNORECASE)

# SRL/SA suffix normalization
_SRL_SUFFIX_RE = re.compile(r"\s+S\.?\s*R\.?\s*L\.?\s*$", re.IGNORECASE)
_SA_SUFFIX_RE = re.compile(r"\s+S\.?\s*A\.?\s*$", re.IGNORECASE)
_SA_HYPHENATED_RE = re.compile(r"-S\.?\s*A\.?\s*$", re.IGNORECASE)


def strip_chinese_chars(text: str) -> str:
    """Remove Chinese/CJK characters from text."""
    return _CHINESE_CHARS_RE.sub("", text).strip()


def _strip_cui(text: str) -> str:
    """Remove CUI patterns (e.g. RO3094980, 3094980) from text."""
    return _CUI_PATTERN_RE.sub("", text).strip()


def _clean_name(name: str) -> str:
    """Normalize whitespace after stripping."""
    return _WHITESPACE_RE.sub(" ", name).strip()


def _remove_sc_prefix(text: str) -> str:
    """Remove SC / S.C. prefix (archaic Romanian legal prefix)."""
    return _SC_PREFIX_RE.sub("", text).strip()


def _normalize_legal_suffix(text: str) -> str:
    """Normalize SRL/SA legal suffixes to canonical form.

    Handles: S.R.L. → SRL, S.A. → SA, hyphenated forms like TERAPLAST-SA.
    """
    text = _SRL_SUFFIX_RE.sub(" SRL", text)
    text = _SA_SUFFIX_RE.sub(" SA", text)
    text = _SA_HYPHENATED_RE.sub(" SA", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_company_name(raw_name: str) -> Tuple[str, bool]:
    """Normalize a company name against the knowledge base.

    Pipeline:
      1. Pre-process (strip Chinese, CUI, whitespace)
      2. SC prefix removal + SRL/SA suffix normalization
      3. KNOWN_COMPANIES exact-match override
      4. Knowledge-base exact match (aliases)
      5. Knowledge-base fuzzy match

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

    # --- SC prefix removal + SRL/SA suffix normalization ---
    cleaned = _remove_sc_prefix(cleaned)
    cleaned = _normalize_legal_suffix(cleaned)
    cleaned = _clean_name(cleaned)

    # --- KNOWN_COMPANIES exact-match override (priority over KB) ---
    upper_cleaned = cleaned.upper()
    if upper_cleaned in KNOWN_COMPANIES:
        canonical = KNOWN_COMPANIES[upper_cleaned]
        logger.info(
            "Known company match: raw='%s' → canonical='%s'",
            raw_name[:60],
            canonical,
            extra={"extra_data": {
                "original": raw_name[:60],
                "normalized": canonical,
                "match_type": "exact_known",
            }},
        )
        return (canonical, True)

    # --- Knowledge-base exact match (case-insensitive) ---
    if upper_cleaned in ALIAS_TO_CANONICAL:
        canonical = ALIAS_TO_CANONICAL[upper_cleaned]
        logger.info(
            "Exact alias match: raw='%s' → canonical='%s'",
            raw_name[:60],
            canonical,
            extra={"extra_data": {
                "original": raw_name[:60],
                "normalized": canonical,
                "match_type": "exact_known",
            }},
        )
        return (canonical, True)

    # --- Knowledge-base fuzzy match ---
    best_score = 0.0
    best_canonical: Optional[str] = None

    for alias_upper, canonical in ALIAS_TO_CANONICAL.items():
        score = fuzz.WRatio(upper_cleaned, alias_upper)
        if score > best_score:
            best_score = score
            best_canonical = canonical

    if best_score >= MATCH_THRESHOLD and best_canonical is not None:
        logger.info(
            "Fuzzy company match: raw='%s' → canonical='%s' (score=%.1f)",
            raw_name[:60],
            best_canonical,
            best_score,
            extra={"extra_data": {
                "original": raw_name[:60],
                "normalized": best_canonical,
                "match_type": "fuzzy",
                "match_score": best_score,
            }},
        )
        return (best_canonical, True)

    # No match — return cleaned version with regex cleanup logged
    logger.info(
        "Company not matched: raw='%s' → cleaned='%s'",
        raw_name[:60],
        cleaned,
        extra={"extra_data": {
            "original": raw_name[:60],
            "normalized": cleaned,
            "match_type": "regex_cleanup",
        }},
    )
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
        logger.debug(
            "Fuzzy address match: raw='%s' → canonical='%s'",
            raw_address[:60],
            best_addr,
            extra={"extra_data": {"raw": raw_address[:60], "canonical": best_addr, "match_score": best_score}},
        )
        return (best_addr, True)

    return (cleaned, False)
