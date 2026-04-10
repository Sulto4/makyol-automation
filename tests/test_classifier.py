"""Tests for document classifier functionality."""

import pytest

from src.importers.document_classifier import DocumentClassifier, ClassificationResult


class TestDocumentClassifier:
    """Test suite for DocumentClassifier class."""

    def test_classifier_initialization(self):
        """Test classifier can be initialized."""
        classifier = DocumentClassifier()
        assert classifier is not None
        assert classifier.numbered_pattern is not None
        assert len(classifier.keyword_patterns) > 0

    def test_classify_numbered_pattern_iso9001(self):
        """Test classification of numbered ISO 9001 pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("2. ISO 9001.pdf")

        assert result.doc_type == "ISO 9001"
        assert result.confidence == 0.9
        assert result.pattern_matched == "numbered_prefix"

    def test_classify_numbered_pattern_avs(self):
        """Test classification of numbered AVS pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("7. AVS.pdf")

        assert result.doc_type == "AVS"
        assert result.confidence == 0.9
        assert result.pattern_matched == "numbered_prefix"

    def test_classify_numbered_pattern_generic(self):
        """Test classification of numbered generic pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("5. Contract de furnizare.pdf")

        assert result.doc_type == "Contract de furnizare"
        assert result.confidence == 0.9
        assert result.pattern_matched == "numbered_prefix"

    def test_classify_keyword_certificat_iso14001(self):
        """Test classification of Certificat ISO 14001 keyword pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("Certificat ISO 14001 SRAC 2025_2026.pdf")

        assert result.doc_type == "Certificat ISO 14001"
        assert result.confidence == 0.7
        assert "keyword" in result.pattern_matched

    def test_classify_keyword_certificat_iso9001(self):
        """Test classification of Certificat ISO 9001 keyword pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("Certificat ISO 9001.pdf")

        assert result.doc_type == "Certificat ISO 9001"
        assert result.confidence == 0.7

    def test_classify_keyword_iso9001(self):
        """Test classification of plain ISO 9001 keyword pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("3. ISO 9001.pdf")

        # Should match numbered pattern first (higher confidence)
        assert result.doc_type == "ISO 9001"
        assert result.confidence == 0.9

    def test_classify_keyword_iso14001(self):
        """Test classification of ISO 14001 keyword pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("ISO 14001 document.pdf")

        assert result.doc_type == "ISO 14001"
        assert result.confidence == 0.7

    def test_classify_keyword_avs(self):
        """Test classification of AVS keyword pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("AVS document 2025.pdf")

        assert result.doc_type == "AVS"
        assert result.confidence == 0.7

    def test_classify_keyword_fisa_tehnica(self):
        """Test classification of Fisa tehnica keyword pattern."""
        classifier = DocumentClassifier()
        result = classifier.classify("10. Fisa tehnica.pdf")

        # Should match numbered pattern first
        assert result.doc_type == "Fisa tehnica"
        assert result.confidence == 0.9

    def test_classify_keyword_fisa_tehnica_romanian(self):
        """Test classification of Fisa tehnica with Romanian diacritics."""
        classifier = DocumentClassifier()
        result = classifier.classify("Fișa tehnică produs.pdf")

        assert result.doc_type == "Fisa tehnica"
        assert result.confidence == 0.7

    def test_classify_unclassifiable(self):
        """Test classification of unclassifiable document."""
        classifier = DocumentClassifier()
        result = classifier.classify("random_document.pdf")

        assert result.doc_type is None
        assert result.confidence == 0.0
        assert result.pattern_matched is None

    def test_classify_case_insensitive(self):
        """Test classification is case-insensitive."""
        classifier = DocumentClassifier()

        result_lower = classifier.classify("iso 9001 document.pdf")
        result_upper = classifier.classify("ISO 9001 DOCUMENT.PDF")
        result_mixed = classifier.classify("Iso 9001 Document.pdf")

        assert result_lower.doc_type == "ISO 9001"
        assert result_upper.doc_type == "ISO 9001"
        assert result_mixed.doc_type == "ISO 9001"

    def test_classify_pattern_priority(self):
        """Test that more specific patterns are matched first."""
        classifier = DocumentClassifier()

        # "Certificat ISO 14001" should match before plain "ISO 14001"
        result = classifier.classify("Certificat ISO 14001 SRAC.pdf")

        assert result.doc_type == "Certificat ISO 14001"
        assert "certificat" in result.doc_type.lower()

    def test_classification_result_dataclass(self):
        """Test ClassificationResult can be created directly."""
        result = ClassificationResult(
            doc_type="Test Type",
            confidence=0.8,
            pattern_matched="test_pattern"
        )

        assert result.doc_type == "Test Type"
        assert result.confidence == 0.8
        assert result.pattern_matched == "test_pattern"
