"""Comprehensive unit tests for pipeline.classification hybrid classifier."""

from unittest.mock import patch

import pytest

from pipeline.classification import (
    FILENAME_RULES,
    TEXT_MARKERS,
    VALID_CATEGORIES,
    _get_text_score,
    classify_by_filename,
    classify_by_text,
    classify_document,
    validate_classification,
)


# ---------------------------------------------------------------------------
# 1. filename+text_agree: both methods agree
# ---------------------------------------------------------------------------

class TestFilenameTextAgree:
    """When filename and text both match the same category, method=filename+text_agree."""

    @pytest.mark.parametrize(
        "filename, text, expected_cat",
        [
            ("ISO 9001 cert.pdf", "certificat ISO 9001 management system ASRO", "ISO"),
            ("fisa tehnica produs.pdf", "fisa tehnica caracteristici tehnice proprietati fizice", "FISA_TEHNICA"),
            ("aviz sanitar nr 123.pdf", "aviz sanitar ministerul sanatatii apa potabila", "AVIZ_SANITAR"),
        ],
    )
    def test_both_agree(self, filename, text, expected_cat):
        cat, conf, method = classify_document(filename, text)
        assert cat == expected_cat
        assert method == "filename+text_agree"
        assert conf >= 0.98


# ---------------------------------------------------------------------------
# 2. text_override: text score >= 5 and disagrees with filename
# ---------------------------------------------------------------------------

class TestTextOverride:
    """Text overrides filename when text_score >= 5 and category is not ALTELE."""

    def test_text_override_strong_text(self):
        # Filename matches FISA_TEHNICA, but text strongly matches ISO (score>=5)
        filename = "FT PEHD 100.pdf"
        text = "ISO 9001 management system certificate ASRO IQNet CERTIND SR EN 123"
        cat, conf, method = classify_document(filename, text)
        assert cat == "ISO"
        assert method == "text_override"
        assert conf >= 0.90

    def test_text_override_not_altele(self):
        """text_override does NOT trigger for ALTELE text."""
        # Even if text somehow scored high for ALTELE, it shouldn't override
        # ALTELE is not in TEXT_MARKERS so text can't score for it
        filename = "ISO 9001.pdf"
        text = "some random text about aprobare"
        cat, conf, method = classify_document(filename, text)
        # filename should win since text can't strongly match ALTELE
        assert cat == "ISO"


# ---------------------------------------------------------------------------
# 3. filename_wins: disagreement but text score < 5
# ---------------------------------------------------------------------------

class TestFilenameWins:
    """Filename wins when there's disagreement but text score is low."""

    def test_filename_wins_weak_text(self):
        # Filename matches FISA_TEHNICA, text weakly matches ISO (score=3)
        filename = "fisa tehnica produs.pdf"
        text = "ISO 9001 certificat"
        cat, conf, method = classify_document(filename, text)
        assert cat == "FISA_TEHNICA"
        assert method == "filename_wins"
        assert conf >= 0.85


# ---------------------------------------------------------------------------
# 4. FILENAME_RULES pattern coverage (6 representative new patterns)
# ---------------------------------------------------------------------------

