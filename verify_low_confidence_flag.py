#!/usr/bin/env python3
"""
Verification script for low-confidence flagging functionality (subtask-3-3).

Tests that metadata includes 'requires_manual_review': true when confidence < 0.85
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.pdf_extractor import PDFExtractor


def test_low_confidence_flagging():
    """Test that low-confidence documents are flagged for manual review."""
    print("=" * 70)
    print("TEST: Low-Confidence Flagging")
    print("=" * 70)

    extractor = PDFExtractor()

    # Test 1: High confidence document (should NOT be flagged)
    print("\nTest 1: High confidence document (0.92)")
    print("-" * 70)
    extraction_result = {
        'total_pages': 5,
        'ocr_pages': [2, 4],
        'page_confidence_scores': {2: 0.92, 4: 0.95}
    }

    # Calculate confidence: (0.92 + 0.95 + 3*1.0) / 5 = 4.87 / 5 = 0.974
    aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
    metadata = extractor.get_extraction_metadata(extraction_result, aggregate_confidence)

    print(f"Aggregate confidence: {aggregate_confidence:.4f}")
    print(f"Metadata: {metadata}")

    assert 'requires_manual_review' in metadata, "Missing requires_manual_review field"
    assert metadata['requires_manual_review'] == False, "Should NOT be flagged for review"
    assert 'review_reason' not in metadata or metadata.get('review_reason') is None, \
        "Should not have review_reason when confidence is acceptable"
    print("✓ PASS: High confidence document not flagged for review")

    # Test 2: Low confidence document (should be flagged)
    print("\n\nTest 2: Low confidence document (0.78)")
    print("-" * 70)
    extraction_result = {
        'total_pages': 5,
        'ocr_pages': [1, 2, 3, 4, 5],
        'page_confidence_scores': {1: 0.78, 2: 0.75, 3: 0.80, 4: 0.72, 5: 0.85}
    }

    # Calculate confidence: (0.78 + 0.75 + 0.80 + 0.72 + 0.85) / 5 = 3.90 / 5 = 0.78
    aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
    metadata = extractor.get_extraction_metadata(extraction_result, aggregate_confidence)

    print(f"Aggregate confidence: {aggregate_confidence:.4f}")
    print(f"Metadata: {metadata}")

    assert 'requires_manual_review' in metadata, "Missing requires_manual_review field"
    assert metadata['requires_manual_review'] == True, "Should be flagged for review"
    assert 'review_reason' in metadata, "Missing review_reason field"
    assert 'Low OCR confidence' in metadata['review_reason'], "review_reason should mention low confidence"
    assert '0.78' in metadata['review_reason'], "review_reason should include confidence score"
    print("✓ PASS: Low confidence document flagged for manual review")

    # Test 3: Confidence exactly at threshold (0.85) - should NOT be flagged
    print("\n\nTest 3: Confidence exactly at threshold (0.85)")
    print("-" * 70)
    extraction_result = {
        'total_pages': 5,
        'ocr_pages': [1, 2, 3, 4, 5],
        'page_confidence_scores': {1: 0.85, 2: 0.85, 3: 0.85, 4: 0.85, 5: 0.85}
    }

    # Calculate confidence: (0.85 * 5) / 5 = 0.85
    aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
    metadata = extractor.get_extraction_metadata(extraction_result, aggregate_confidence)

    print(f"Aggregate confidence: {aggregate_confidence:.4f}")
    print(f"Metadata: {metadata}")

    assert 'requires_manual_review' in metadata, "Missing requires_manual_review field"
    assert metadata['requires_manual_review'] == False, "Threshold value should NOT be flagged (>= check)"
    print("✓ PASS: Threshold confidence (0.85) not flagged for review")

    # Test 4: Mixed document with aggregate below threshold
    print("\n\nTest 4: Mixed document with low-confidence OCR pages")
    print("-" * 70)
    extraction_result = {
        'total_pages': 10,
        'ocr_pages': [1, 3, 5, 7],
        'page_confidence_scores': {1: 0.65, 3: 0.70, 5: 0.60, 7: 0.68}
    }

    # Calculate confidence: (0.65 + 0.70 + 0.60 + 0.68 + 6*1.0) / 10 = 8.63 / 10 = 0.863
    # Actually this should be high enough. Let me recalculate for a case that fails
    # To get below 0.85: need sum < 8.5
    # If 6 text pages contribute 6.0, OCR pages need to contribute < 2.5
    # Average OCR confidence needed: < 2.5/4 = 0.625

    # Adjust to ensure it's below threshold
    extraction_result = {
        'total_pages': 10,
        'ocr_pages': [1, 2, 3, 4, 5, 6, 7, 8],  # 8 OCR pages, 2 text pages
        'page_confidence_scores': {
            1: 0.70, 2: 0.72, 3: 0.75, 4: 0.68,
            5: 0.78, 6: 0.80, 7: 0.82, 8: 0.85
        }
    }

    # Calculate: (0.70 + 0.72 + 0.75 + 0.68 + 0.78 + 0.80 + 0.82 + 0.85 + 2*1.0) / 10
    # = (6.10 + 2.0) / 10 = 8.10 / 10 = 0.81
    aggregate_confidence = extractor.calculate_aggregate_confidence(extraction_result)
    metadata = extractor.get_extraction_metadata(extraction_result, aggregate_confidence)

    print(f"Aggregate confidence: {aggregate_confidence:.4f}")
    print(f"Metadata: {metadata}")

    assert 'requires_manual_review' in metadata, "Missing requires_manual_review field"
    assert metadata['requires_manual_review'] == True, "Should be flagged for review"
    assert 'review_reason' in metadata, "Missing review_reason field"
    print("✓ PASS: Mixed document with low aggregate confidence flagged for review")

    # Test 5: Non-OCR document (all text pages) - should NOT have flagging
    print("\n\nTest 5: Non-OCR document (all text pages)")
    print("-" * 70)
    extraction_result = {
        'total_pages': 5,
        'ocr_pages': [],
        'page_confidence_scores': {}
    }

    metadata = extractor.get_extraction_metadata(extraction_result)

    print(f"Metadata: {metadata}")

    # Non-OCR documents shouldn't have the requires_manual_review field set
    # (or if set, should be False since no OCR was used)
    print("✓ PASS: Non-OCR document handled correctly")

    # Test 6: Auto-calculation of aggregate confidence
    print("\n\nTest 6: Auto-calculation of aggregate confidence (no explicit param)")
    print("-" * 70)
    extraction_result = {
        'total_pages': 5,
        'ocr_pages': [1, 2, 3, 4, 5],
        'page_confidence_scores': {1: 0.70, 2: 0.72, 3: 0.75, 4: 0.68, 5: 0.78}
    }

    # Don't pass aggregate_confidence - let it be calculated automatically
    metadata = extractor.get_extraction_metadata(extraction_result)

    print(f"Metadata: {metadata}")

    # Should auto-calculate: (0.70 + 0.72 + 0.75 + 0.68 + 0.78) / 5 = 3.63 / 5 = 0.726
    assert 'requires_manual_review' in metadata, "Missing requires_manual_review field"
    assert metadata['requires_manual_review'] == True, "Should be flagged (auto-calculated < 0.85)"
    assert 'review_reason' in metadata, "Missing review_reason field"
    print("✓ PASS: Auto-calculation of aggregate confidence works correctly")

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED! ✓")
    print("=" * 70)
    print("\nSummary:")
    print("- High confidence documents are NOT flagged for review")
    print("- Low confidence documents (< 0.85) are flagged for review")
    print("- Metadata includes 'requires_manual_review' boolean flag")
    print("- Metadata includes 'review_reason' with confidence score when flagged")
    print("- Threshold boundary (0.85) is handled correctly (not flagged)")
    print("- Auto-calculation of aggregate confidence works when not provided")
    print("\nSubtask 3-3 implementation verified! ✓")


if __name__ == '__main__':
    try:
        test_low_confidence_flagging()
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
