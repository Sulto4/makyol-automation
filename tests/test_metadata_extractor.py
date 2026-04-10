"""Unit tests for metadata_extractor module."""

import pytest

from src.metadata_extractor import (
    extract_all_metadata,
    extract_distributor,
    extract_expiration_date,
    extract_material,
    extract_producer,
    _normalize_date,
)
from src.models import DocumentType


class TestDateExtraction:
    """Test expiration date extraction with various formats."""

    def test_dd_mm_yyyy_dot(self):
        text = "valabilă până la 15.06.2025"
        assert extract_expiration_date(text) == "15.06.2025"

    def test_dd_mm_yyyy_slash(self):
        text = "valabila până la 5/3/2026"
        assert extract_expiration_date(text) == "05.03.2026"

    def test_iso_format(self):
        text = "valid until 2025-12-31"
        assert extract_expiration_date(text) == "31.12.2025"

    def test_romanian_month_name(self):
        text = "valabila până la 15 decembrie 2025"
        assert extract_expiration_date(text) == "15.12.2025"

    def test_romanian_month_ianuarie(self):
        text = "până in 3 ianuarie 2026"
        assert extract_expiration_date(text) == "03.01.2026"

    def test_no_date_found(self):
        assert extract_expiration_date("no date here") == "N/A"

    def test_empty_text(self):
        assert extract_expiration_date("") == "N/A"

    def test_valabil_din_pana_in(self):
        text = "valabil din 01.01.2020 până în 31.12.2025"
        assert extract_expiration_date(text) == "31.12.2025"


class TestNormalizeDate:
    """Test the _normalize_date helper."""

    def test_iso_format(self):
        assert _normalize_date("2025-06-15") == "15.06.2025"

    def test_dot_format(self):
        assert _normalize_date("15.06.2025") == "15.06.2025"

    def test_slash_format(self):
        assert _normalize_date("5/3/2025") == "05.03.2025"

    def test_romanian_month(self):
        assert _normalize_date("15 martie 2025") == "15.03.2025"

    def test_unknown_format_passthrough(self):
        assert _normalize_date("not a date") == "not a date"


class TestProducerExtraction:
    """Test producer extraction from text and folder fallback."""

    def test_from_text_producator(self):
        text = "Producator: TERAPLAST S.A."
        result = extract_producer(text, "unknown")
        assert "TERAPLAST" in result

    def test_from_text_titularul(self):
        text = "Titularul certificatului: VALROM INDUSTRIE SRL"
        result = extract_producer(text, "unknown")
        assert "VALROM" in result

    def test_from_text_fabricant(self):
        text = "Fabricantul: SC TERAPLAST SA"
        result = extract_producer(text, "unknown")
        assert "TERAPLAST" in result

    def test_folder_fallback_teraplast(self):
        result = extract_producer("no match here", "TERAPLAST")
        assert result == "TERAPLAST SA"

    def test_folder_fallback_valrom(self):
        result = extract_producer("no match here", "VALROM")
        assert result == "VALROM INDUSTRIE SRL"

    def test_tehnoworld_no_producer_in_roles(self):
        """Tehnoworld is a distributor; producer fallback goes to KNOWN_PRODUCERS."""
        result = extract_producer("no match", "Tehnoworld")
        assert "TEHNO WORLD" in result

    def test_no_match_returns_na(self):
        result = extract_producer("no match", "UnknownFolder")
        assert result == "N/A"


class TestDistributorExtraction:
    """Test distributor extraction - CRITICAL: Tehnoworld/Zakprest get distributor."""

    def test_from_text_distribuitor(self):
        text = "Distribuitor: MEGA CONSTRUCT SRL"
        result = extract_distributor(text, "unknown")
        assert "MEGA CONSTRUCT" in result

    def test_from_text_furnizor(self):
        text = "Furnizor: SC DISTRIBEX SRL"
        result = extract_distributor(text, "unknown")
        assert "DISTRIBEX" in result

    def test_tehnoworld_always_gets_distributor(self):
        """CRITICAL: Tehnoworld folder must always populate distributor."""
        result = extract_distributor("no distributor in text", "Tehnoworld")
        assert result == "TEHNO WORLD SRL"

    def test_zakprest_always_gets_distributor(self):
        """CRITICAL: Zakprest folder must always populate distributor."""
        result = extract_distributor("no distributor in text", "Zakprest")
        assert result == "SC ZAKPREST CONSTRUCT SRL"

    def test_teraplast_no_distributor(self):
        """Teraplast is a producer, not a distributor -> N/A."""
        result = extract_distributor("no match", "TERAPLAST")
        assert result == "N/A"

    def test_no_match_returns_na(self):
        result = extract_distributor("no match", "UnknownFolder")
        assert result == "N/A"


class TestMaterialExtraction:
    """Test material extraction from text and folder fallback."""

    def test_from_text_tevi_pehd(self):
        text = "Produsul: tevi PEHD PE 100 pentru apa potabila"
        result = extract_material(text, "unknown", DocumentType.FISA_TEHNICA)
        assert "PEHD" in result.upper() or "tevi" in result.lower()

    def test_folder_fallback_teraplast(self):
        result = extract_material("no match", "TERAPLAST", DocumentType.OTHER)
        assert result == "Tevi PEHD PE100 pentru apa"

    def test_folder_fallback_valrom(self):
        result = extract_material("no match", "VALROM", DocumentType.OTHER)
        assert "VALROM" not in result  # Should be the material, not the company
        assert "PEHD" in result

    def test_no_match_returns_na(self):
        result = extract_material("no match", "UnknownFolder", DocumentType.OTHER)
        assert result == "N/A"


class TestExtractAllMetadata:
    """Test the orchestration function."""

    def test_returns_all_keys(self):
        result = extract_all_metadata("some text", "TERAPLAST", DocumentType.FISA_TEHNICA)
        assert "expiration_date" in result
        assert "producer" in result
        assert "distributor" in result
        assert "material" in result

    def test_tehnoworld_integration(self):
        """Integration: Tehnoworld folder produces correct distributor."""
        result = extract_all_metadata("", "Tehnoworld", DocumentType.OTHER)
        assert result["distributor"] == "TEHNO WORLD SRL"
