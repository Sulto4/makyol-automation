"""Document classifier for identifying document types from filenames."""

import re
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of document classification.

    Attributes:
        doc_type: Identified document type, or None if unclassifiable
        confidence: Confidence score (0.0-1.0), or 0.0 if unclassifiable
        pattern_matched: Name of the pattern that matched, for debugging
    """
    doc_type: Optional[str]
    confidence: float
    pattern_matched: Optional[str] = None


class DocumentClassifier:
    """Classifier for identifying document types from filename patterns.

    Uses regex patterns to parse filename conventions and extract document types.
    Returns classification confidence based on pattern match quality.

    Confidence levels:
    - High (0.9): Numbered prefix patterns like "2. ISO 9001.pdf"
    - Medium (0.7): Keyword patterns like "Certificat ISO 14001 SRAC 2025_2026.pdf"
    - Low (0.5): Fuzzy matches
    - None (0.0): Unclassifiable
    """

    def __init__(self):
        """Initialize the document classifier with regex patterns."""
        # High-confidence patterns: numbered prefix format
        # Pattern: "2. ISO 9001.pdf" -> "ISO 9001"
        self.numbered_pattern = re.compile(
            r'^\d+\.\s*(.+?)\.pdf$',
            re.IGNORECASE
        )

        # Medium-confidence patterns: keyword matching
        self.keyword_patterns = [
            # ISO certificates
            (re.compile(r'(?:certificat\s+)?ISO\s+9001', re.IGNORECASE), "ISO 9001"),
            (re.compile(r'(?:certificat\s+)?ISO\s+14001', re.IGNORECASE), "ISO 14001"),

            # Other document types
            (re.compile(r'\bAVS\b', re.IGNORECASE), "AVS"),
            (re.compile(r'certificat', re.IGNORECASE), "Certificat"),
            (re.compile(r'fi[șs]a?\s+tehnic[aă]', re.IGNORECASE), "Fisa tehnica"),
        ]

    def classify(self, filename: str) -> ClassificationResult:
        """Classify a document based on its filename.

        Attempts to identify document type using regex patterns with
        decreasing confidence levels:
        1. Numbered patterns (highest confidence)
        2. Keyword patterns (medium confidence)
        3. Unclassifiable (no confidence)

        Args:
            filename: Name of the file to classify (e.g., "2. ISO 9001.pdf")

        Returns:
            ClassificationResult: Classification result with doc_type and confidence
        """
        # Try numbered pattern first (highest confidence)
        match = self.numbered_pattern.match(filename)
        if match:
            doc_type = match.group(1).strip()
            logger.debug(f"Classified '{filename}' as '{doc_type}' (numbered pattern)")
            return ClassificationResult(
                doc_type=doc_type,
                confidence=0.9,
                pattern_matched="numbered_prefix"
            )

        # Try keyword patterns (medium confidence)
        for pattern, doc_type in self.keyword_patterns:
            if pattern.search(filename):
                logger.debug(f"Classified '{filename}' as '{doc_type}' (keyword pattern)")
                return ClassificationResult(
                    doc_type=doc_type,
                    confidence=0.7,
                    pattern_matched=f"keyword_{doc_type.lower().replace(' ', '_')}"
                )

        # Unclassifiable
        logger.debug(f"Could not classify '{filename}' - no pattern matched")
        return ClassificationResult(
            doc_type=None,
            confidence=0.0,
            pattern_matched=None
        )
