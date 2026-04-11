#!/usr/bin/env python3
"""
Verification script for aggregate confidence score calculation.

Tests the calculate_aggregate_confidence() method with different scenarios.
"""

import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Import the PDFExtractor
try:
    from src.services.pdf_extractor import PDFExtractor
    logging.info("✓ Successfully imported PDFExtractor")
except ImportError as e:
    logging.error(f"✗ Failed to import PDFExtractor: {e}")
    sys.exit(1)


def test_all_text_pages():
    """Test: All pages are text-based (no OCR) -> confidence = 1.0"""
    print("\n--- Test 1: All text-based pages ---")

    extractor = PDFExtractor()

    # Simulate 5 pages, all text-based (no OCR)
    result = {
        'total_pages': 5,
        'ocr_pages': [],
        'page_confidence_scores': {}
    }

    confidence = extractor.calculate_aggregate_confidence(result)
    expected = 1.0

    print(f"Input: {result}")
    print(f"Expected: {expected}")
    print(f"Actual: {confidence}")

    if abs(confidence - expected) < 0.0001:
        print("✓ PASS")
        return True
    else:
        print(f"✗ FAIL: Expected {expected}, got {confidence}")
        return False


def test_all_ocr_pages():
    """Test: All pages are OCR -> confidence = average of OCR scores"""
    print("\n--- Test 2: All OCR pages ---")

    extractor = PDFExtractor()

    # Simulate 3 pages, all OCR with scores 0.9, 0.8, 0.7
    result = {
        'total_pages': 3,
        'ocr_pages': [1, 2, 3],
        'page_confidence_scores': {1: 0.9, 2: 0.8, 3: 0.7}
    }

    confidence = extractor.calculate_aggregate_confidence(result)
    expected = (0.9 + 0.8 + 0.7) / 3  # 0.8

    print(f"Input: {result}")
    print(f"Expected: {expected}")
    print(f"Actual: {confidence}")

    if abs(confidence - expected) < 0.0001:
        print("✓ PASS")
        return True
    else:
        print(f"✗ FAIL: Expected {expected}, got {confidence}")
        return False


def test_mixed_pages():
    """Test: Mixed document -> weighted average"""
    print("\n--- Test 3: Mixed document (text + OCR) ---")

    extractor = PDFExtractor()

    # Simulate 5 pages: 3 text-based, 2 OCR with scores 0.92 and 0.78
    result = {
        'total_pages': 5,
        'ocr_pages': [2, 4],
        'page_confidence_scores': {2: 0.92, 4: 0.78}
    }

    confidence = extractor.calculate_aggregate_confidence(result)
    # (0.92 + 0.78 + 3*1.0) / 5 = 4.70 / 5 = 0.94
    expected = (0.92 + 0.78 + 3) / 5

    print(f"Input: {result}")
    print(f"Expected: {expected:.4f}")
    print(f"Actual: {confidence:.4f}")

    if abs(confidence - expected) < 0.0001:
        print("✓ PASS")
        return True
    else:
        print(f"✗ FAIL: Expected {expected}, got {confidence}")
        return False


def test_low_quality_ocr():
    """Test: Low quality OCR pages -> low confidence"""
    print("\n--- Test 4: Low quality OCR pages ---")

    extractor = PDFExtractor()

    # Simulate 4 pages: 1 text, 3 OCR with low scores
    result = {
        'total_pages': 4,
        'ocr_pages': [2, 3, 4],
        'page_confidence_scores': {2: 0.65, 3: 0.70, 4: 0.60}
    }

    confidence = extractor.calculate_aggregate_confidence(result)
    # (0.65 + 0.70 + 0.60 + 1*1.0) / 4 = 2.95 / 4 = 0.7375
    expected = (0.65 + 0.70 + 0.60 + 1) / 4

    print(f"Input: {result}")
    print(f"Expected: {expected:.4f}")
    print(f"Actual: {confidence:.4f}")
    print(f"Quality: {'Below threshold (0.85)' if confidence < 0.85 else 'Above threshold'}")

    if abs(confidence - expected) < 0.0001:
        print("✓ PASS")
        return True
    else:
        print(f"✗ FAIL: Expected {expected}, got {confidence}")
        return False


def test_edge_case_zero_pages():
    """Test: Edge case - zero pages"""
    print("\n--- Test 5: Edge case - zero pages ---")

    extractor = PDFExtractor()

    result = {
        'total_pages': 0,
        'ocr_pages': [],
        'page_confidence_scores': {}
    }

    confidence = extractor.calculate_aggregate_confidence(result)
    expected = 0.0

    print(f"Input: {result}")
    print(f"Expected: {expected}")
    print(f"Actual: {confidence}")

    if abs(confidence - expected) < 0.0001:
        print("✓ PASS")
        return True
    else:
        print(f"✗ FAIL: Expected {expected}, got {confidence}")
        return False


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("Aggregate Confidence Score Verification")
    print("=" * 60)

    tests = [
        test_all_text_pages,
        test_all_ocr_pages,
        test_mixed_pages,
        test_low_quality_ocr,
        test_edge_case_zero_pages
    ]

    results = []
    for test_func in tests:
        try:
            results.append(test_func())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    if all(results):
        print("\n✓ All tests passed! Aggregate confidence calculation is working correctly.")
        return 0
    else:
        print("\n✗ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
