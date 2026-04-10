"""Metadata extraction functions for PDF document processing.

Extracts expiration dates, producer, distributor, and material information
from PDF text content using regex patterns and folder-name fallbacks.

Critical fix from prototype: Tehnoworld and Zakprest folders always populate
the distributor field via SUPPLIER_ROLES, even when not found in text.
"""

import re
from typing import Optional

from src.config import (
    DATE_PATTERNS,
    DISTRIBUTOR_PATTERNS,
    KNOWN_MATERIALS,
    KNOWN_PRODUCERS,
    MATERIAL_PATTERNS,
    MONTH_MAP_RO,
    PRODUCER_PATTERNS,
    SUPPLIER_ROLES,
)
from src.models import DocumentType


def _normalize_date(raw_date: str) -> str:
    """Normalize a date string to DD.MM.YYYY format.

    Handles formats:
      - DD/MM/YYYY or DD.MM.YYYY
      - DD month_name YYYY (Romanian month names)
      - YYYY-MM-DD (ISO format)
    """
    raw_date = raw_date.strip()

    # ISO format: YYYY-MM-DD
    iso_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', raw_date)
    if iso_match:
        return f"{iso_match.group(3)}.{iso_match.group(2)}.{iso_match.group(1)}"

    # DD/MM/YYYY or DD.MM.YYYY
    numeric_match = re.match(r'(\d{1,2})[./](\d{1,2})[./](\d{4})', raw_date)
    if numeric_match:
        day = numeric_match.group(1).zfill(2)
        month = numeric_match.group(2).zfill(2)
        year = numeric_match.group(3)
        return f"{day}.{month}.{year}"

    # DD month_name YYYY (Romanian)
    text_match = re.match(r'(\d{1,2})\s+(\w+)\s+(\d{4})', raw_date)
    if text_match:
        day = text_match.group(1).zfill(2)
        month_name = text_match.group(2).lower()
        year = text_match.group(3)
        month = MONTH_MAP_RO.get(month_name)
        if month:
            return f"{day}.{month}.{year}"

    return raw_date


def _folder_key(folder_name: str) -> Optional[str]:
    """Find the matching key in KNOWN_PRODUCERS/KNOWN_MATERIALS by folder name."""
    upper = folder_name.upper()
    for key in KNOWN_PRODUCERS:
        if key.upper() in upper:
            return key
    return None


def _supplier_role_key(folder_name: str) -> Optional[str]:
    """Find the matching key in SUPPLIER_ROLES by folder name."""
    for key in SUPPLIER_ROLES:
        if key.upper() in folder_name.upper():
            return key
    return None


def extract_expiration_date(text: str) -> str:
    """Extract validity/expiration date from text using DATE_PATTERNS.

    Returns the date normalized to DD.MM.YYYY format, or 'N/A' if not found.
    """
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return _normalize_date(match.group(1))
    return "N/A"


def extract_producer(text: str, folder_name: str) -> str:
    """Extract producer company name from text, with folder-name fallback.

    Searches text using PRODUCER_PATTERNS first, then falls back to
    KNOWN_PRODUCERS lookup by folder name.
    """
    for pattern in PRODUCER_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    # Fallback: check SUPPLIER_ROLES for a producer entry
    role_key = _supplier_role_key(folder_name)
    if role_key and 'producer' in SUPPLIER_ROLES[role_key]:
        return SUPPLIER_ROLES[role_key]['producer']

    # Fallback: KNOWN_PRODUCERS by folder name
    key = _folder_key(folder_name)
    if key:
        return KNOWN_PRODUCERS[key]

    return "N/A"


def extract_distributor(text: str, folder_name: str) -> str:
    """Extract distributor from text, with critical folder-name fallback.

    CRITICAL FIX: For Tehnoworld and Zakprest folders, the distributor is
    always set from SUPPLIER_ROLES even if not found in text. These suppliers
    are distributors, not producers.
    """
    # First try to extract from text
    for pattern in DISTRIBUTOR_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()

    # CRITICAL FIX: For folders that are distributors, always populate
    role_key = _supplier_role_key(folder_name)
    if role_key and 'distributor' in SUPPLIER_ROLES[role_key]:
        return SUPPLIER_ROLES[role_key]['distributor']

    return "N/A"


def extract_material(
    text: str, folder_name: str, doc_type: DocumentType
) -> str:
    """Extract material/product name from text, with folder-name fallback.

    Uses MATERIAL_PATTERNS to search text content first, then falls back
    to KNOWN_MATERIALS by folder name.
    """
    for pattern in MATERIAL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            material = match.group(1).strip()
            # Clean up excessive whitespace
            material = re.sub(r'\s+', ' ', material)
            return material

    # Fallback: KNOWN_MATERIALS by folder name
    key = _folder_key(folder_name)
    if key:
        return KNOWN_MATERIALS[key]

    return "N/A"


def extract_all_metadata(
    text: str, folder_name: str, doc_type: DocumentType
) -> dict:
    """Orchestrate all metadata extraction and return a dict.

    Returns:
        dict with keys: expiration_date, producer, distributor, material
    """
    return {
        "expiration_date": extract_expiration_date(text),
        "producer": extract_producer(text, folder_name),
        "distributor": extract_distributor(text, folder_name),
        "material": extract_material(text, folder_name, doc_type),
    }
