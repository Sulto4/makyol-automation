"""Unit tests for document_classifier module."""

import pytest

from src.document_classifier import classify_document, classify_with_confidence
from src.models import DocumentType


class TestFilenameClassification:
    """Test filename-based classification (Pass 1, confidence 1.0)."""

    @pytest.mark.parametrize(
        "filename, expected",
        [
            ("FT PEHD 100.pdf", DocumentType.FISA_TEHNICA),
            ("FT teava PE100.pdf", DocumentType.FISA_TEHNICA),
            ("fisa tehnica material.pdf", DocumentType.FISA_TEHNICA),
            ("FT fiting PEHD.pdf", DocumentType.FISA_TEHNICA),
            ("data sheet product.pdf", DocumentType.FISA_TEHNICA),
            ("2. ISO 9001.pdf", DocumentType.ISO_9001),
            ("ISO 14001 certificate.pdf", DocumentType.ISO_14001),
            ("ISO 45001.pdf", DocumentType.ISO_45001),
            ("ISO 50001 cert.pdf", DocumentType.ISO_50001),
            ("AVT agreat.pdf", DocumentType.AVIZ_TEHNIC),
            ("aviz tehnic nr 123.pdf", DocumentType.AVIZ_TEHNIC),
            ("AGT 001.pdf", DocumentType.AGREMENT_TEHNIC),
            ("agrement tehnic.pdf", DocumentType.AGREMENT_TEHNIC),
            ("AT 015-123 doc.pdf", DocumentType.AGREMENT_TEHNIC),
            ("Aviz-agrement-tehnic-doc.pdf", DocumentType.AGREMENT_TEHNIC),
            ("AVS 2024.pdf", DocumentType.AVIZ_SANITAR),
            ("aviz sanitar nr.pdf", DocumentType.AVIZ_SANITAR),
            ("DC conformitate.pdf", DocumentType.DECLARATIE_CONFORMITATE),
            ("declaratie de conformitate.pdf", DocumentType.DECLARATIE_CONFORMITATE),
            ("CC calitate.pdf", DocumentType.CERTIFICAT_CONFORMITATE),
            ("certificat de calitate.pdf", DocumentType.CERTIFICAT_CONFORMITATE),
            ("certificat de conformitate.pdf", DocumentType.CERTIFICAT_CONFORMITATE),
            ("CG garantie.pdf", DocumentType.CERTIFICAT_GARANTIE),
            ("certificat de garantie.pdf", DocumentType.CERTIFICAT_GARANTIE),
            ("certificat P1R-123.pdf", DocumentType.CERTIFICAT_CONFORMITATE),
            ("certificat CERT-456.pdf", DocumentType.CERTIFICAT_CONFORMITATE),
        ],
    )
    def test_filename_patterns(self, filename, expected):
        doc_type, confidence = classify_with_confidence(filename, "")
        assert doc_type == expected
        assert confidence == 1.0

    def test_filename_confidence_is_1(self):
        _, confidence = classify_with_confidence("ISO 9001.pdf", "")
        assert confidence == 1.0


class TestContentClassification:
    """Test text content-based classification (Pass 2, confidence 0.7)."""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Aceasta este fisa tehnica a produsului", DocumentType.FISA_TEHNICA),
            ("technical data sheet for PE100", DocumentType.FISA_TEHNICA),
            ("certificat conform ISO 9001", DocumentType.ISO_9001),
            ("certificat ISO 14001", DocumentType.ISO_14001),
            ("ISO 45001 management", DocumentType.ISO_45001),
            ("ISO 50001 energy", DocumentType.ISO_50001),
            ("aviz sanitar produs", DocumentType.AVIZ_SANITAR),
            ("aviz tehnic nr 123", DocumentType.AVIZ_TEHNIC),
            ("agrement tehnic special", DocumentType.AGREMENT_TEHNIC),
            ("declaratie de conformitate", DocumentType.DECLARATIE_CONFORMITATE),
            ("declarație de conformitate", DocumentType.DECLARATIE_CONFORMITATE),
            ("certificat de calitate produs", DocumentType.CERTIFICAT_CONFORMITATE),
            ("certificat de garanție valabil", DocumentType.CERTIFICAT_GARANTIE),
            ("certificat de conformitate nr", DocumentType.CERTIFICAT_CONFORMITATE),
        ],
    )
    def test_text_patterns(self, text, expected):
        doc_type, confidence = classify_with_confidence("unknown.pdf", text)
        assert doc_type == expected
        assert confidence == 0.7


class TestFallbackClassification:
    """Test fallback to OTHER when nothing matches."""

    def test_unknown_filename_no_text(self):
        doc_type, confidence = classify_with_confidence("random_file.pdf", "")
        assert doc_type == DocumentType.OTHER
        assert confidence == 0.3

    def test_unknown_filename_gibberish_text(self):
        doc_type, confidence = classify_with_confidence("doc.pdf", "lorem ipsum dolor sit amet")
        assert doc_type == DocumentType.OTHER
        assert confidence == 0.3

    def test_empty_text(self):
        doc_type = classify_document("unknown.pdf", "")
        assert doc_type == DocumentType.OTHER


class TestEdgeCases:
    """Test edge cases: CC-01740 prefix, DOC001, descriptive VALROM filenames."""

    def test_cc_prefix_matches_certificat(self):
        """CC-01740 style filenames should match CERTIFICAT_CONFORMITATE."""
        doc_type = classify_document("CC-01740 certificat.pdf", "")
        assert doc_type == DocumentType.CERTIFICAT_CONFORMITATE

    def test_doc001_unknown(self):
        """Generic DOC001 filename with no matching text falls to OTHER."""
        doc_type = classify_document("DOC001.pdf", "")
        assert doc_type == DocumentType.OTHER

    def test_doc001_with_text_fallback(self):
        """DOC001 filename but text contains ISO 9001 -> text classification."""
        doc_type, confidence = classify_with_confidence(
            "DOC001.pdf", "Certificat conform ISO 9001 valabil"
        )
        assert doc_type == DocumentType.ISO_9001
        assert confidence == 0.7

    def test_descriptive_valrom_ft(self):
        """Descriptive VALROM filename like 'FT PEHD tevi VALROM.pdf'."""
        doc_type = classify_document("FT PEHD tevi VALROM.pdf", "")
        assert doc_type == DocumentType.FISA_TEHNICA

    def test_classify_document_convenience(self):
        """classify_document returns only DocumentType, not confidence."""
        result = classify_document("ISO 9001.pdf", "")
        assert isinstance(result, DocumentType)
        assert result == DocumentType.ISO_9001

    def test_dc_dash_prefix_not_matched(self):
        """DC- prefix (like DC-Tevi) should NOT match DECLARATIE_CONFORMITATE."""
        # The pattern excludes DC followed by dash: (?:\bDC\b(?!\s*-)|...)
        doc_type = classify_document("DC-Tevi PEHD.pdf", "")
        assert doc_type != DocumentType.DECLARATIE_CONFORMITATE
