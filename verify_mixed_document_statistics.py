"""
Verification script for subtask-4-2: Track mixed document statistics in metadata

This script demonstrates that get_extraction_metadata() correctly tracks:
- text_pages_count: Number of pages processed with text extraction
- ocr_pages_count: Number of pages processed with OCR
- total_pages: Total number of pages in the document
- document_type: Categorization as "text", "scanned", or "mixed"

Manual verification for subtask-4-2 acceptance criteria.
"""

from src.services.pdf_extractor import PDFExtractor

def test_mixed_document_statistics():
    """Test that metadata includes mixed document statistics."""

    print("=" * 80)
    print("SUBTASK 4-2 VERIFICATION: Track Mixed Document Statistics in Metadata")
    print("=" * 80)
    print()

    extractor = PDFExtractor()

    # Test 1: Text-only document (all pages have text layer)
    print("Test 1: Text-only document (5 pages, all text-based)")
    print("-" * 80)

    extraction_result_text_only = {
        'full_text': 'Combined text from 5 text-based pages...',
        'ocr_pages': [],  # No OCR pages
        'page_confidence_scores': {},
        'total_pages': 5
    }

    metadata = extractor.get_extraction_metadata(extraction_result_text_only)

    print(f"  text_pages_count: {metadata.get('text_pages_count')}")
    print(f"  ocr_pages_count: {metadata.get('ocr_pages_count')}")
    print(f"  total_pages: {metadata.get('total_pages')}")
    print(f"  document_type: {metadata.get('document_type')}")

    assert metadata['text_pages_count'] == 5, "Text pages count should be 5"
    assert metadata['ocr_pages_count'] == 0, "OCR pages count should be 0"
    assert metadata['total_pages'] == 5, "Total pages should be 5"
    assert metadata['document_type'] == 'text', "Document type should be 'text'"
    print("  ✓ Text-only document statistics correct")
    print()

    # Test 2: Scanned-only document (all pages are OCR)
    print("Test 2: Scanned-only document (5 pages, all scanned)")
    print("-" * 80)

    extraction_result_scanned_only = {
        'full_text': 'OCR text from 5 scanned pages...',
        'ocr_pages': [1, 2, 3, 4, 5],  # All pages are OCR
        'page_confidence_scores': {1: 0.95, 2: 0.88, 3: 0.92, 4: 0.90, 5: 0.87},
        'total_pages': 5
    }

    metadata = extractor.get_extraction_metadata(extraction_result_scanned_only)

    print(f"  text_pages_count: {metadata.get('text_pages_count')}")
    print(f"  ocr_pages_count: {metadata.get('ocr_pages_count')}")
    print(f"  total_pages: {metadata.get('total_pages')}")
    print(f"  document_type: {metadata.get('document_type')}")

    assert metadata['text_pages_count'] == 0, "Text pages count should be 0"
    assert metadata['ocr_pages_count'] == 5, "OCR pages count should be 5"
    assert metadata['total_pages'] == 5, "Total pages should be 5"
    assert metadata['document_type'] == 'scanned', "Document type should be 'scanned'"
    print("  ✓ Scanned-only document statistics correct")
    print()

    # Test 3: Mixed document (some text pages, some scanned pages)
    print("Test 3: Mixed document (5 pages: 3 text-based, 2 scanned)")
    print("-" * 80)

    extraction_result_mixed = {
        'full_text': 'Combined text from mixed pages...',
        'ocr_pages': [2, 4],  # Pages 2 and 4 are scanned
        'page_confidence_scores': {2: 0.92, 4: 0.78},
        'total_pages': 5
    }

    metadata = extractor.get_extraction_metadata(extraction_result_mixed)

    print(f"  text_pages_count: {metadata.get('text_pages_count')}")
    print(f"  ocr_pages_count: {metadata.get('ocr_pages_count')}")
    print(f"  total_pages: {metadata.get('total_pages')}")
    print(f"  document_type: {metadata.get('document_type')}")

    assert metadata['text_pages_count'] == 3, "Text pages count should be 3"
    assert metadata['ocr_pages_count'] == 2, "OCR pages count should be 2"
    assert metadata['total_pages'] == 5, "Total pages should be 5"
    assert metadata['document_type'] == 'mixed', "Document type should be 'mixed'"
    print("  ✓ Mixed document statistics correct")
    print()

    # Test 4: Verify complete metadata structure
    print("Test 4: Verify complete metadata structure")
    print("-" * 80)

    metadata_keys = set(metadata.keys())
    required_keys = {
        'is_ocr_processed',
        'ocr_pages',
        'page_confidence_scores',
        'text_pages_count',
        'ocr_pages_count',
        'total_pages',
        'document_type',
        'requires_manual_review'
    }

    print(f"  Required keys: {sorted(required_keys)}")
    print(f"  Actual keys: {sorted(metadata_keys)}")

    assert required_keys.issubset(metadata_keys), f"Missing keys: {required_keys - metadata_keys}"
    print("  ✓ All required keys present in metadata")
    print()

    # Test 5: Edge case - single page document
    print("Test 5: Edge case - single page text document")
    print("-" * 80)

    extraction_result_single = {
        'full_text': 'Single page text',
        'ocr_pages': [],
        'page_confidence_scores': {},
        'total_pages': 1
    }

    metadata = extractor.get_extraction_metadata(extraction_result_single)

    print(f"  text_pages_count: {metadata.get('text_pages_count')}")
    print(f"  ocr_pages_count: {metadata.get('ocr_pages_count')}")
    print(f"  total_pages: {metadata.get('total_pages')}")
    print(f"  document_type: {metadata.get('document_type')}")

    assert metadata['text_pages_count'] == 1, "Text pages count should be 1"
    assert metadata['ocr_pages_count'] == 0, "OCR pages count should be 0"
    assert metadata['total_pages'] == 1, "Total pages should be 1"
    assert metadata['document_type'] == 'text', "Document type should be 'text'"
    print("  ✓ Single page document statistics correct")
    print()

    # Test 6: Verify JSON serialization compatibility
    print("Test 6: Verify JSON serialization compatibility")
    print("-" * 80)

    import json

    try:
        json_str = json.dumps(metadata, indent=2)
        print("  Metadata JSON:")
        print("  " + "\n  ".join(json_str.split("\n")))

        # Verify deserialization
        deserialized = json.loads(json_str)
        assert deserialized['text_pages_count'] == metadata['text_pages_count']
        assert deserialized['ocr_pages_count'] == metadata['ocr_pages_count']
        assert deserialized['total_pages'] == metadata['total_pages']
        assert deserialized['document_type'] == metadata['document_type']

        print("  ✓ Metadata is JSON-serializable and compatible with JSONB")
    except Exception as e:
        print(f"  ✗ JSON serialization failed: {e}")
        raise
    print()

    # Summary
    print("=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    print("✓ text_pages_count correctly calculated (total_pages - ocr_pages_count)")
    print("✓ ocr_pages_count correctly calculated (length of ocr_pages list)")
    print("✓ total_pages correctly extracted from extraction_result")
    print("✓ document_type correctly categorized:")
    print("  - 'text' when ocr_pages_count == 0")
    print("  - 'scanned' when text_pages_count == 0")
    print("  - 'mixed' when both types present")
    print("✓ All fields are JSON-serializable for JSONB storage")
    print("✓ Integration with existing metadata fields (is_ocr_processed, confidence, etc.)")
    print()
    print("ACCEPTANCE CRITERIA MET:")
    print("✓ Metadata includes: text_pages_count, ocr_pages_count, total_pages")
    print("✓ Document type classification added for better categorization")
    print("✓ Statistics accurately reflect page composition")
    print()
    print("All tests passed! Subtask 4-2 is complete.")
    print()

if __name__ == '__main__':
    test_mixed_document_statistics()
