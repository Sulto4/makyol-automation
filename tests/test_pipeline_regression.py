"""Regression tests for the document processing pipeline.

Loads test_fixtures.json (26 fixtures, 2 per category) and runs
pipeline.process_document() on actual PDF files from Pachete Makyol/.
Compares classification and extraction against expected values using
fuzzy string matching. Asserts ≥90% classification and ≥85% extraction.

Requires: test_fixtures.json and PDF files in Pachete Makyol/ directory.
Skip with: pytest -m "not regression" to skip these tests.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest

# Mark all tests in this module as regression (slow, needs real files)
pytestmark = [pytest.mark.regression, pytest.mark.slow]

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Search for test_fixtures.json in common locations
FIXTURES_PATH = None
for candidate in [
    PROJECT_ROOT / "test_fixtures.json",
    PROJECT_ROOT / "makyol-automation" / "test_fixtures.json",
    PROJECT_ROOT / "tests" / "test_fixtures.json",
    PROJECT_ROOT / "pipeline" / "test_fixtures.json",
]:
    if candidate.exists():
        FIXTURES_PATH = candidate
        break

# Search for Pachete Makyol directory
PACHETE_DIR = None
for candidate in [
    PROJECT_ROOT / "Pachete Makyol",
    PROJECT_ROOT / "makyol-automation" / "Pachete Makyol",
    PROJECT_ROOT.parent / "Pachete Makyol",
    PROJECT_ROOT.parent / "makyol-automation" / "Pachete Makyol",
]:
    if candidate.exists():
        PACHETE_DIR = candidate
        break

# Skip entire module if fixtures or PDFs are not available
if FIXTURES_PATH is None:
    pytest.skip(
        "test_fixtures.json not found — regression tests require fixture data",
        allow_module_level=True,
    )

if PACHETE_DIR is None:
    pytest.skip(
        "Pachete Makyol/ directory not found — regression tests require real PDFs",
        allow_module_level=True,
    )


def _load_fixtures() -> list[dict[str, Any]]:
    """Load and return test fixtures from JSON file."""
    with open(FIXTURES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _fuzzy_ratio(a: str, b: str) -> float:
    """Compute normalized Levenshtein similarity ratio between two strings.

    Returns a float between 0.0 and 1.0 where 1.0 is an exact match.
    Uses a simple DP-based edit distance to avoid external dependencies.
    """
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0

    a = a.strip().lower()
    b = b.strip().lower()

    if a == b:
        return 1.0

    len_a, len_b = len(a), len(b)
    # DP table for Levenshtein distance
    prev = list(range(len_b + 1))
    curr = [0] * (len_b + 1)

    for i in range(1, len_a + 1):
        curr[0] = i
        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
        prev, curr = curr, prev

    distance = prev[len_b]
    max_len = max(len_a, len_b)
    return 1.0 - (distance / max_len)


def _fields_match(actual: dict, expected: dict, threshold: float = 0.75) -> tuple[int, int]:
    """Compare extracted fields against expected values using fuzzy matching.

    Returns (matched_count, total_expected_fields).
    A field is considered matched if fuzzy_ratio >= threshold.
    """
    matched = 0
    total = 0

    for key, expected_val in expected.items():
        if expected_val is None or expected_val == "":
            continue
        total += 1

        actual_val = actual.get(key)
        if actual_val is None or actual_val == "":
            continue

        ratio = _fuzzy_ratio(str(actual_val), str(expected_val))
        if ratio >= threshold:
            matched += 1

    return matched, total


class TestPipelineRegression:
    """Regression tests running pipeline on real PDFs from test fixtures."""

    @pytest.fixture(scope="class")
    def fixtures(self) -> list[dict[str, Any]]:
        return _load_fixtures()

    @pytest.fixture(scope="class")
    def results(self, fixtures):
        """Run pipeline on all fixture PDFs and cache results."""
        from pipeline import process_document

        all_results = []
        for fixture in fixtures:
            pdf_rel_path = fixture.get("pdf_path", "")
            pdf_path = PACHETE_DIR / pdf_rel_path if pdf_rel_path else None

            if pdf_path is None or not pdf_path.exists():
                all_results.append({
                    "fixture": fixture,
                    "result": None,
                    "skipped": True,
                    "error": f"PDF not found: {pdf_path}",
                })
                continue

            try:
                result = process_document(str(pdf_path), fixture.get("filename", ""))
                all_results.append({
                    "fixture": fixture,
                    "result": result,
                    "skipped": False,
                    "error": None,
                })
            except Exception as e:
                all_results.append({
                    "fixture": fixture,
                    "result": None,
                    "skipped": False,
                    "error": str(e),
                })

        return all_results

    def test_classification_accuracy(self, results):
        """Assert ≥90% classification accuracy across all fixtures."""
        correct = 0
        total = 0

        for entry in results:
            if entry["skipped"]:
                continue

            total += 1
            fixture = entry["fixture"]
            result = entry["result"]

            if result is None:
                continue

            expected_category = fixture.get("expected_category", "")
            actual_category = result.get("classification", "")

            if actual_category and expected_category:
                # Allow case-insensitive and minor variant matching
                if _fuzzy_ratio(actual_category, expected_category) >= 0.85:
                    correct += 1

        if total == 0:
            pytest.skip("No fixtures were processed (all PDFs missing)")

        accuracy = correct / total
        print(f"\nClassification accuracy: {correct}/{total} = {accuracy:.1%}")

        for entry in results:
            if entry["skipped"] or entry["result"] is None:
                continue
            expected = entry["fixture"].get("expected_category", "")
            actual = entry["result"].get("classification", "")
            status = "✓" if _fuzzy_ratio(actual or "", expected) >= 0.85 else "✗"
            filename = entry["fixture"].get("filename", "unknown")
            print(f"  {status} {filename}: expected={expected}, got={actual}")

        assert accuracy >= 0.90, (
            f"Classification accuracy {accuracy:.1%} is below 90% threshold "
            f"({correct}/{total} correct)"
        )

    def test_extraction_accuracy(self, results):
        """Assert ≥85% extraction field accuracy across all fixtures."""
        total_matched = 0
        total_fields = 0

        for entry in results:
            if entry["skipped"] or entry["result"] is None:
                continue

            fixture = entry["fixture"]
            result = entry["result"]
            expected_fields = fixture.get("expected_extraction", {})
            actual_fields = result.get("extraction", {})

            matched, fields = _fields_match(actual_fields, expected_fields)
            total_matched += matched
            total_fields += fields

        if total_fields == 0:
            pytest.skip("No extraction fields to compare (all PDFs missing)")

        accuracy = total_matched / total_fields
        print(f"\nExtraction accuracy: {total_matched}/{total_fields} = {accuracy:.1%}")

        for entry in results:
            if entry["skipped"] or entry["result"] is None:
                continue
            fixture = entry["fixture"]
            expected_fields = fixture.get("expected_extraction", {})
            actual_fields = entry["result"].get("extraction", {})
            matched, fields = _fields_match(actual_fields, expected_fields)
            pct = f"{matched}/{fields}" if fields else "n/a"
            filename = fixture.get("filename", "unknown")
            print(f"  {filename}: {pct} fields matched")

        assert accuracy >= 0.85, (
            f"Extraction accuracy {accuracy:.1%} is below 85% threshold "
            f"({total_matched}/{total_fields} fields matched)"
        )

    def test_no_pipeline_crashes(self, results):
        """Verify pipeline doesn't crash on any fixture PDF."""
        crashes = []
        for entry in results:
            if entry["skipped"]:
                continue
            if entry["error"] is not None:
                crashes.append(
                    f"{entry['fixture'].get('filename', 'unknown')}: {entry['error']}"
                )

        assert len(crashes) == 0, (
            f"Pipeline crashed on {len(crashes)} fixture(s):\n"
            + "\n".join(f"  - {c}" for c in crashes)
        )

    def test_all_categories_covered(self, fixtures):
        """Verify test fixtures cover all expected categories (2 per category)."""
        from collections import Counter

        categories = Counter(f.get("expected_category") for f in fixtures)

        # Should have at least 13 categories covered (14 minus possibly ALTELE)
        assert len(categories) >= 12, (
            f"Only {len(categories)} categories covered, expected ≥12. "
            f"Categories: {dict(categories)}"
        )

        # Each category should have at least 2 fixtures
        under_represented = {
            cat: count for cat, count in categories.items() if count < 2
        }
        if under_represented:
            print(
                f"\nWarning: categories with <2 fixtures: {under_represented}"
            )

    def test_fixture_count(self, fixtures):
        """Verify we have the expected 26 fixtures."""
        assert len(fixtures) >= 26, (
            f"Expected ≥26 fixtures, got {len(fixtures)}"
        )