class TestFilenameRulesPatterns:
    """Each key FILENAME_RULES pattern classifies correctly."""

    @pytest.mark.parametrize(
        "filename, expected_cat",
        [
            # ISO variants
            ("ISO 9001.pdf", "ISO"),
            ("ISO 14001 cert.pdf", "ISO"),
            ("ISO 45001.pdf", "ISO"),
            ("ISO 50001 certificate.pdf", "ISO"),
            ("ISO 22000.pdf", "ISO"),
            ("ISO 13485 cert.pdf", "ISO"),
            # CE / PED
            ("CE certificat PED.pdf", "CE"),
            ("PED approval.pdf", "CE"),
            # Fisa tehnica
            ("FT PEHD 100.pdf", "FISA_TEHNICA"),
            ("fisa tehnica material.pdf", "FISA_TEHNICA"),
            ("technical data sheet.pdf", "FISA_TEHNICA"),
            # Agrement
            ("AGT 001.pdf", "AGREMENT"),
            ("agrement tehnic nr.pdf", "AGREMENT"),
            ("AT 015-123 doc.pdf", "AGREMENT"),
            # Aviz tehnic
            ("AVT agreat.pdf", "AVIZ_TEHNIC"),
            ("aviz tehnic nr 123.pdf", "AVIZ_TEHNIC"),
            # Aviz sanitar
            ("AVS 2024.pdf", "AVIZ_SANITAR"),
            ("aviz sanitar nr.pdf", "AVIZ_SANITAR"),
            # Declaratie conformitate
            ("DC conformitate.pdf", "DECLARATIE_CONFORMITATE"),
            ("declaratie de conformitate.pdf", "DECLARATIE_CONFORMITATE"),
            # Certificat calitate
            ("CC calitate.pdf", "CERTIFICAT_CALITATE"),
            ("certificat de calitate.pdf", "CERTIFICAT_CALITATE"),
            ("certificat de conformitate.pdf", "CERTIFICAT_CALITATE"),
            # Certificat garantie
            ("CG garantie.pdf", "CERTIFICAT_GARANTIE"),
            ("certificat de garantie.pdf", "CERTIFICAT_GARANTIE"),
            # Autorizatie distributie
            ("autorizatie de distributie.pdf", "AUTORIZATIE_DISTRIBUTIE"),
            # CUI
            ("CUI firma.pdf", "CUI"),
            ("certificat de inregistrare.pdf", "CUI"),
            ("certificat constatator.pdf", "CUI"),
            ("ONRC doc.pdf", "CUI"),
            # Declaratie performanta
            ("declaratie de performanta.pdf", "DECLARATIE_PERFORMANTA"),
            ("DoP produs.pdf", "DECLARATIE_PERFORMANTA"),
            # Combined aviz + agrement
            ("aviz-agrement-tehnic-doc.pdf", "AVIZ_TEHNIC_SI_AGREMENT"),
            # Lab reports -> CERTIFICAT_CALITATE
            ("buletin de analiza.pdf", "CERTIFICAT_CALITATE"),
            ("raport de incercare.pdf", "CERTIFICAT_CALITATE"),
            ("test report.pdf", "CERTIFICAT_CALITATE"),
        ],
    )
    def test_filename_pattern(self, filename, expected_cat):
        result = classify_by_filename(filename)
        assert result is not None, f"No match for filename '{filename}'"
        cat, conf, method = result
        assert cat == expected_cat
        assert conf == 0.95
        assert method == "filename_regex"

    def test_altele_pattern_skipped(self):
        """Filename patterns matching ALTELE are skipped (continue)."""
        result = classify_by_filename("aprobare de tip.pdf")
        assert result is None


# ---------------------------------------------------------------------------
# 5. TEXT_MARKERS weight coverage (representative markers)
# ---------------------------------------------------------------------------

class TestTextMarkersWeights:
    """Each key TEXT_MARKERS entry contributes the correct weight."""

    @pytest.mark.parametrize(
        "text, category, min_score",
        [
            ("ISO 9001", "ISO", 3),
            ("management system certificate", "ISO", 2),
            ("fisa tehnica", "FISA_TEHNICA", 3),
            ("technical data sheet", "FISA_TEHNICA", 3),
            ("caracteristici tehnice", "FISA_TEHNICA", 2),
            ("agrement tehnic", "AGREMENT", 3),
            ("aviz tehnic", "AVIZ_TEHNIC", 3),
            ("aviz sanitar", "AVIZ_SANITAR", 3),
            ("declaratie de conformitate", "DECLARATIE_CONFORMITATE", 3),
            ("certificat de calitate", "CERTIFICAT_CALITATE", 3),
            ("autorizatie de distributie", "AUTORIZATIE_DISTRIBUTIE", 3),
            ("certificat de inregistrare", "CUI", 3),
            ("certificat de garantie", "CERTIFICAT_GARANTIE", 3),
            ("declaratie de performanta", "DECLARATIE_PERFORMANTA", 3),
            ("aviz tehnic agrement", "AVIZ_TEHNIC_SI_AGREMENT", 3),
            ("warranty certificate", "CERTIFICAT_GARANTIE", 3),
            ("declaration of performance", "DECLARATIE_PERFORMANTA", 3),
            # Weight=1 markers
            ("apa potabila", "AVIZ_SANITAR", 1),
            ("garantie 10 ani", "CERTIFICAT_GARANTIE", 1),
            ("punct de lucru", "CUI", 1),
        ],
    )
    def test_text_marker_weight(self, text, category, min_score):
        score = _get_text_score(text, category)
        assert score >= min_score


# ---------------------------------------------------------------------------
# 6. _get_text_score cumulative scoring
# ---------------------------------------------------------------------------

