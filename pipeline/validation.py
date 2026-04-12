"""Post-extraction schema validation with AI retry.

Checks field constraints and flags suspicious patterns.
On failure, retries extraction once with specific feedback.
Returns (result, review_status).
"""

import re
import logging
from typing import Any, Dict, List, Tuple

from pipeline.config import (
    MAX_COMPANY_LENGTH,
    MAX_MATERIAL_LENGTH,
    MAX_ADDRESS_LENGTH,
    MAX_RETRIES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Date format pattern
# ---------------------------------------------------------------------------

DATE_PATTERN = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")

# Chinese character range
CHINESE_ONLY_PATTERN = re.compile(r'^[\u4e00-\u9fff\s.,;:!?]+$')


# ---------------------------------------------------------------------------
# Individual validators
# ---------------------------------------------------------------------------


def _check_length(value: str, max_len: int, field_name: str) -> List[str]:
    """Check that a string field does not exceed max length."""
    if not value:
        return []
    if len(value) > max_len:
        return [f"{field_name} exceeds {max_len} chars ({len(value)} chars)"]
    return []


def _check_comma_separated_list(value: str, field_name: str) -> List[str]:
    """Flag comma-separated lists in company/producer/distributor fields."""
    if not value:
        return []
    # Flag if there are 2+ commas suggesting a list of entities
    if value.count(",") >= 2:
        return [f"{field_name} appears to be a comma-separated list: '{value[:60]}...'"]
    return []


def _check_material(value: str) -> List[str]:
    """Validate material field: not just 'Produse', not Chinese-only, length check."""
    issues = []
    if not value:
        return []
    issues.extend(_check_length(value, MAX_MATERIAL_LENGTH, "material"))
    # Flag generic placeholder
    if value.strip().lower() in ("produse", "produse diverse", "products"):
        issues.append(f"material is too generic: '{value}'")
    # Flag Chinese-only text
    if re.match(r'^[\u4e00-\u9fff\s.,;:!?]+$', value):
        issues.append(f"material appears to be Chinese-only text: '{value[:40]}'")
    return issues


def _check_date(value: str, field_name: str) -> List[str]:
    """Validate date is in DD.MM.YYYY format."""
    if not value:
        return []
    if not DATE_PATTERN.match(value.strip()):
        return [f"{field_name} is not in DD.MM.YYYY format: '{value}'"]
    return []


def _check_address(value: str, field_name: str) -> List[str]:
    """Validate address: length and no repeated segments."""
    issues = []
    if not value:
        return []
    issues.extend(_check_length(value, MAX_ADDRESS_LENGTH, field_name))
    # Check for repeated segments (same substring 20+ chars appearing twice)
    if len(value) > 40:
        half = len(value) // 2
        for seg_len in range(20, half + 1):
            segment = value[:seg_len]
            if segment in value[seg_len:]:
                issues.append(f"{field_name} contains repeated segments")
                break
    return issues


# ---------------------------------------------------------------------------
# Main validation function
# ---------------------------------------------------------------------------


def validate_extraction(
    result: Dict[str, Any],
    category: str,
    retry_func=None,
    retry_context: Dict[str, Any] = None,
) -> Tuple[Dict[str, Any], str]:
    """Validate extracted data against schema constraints.

    Args:
        result: Extraction result dictionary.
        category: Document category (e.g. 'FISA_TEHNICA').
        retry_func: Optional callable(result, issues, context) for AI retry.
        retry_context: Optional context passed to retry_func.

    Returns:
        Tuple of (validated_result, review_status).
        review_status is 'OK', 'REVIEW', or 'FAILED'.
    """
    issues = _collect_issues(result)

    if not issues:
        return result, "OK"

    logger.warning("Validation issues for %s: %s", category, issues)

    # Attempt retry if retry function provided
    if retry_func and retry_context:
        logger.info("Retrying extraction with feedback for %s", category)
        retried_result = retry_func(result, issues, retry_context)
        if retried_result:
            retry_issues = _collect_issues(retried_result)
            if not retry_issues:
                return retried_result, "OK"
            # Retry didn't fully fix it — use retried result but flag for review
            logger.warning("Retry still has issues: %s", retry_issues)
            return retried_result, "REVIEW"

    # No retry or retry not available — flag for review
    return result, "REVIEW"


def _collect_issues(result: Dict[str, Any]) -> List[str]:
    """Collect all validation issues from a result dict."""
    issues: List[str] = []

    # Company name checks
    for field in ("companie", "producator", "distribuitor"):
        value = result.get(field, "")
        if value:
            issues.extend(_check_length(value, MAX_COMPANY_LENGTH, field))
            issues.extend(_check_comma_separated_list(value, field))

    # Material check
    issues.extend(_check_material(result.get("material", "")))

    # Date checks
    for field in ("data_expirare", "data_emitere"):
        value = result.get(field, "")
        if value:
            issues.extend(_check_date(value, field))

    # Address checks
    for field in ("adresa_producator", "adresa_distribuitor"):
        value = result.get(field, "")
        if value:
            issues.extend(_check_address(value, field))

    return issues
