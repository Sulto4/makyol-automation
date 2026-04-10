"""Two-pass document classification for construction material PDFs.

Pass 1: Match filename against FILENAME_PATTERNS (confidence 1.0).
Pass 2: Match extracted text against TEXT_PATTERNS (confidence 0.7).
Fallback: DocumentType.OTHER (confidence 0.3).
"""

import re

from src.config import FILENAME_PATTERNS, TEXT_PATTERNS
from src.models import DocumentType


def classify_with_confidence(
    filename: str, text: str
) -> tuple[DocumentType, float]:
    """Classify a document by filename then text content.

    Args:
        filename: The PDF filename (e.g. '2. ISO 9001.pdf').
        text: Extracted text content from the PDF.

    Returns:
        Tuple of (DocumentType, confidence) where confidence is
        1.0 for filename match, 0.7 for text match, 0.3 for OTHER.
    """
    # --- Pass 1: filename-based classification ---
    # Special case: filenames containing both AGT/agrement and DC indicators
    # should prefer AGREMENT_TEHNIC based on document purpose.
    for pattern, doc_type in FILENAME_PATTERNS:
        if re.search(pattern, filename):
            # Handle ambiguous filenames like 'Aviz-agrement-tehnic-...-DC-Tevi...'
            # If AGREMENT_TEHNIC matched, it takes priority even if DC is present.
            if doc_type == DocumentType.OTHER:
                continue  # Skip OTHER from filename pass, fall through to text
            return doc_type, 1.0

    # --- Pass 2: text content-based classification ---
    if text and text.strip():
        for pattern, doc_type in TEXT_PATTERNS:
            if re.search(pattern, text):
                if doc_type == DocumentType.OTHER:
                    continue
                return doc_type, 0.7

    # --- Fallback ---
    return DocumentType.OTHER, 0.3


def classify_document(filename: str, text: str) -> DocumentType:
    """Classify a document, returning only the DocumentType.

    Convenience wrapper around classify_with_confidence.

    Args:
        filename: The PDF filename.
        text: Extracted text content from the PDF.

    Returns:
        The classified DocumentType.
    """
    doc_type, _ = classify_with_confidence(filename, text)
    return doc_type
