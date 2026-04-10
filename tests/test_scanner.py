"""Tests for folder scanner functionality."""

import pytest
from pathlib import Path

from src.scanner.folder_scanner import FolderScanner


class TestFolderScanner:
    """Test suite for FolderScanner class."""

    def test_scanner_initialization(self, test_fixtures_path):
        """Test scanner can be initialized with custom base path."""
        scanner = FolderScanner(base_path=test_fixtures_path)
        assert scanner.base_path == test_fixtures_path
        assert isinstance(scanner.base_path, Path)

    def test_scanner_initialization_default(self):
        """Test scanner can be initialized with default settings."""
        scanner = FolderScanner()
        assert scanner.base_path is not None
        assert isinstance(scanner.base_path, Path)

    def test_scan_folder_finds_pdfs(self, test_fixtures_path):
        """Test scanning a folder finds PDF files."""
        scanner = FolderScanner(base_path=test_fixtures_path)
        zakprest_folder = test_fixtures_path / "Documente Zakprest"

        pdfs = list(scanner.scan_folder(zakprest_folder))

        # Should find at least 2 PDFs in the Zakprest folder
        assert len(pdfs) >= 2
        assert all(pdf.suffix.lower() == '.pdf' for pdf in pdfs)
        assert all(pdf.exists() for pdf in pdfs)

    def test_scan_folder_missing_folder(self, test_fixtures_path):
        """Test scanning non-existent folder returns empty list."""
        scanner = FolderScanner(base_path=test_fixtures_path)
        missing_folder = test_fixtures_path / "NonExistentFolder"

        pdfs = list(scanner.scan_folder(missing_folder))

        assert len(pdfs) == 0

    def test_scan_folder_not_a_directory(self, test_fixtures_path):
        """Test scanning a file instead of directory returns empty list."""
        scanner = FolderScanner(base_path=test_fixtures_path)
        # Use one of the PDFs as the "folder" to scan
        zakprest_folder = test_fixtures_path / "Documente Zakprest"
        pdf_file = next(scanner.scan_folder(zakprest_folder))

        pdfs = list(scanner.scan_folder(pdf_file))

        assert len(pdfs) == 0

    def test_scan_all_suppliers(self, test_fixtures_path, test_settings):
        """Test scanning all supplier folders."""
        scanner = FolderScanner(base_path=test_fixtures_path)

        results = list(scanner.scan_all_suppliers())

        # Should find PDFs from all 4 suppliers
        assert len(results) > 0

        # Each result should be a tuple of (path, supplier_name)
        for pdf_path, supplier_name in results:
            assert isinstance(pdf_path, Path)
            assert pdf_path.suffix.lower() == '.pdf'
            assert supplier_name in ["Zakprest", "TERAPLAST", "VALROM", "Tehnoworld"]

    def test_get_supplier_from_path_zakprest(self):
        """Test supplier identification from Zakprest path."""
        scanner = FolderScanner()
        supplier = scanner.get_supplier_from_path("Documente/Documente Zakprest/test.pdf")

        assert supplier == "Zakprest"

    def test_get_supplier_from_path_teraplast(self):
        """Test supplier identification from TERAPLAST path."""
        scanner = FolderScanner()
        supplier = scanner.get_supplier_from_path("Documente/PEHD Apa - TERAPLAST/test.pdf")

        assert supplier == "TERAPLAST"

    def test_get_supplier_from_path_valrom(self):
        """Test supplier identification from VALROM path."""
        scanner = FolderScanner()
        supplier = scanner.get_supplier_from_path("Documente/PEHD Apa - VALROM/test.pdf")

        assert supplier == "VALROM"

    def test_get_supplier_from_path_tehnoworld(self):
        """Test supplier identification from Tehnoworld path."""
        scanner = FolderScanner()
        supplier = scanner.get_supplier_from_path("Documente/Teava apa PEHD - Tehnoworld/test.pdf")

        assert supplier == "Tehnoworld"

    def test_get_supplier_from_path_unknown(self):
        """Test supplier identification from unknown path returns None."""
        scanner = FolderScanner()
        supplier = scanner.get_supplier_from_path("Unknown/Folder/test.pdf")

        assert supplier is None

    def test_scan_folder_no_duplicates(self, test_fixtures_path):
        """Test scanning doesn't return duplicate files on case-insensitive filesystems."""
        scanner = FolderScanner(base_path=test_fixtures_path)
        zakprest_folder = test_fixtures_path / "Documente Zakprest"

        pdfs = list(scanner.scan_folder(zakprest_folder))
        pdf_paths = [str(pdf.resolve()) for pdf in pdfs]

        # Check no duplicates by comparing resolved paths
        assert len(pdf_paths) == len(set(pdf_paths))