class TestGetTextScore:
    """_get_text_score returns correct cumulative scores."""

    def test_cumulative_iso_score(self):
        text = "ISO 9001 management system certificate ASRO IQNet CERTIND SR EN 123"
        score = _get_text_score(text, "ISO")
        # ISO 9001=3 + management system certificate=2 + ASRO=2 + IQNet=2 + CERTIND=2 + SR EN 123=2
        assert score >= 13

    def test_empty_text_returns_zero(self):
        assert _get_text_score("", "ISO") == 0
        assert _get_text_score("  ", "ISO") == 0

    def test_invalid_category_returns_zero(self):
        assert _get_text_score("ISO 9001", "INVALID_CAT") == 0

    def test_no_match_returns_zero(self):
        assert _get_text_score("lorem ipsum dolor sit amet", "ISO") == 0

    def test_single_marker_score(self):
        score = _get_text_score("aviz sanitar", "AVIZ_SANITAR")
        assert score == 3


# ---------------------------------------------------------------------------
# 7. validate_classification boosts by +0.05 when >= 2 patterns match
# ---------------------------------------------------------------------------

class TestValidateClassificationBoost:
    """validate_classification boosts confidence when >= 2 patterns match."""

    def test_boost_when_two_patterns_match(self):
        text = "ISO 9001 management system"
        result = validate_classification("ISO", 0.90, text)
        assert result == 0.95

    def test_boost_capped_at_099(self):
        text = "ISO 9001 management system certificate ASRO"
        result = validate_classification("ISO", 0.98, text)
        assert result == 0.99

    def test_boost_exact_cap(self):
        text = "certificat de calitate quality certificate"
        result = validate_classification("CERTIFICAT_CALITATE", 0.95, text)
        assert result == 0.99


# ---------------------------------------------------------------------------
# 8. validate_classification unchanged when < 2 patterns match
# ---------------------------------------------------------------------------

class TestValidateClassificationNoBoost:
    """validate_classification unchanged when < 2 patterns match."""

    def test_no_boost_one_pattern(self):
        text = "ISO 9001"
        result = validate_classification("ISO", 0.90, text)
        assert result == 0.90

    def test_no_boost_no_patterns(self):
        result = validate_classification("ISO", 0.90, "random text")
        assert result == 0.90

    def test_no_boost_unknown_category(self):
        result = validate_classification("UNKNOWN", 0.90, "ISO 9001 management system")
        assert result == 0.90

    def test_no_boost_empty_text(self):
        result = validate_classification("ISO", 0.90, "")
        assert result == 0.90


# ---------------------------------------------------------------------------
# 9. text_override does NOT trigger for ALTELE text
# ---------------------------------------------------------------------------

class TestNoAlteleOverride:
    """ALTELE cannot override filename via text_override."""

    def test_altele_not_in_text_markers(self):
        """ALTELE has no TEXT_MARKERS entries, so it can never be a text result."""
        altele_markers = [m for m in TEXT_MARKERS if m[1] == "ALTELE"]
        assert len(altele_markers) == 0

    def test_filename_not_overridden_by_altele(self):
        """When filename matches but text doesn't, filename wins."""
        cat, conf, method = classify_document("ISO 9001.pdf", "some unrelated text")
        assert cat == "ISO"
        assert method == "filename_regex"


# ---------------------------------------------------------------------------
# 10. Empty text with filename match works
# ---------------------------------------------------------------------------

class TestEmptyTextFilenameMatch:
    """Classification works with empty text when filename matches."""

    def test_empty_text(self):
        cat, conf, method = classify_document("ISO 9001.pdf", "")
        assert cat == "ISO"
        assert conf == 0.95
        assert method == "filename_regex"

    def test_whitespace_text(self):
        cat, conf, method = classify_document("fisa tehnica.pdf", "   ")
        assert cat == "FISA_TEHNICA"
        assert conf == 0.95
        assert method == "filename_regex"


# ---------------------------------------------------------------------------
# 11. No match falls through to ALTELE fallback
# ---------------------------------------------------------------------------

class TestAlteleFallback:
    """When nothing matches, falls through to ALTELE."""

    def test_no_match_fallback(self):
        cat, conf, method = classify_document("random_file.pdf", "")
        assert cat == "ALTELE"
        assert conf == 0.3
        assert method == "fallback"

    @patch("pipeline.classification.classify_by_ai", return_value=None)
    def test_gibberish_fallback(self, mock_ai):
        cat, conf, method = classify_document("doc123.pdf", "lorem ipsum dolor sit amet")
        assert cat == "ALTELE"
        assert conf == 0.3
        assert method == "fallback"
