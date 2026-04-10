"""Tests for document importer functionality."""

import pytest
from pathlib import Path

from src.importers.document_importer import DocumentImporter, ImportSummary
from src.importers.document_classifier import ClassificationResult
from src.models.document import Document
from src.models.supplier import Supplier


class TestImportSummary:
    """Test suite for ImportSummary class."""

    def test_import_summary_initialization(self):
        """Test ImportSummary can be initialized with zero counters."""
        summary = ImportSummary()

        assert summary.found == 0
        assert summary.imported == 0
        assert summary.skipped == 0
        assert summary.classified == 0
        assert summary.unclassified == 0
        assert len(summary.by_supplier) == 0

    def test_import_summary_add_found(self):
        """Test adding found documents to summary."""
        summary = ImportSummary()

        summary.add_found()
        summary.add_found("TestSupplier")

        assert summary.found == 2
        assert summary.by_supplier["TestSupplier"]["found"] == 1

    def test_import_summary_add_imported_classified(self):
        """Test adding classified imported documents to summary."""
        summary = ImportSummary()

        summary.add_imported(supplier_name="TestSupplier", is_classified=True)

        assert summary.imported == 1
        assert summary.classified == 1
        assert summary.unclassified == 0
        assert summary.by_supplier["TestSupplier"]["imported"] == 1
        assert summary.by_supplier["TestSupplier"]["classified"] == 1

    def test_import_summary_add_imported_unclassified(self):
        """Test adding unclassified imported documents to summary."""
        summary = ImportSummary()

        summary.add_imported(supplier_name="TestSupplier", is_classified=False)

        assert summary.imported == 1
        assert summary.classified == 0
        assert summary.unclassified == 1
        assert summary.by_supplier["TestSupplier"]["unclassified"] == 1

    def test_import_summary_add_skipped(self):
        """Test adding skipped documents to summary."""
        summary = ImportSummary()

        summary.add_skipped("TestSupplier")

        assert summary.skipped == 1
        assert summary.by_supplier["TestSupplier"]["skipped"] == 1

    def test_import_summary_multiple_suppliers(self):
        """Test summary with multiple suppliers."""
        summary = ImportSummary()

        summary.add_found("Supplier1")
        summary.add_found("Supplier2")
        summary.add_imported("Supplier1", is_classified=True)
        summary.add_skipped("Supplier2")

        assert summary.found == 2
        assert summary.imported == 1
        assert summary.skipped == 1
        assert len(summary.by_supplier) == 2
        assert summary.by_supplier["Supplier1"]["found"] == 1
        assert summary.by_supplier["Supplier2"]["skipped"] == 1

    def test_import_summary_str_output(self):
        """Test formatted string output of summary."""
        summary = ImportSummary()
        summary.found = 10
        summary.imported = 8
        summary.skipped = 2
        summary.classified = 7
        summary.unclassified = 1

        output = str(summary)

        assert "Import Summary:" in output
        assert "Total Found: 10" in output
        assert "Imported: 8" in output
        assert "Skipped (duplicates): 2" in output
        assert "Classified: 7" in output
        assert "Unclassified: 1" in output


class TestDocumentImporter:
    """Test suite for DocumentImporter class."""

    def test_importer_initialization(self):
        """Test importer can be initialized."""
        importer = DocumentImporter()

        assert importer is not None
        assert importer.classifier is not None

    def test_importer_initialization_with_session(self, db_session):
        """Test importer can be initialized with custom session."""
        importer = DocumentImporter(db_session=db_session)

        assert importer.db_session == db_session
        assert importer._owns_session is False

    def test_calculate_file_hash(self, test_fixtures_path):
        """Test SHA256 hash calculation for a file."""
        importer = DocumentImporter()
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        file_hash = importer.calculate_file_hash(pdf_file)

        assert file_hash is not None
        assert len(file_hash) == 64  # SHA256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in file_hash)

    def test_calculate_file_hash_missing_file(self):
        """Test hash calculation raises error for missing file."""
        importer = DocumentImporter()
        missing_file = Path("nonexistent.pdf")

        with pytest.raises(FileNotFoundError):
            importer.calculate_file_hash(missing_file)

    def test_calculate_file_hash_consistency(self, test_fixtures_path):
        """Test hash calculation is consistent for same file."""
        importer = DocumentImporter()
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        hash1 = importer.calculate_file_hash(pdf_file)
        hash2 = importer.calculate_file_hash(pdf_file)

        assert hash1 == hash2

    def test_document_exists_false(self, db_session):
        """Test document_exists returns False for new hash."""
        importer = DocumentImporter(db_session=db_session)

        exists = importer.document_exists("nonexistenthash123", db_session)

        assert exists is False

    def test_document_exists_true(self, db_session, test_supplier, test_fixtures_path):
        """Test document_exists returns True for existing hash."""
        importer = DocumentImporter(db_session=db_session)
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        # Import document first
        document, was_imported = importer.import_document(pdf_file, test_supplier.id)
        assert was_imported

        # Check if it exists
        exists = importer.document_exists(document.file_hash, db_session)

        assert exists is True

    def test_get_or_create_supplier_new(self, db_session):
        """Test creating a new supplier."""
        importer = DocumentImporter(db_session=db_session)

        supplier = importer.get_or_create_supplier("NewSupplier", "Documente/NewSupplier")

        assert supplier is not None
        assert supplier.id is not None
        assert supplier.name == "NewSupplier"
        assert supplier.folder_path == "Documente/NewSupplier"

    def test_get_or_create_supplier_existing(self, db_session, test_supplier):
        """Test getting an existing supplier."""
        importer = DocumentImporter(db_session=db_session)

        supplier = importer.get_or_create_supplier(test_supplier.name, test_supplier.folder_path)

        assert supplier.id == test_supplier.id
        assert supplier.name == test_supplier.name

    def test_import_document_success(self, db_session, test_supplier, test_fixtures_path):
        """Test successful document import."""
        importer = DocumentImporter(db_session=db_session)
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        document, was_imported = importer.import_document(pdf_file, test_supplier.id)

        assert was_imported is True
        assert document is not None
        assert document.id is not None
        assert document.supplier_id == test_supplier.id
        assert document.filename == "2. ISO 9001.pdf"
        assert document.document_type == "ISO 9001"
        assert document.classification_confidence == 0.9
        assert document.needs_review is False
        assert len(document.file_hash) == 64

    def test_import_document_duplicate(self, db_session, test_supplier, test_fixtures_path):
        """Test importing duplicate document is skipped."""
        importer = DocumentImporter(db_session=db_session)
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        # Import first time
        doc1, was_imported1 = importer.import_document(pdf_file, test_supplier.id)
        assert was_imported1 is True

        # Import second time (should skip)
        doc2, was_imported2 = importer.import_document(pdf_file, test_supplier.id)

        assert was_imported2 is False
        assert doc2 is None

        # Verify only one document in database
        count = db_session.query(Document).count()
        assert count == 1

    def test_import_document_with_classification(self, db_session, test_supplier, test_fixtures_path):
        """Test importing document with pre-computed classification."""
        importer = DocumentImporter(db_session=db_session)
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        classification = ClassificationResult(
            doc_type="Custom Type",
            confidence=0.8,
            pattern_matched="custom"
        )

        document, was_imported = importer.import_document(
            pdf_file,
            test_supplier.id,
            classification=classification
        )

        assert was_imported is True
        assert document.document_type == "Custom Type"
        assert document.classification_confidence == 0.8

    def test_import_document_unclassified_needs_review(self, db_session, test_supplier, test_fixtures_path):
        """Test unclassified document is flagged for review."""
        importer = DocumentImporter(db_session=db_session)
        pdf_file = test_fixtures_path / "Documente Zakprest" / "random_document.pdf"

        document, was_imported = importer.import_document(pdf_file, test_supplier.id)

        assert was_imported is True
        assert document.document_type is None
        assert document.classification_confidence == 0.0
        assert document.needs_review is True

    def test_import_document_low_confidence_needs_review(self, db_session, test_supplier, test_fixtures_path):
        """Test low confidence document is flagged for review."""
        importer = DocumentImporter(db_session=db_session)
        pdf_file = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"

        classification = ClassificationResult(
            doc_type="Low Confidence Type",
            confidence=0.3,
            pattern_matched="low"
        )

        document, was_imported = importer.import_document(
            pdf_file,
            test_supplier.id,
            classification=classification
        )

        assert was_imported is True
        assert document.needs_review is True

    def test_context_manager(self, db_session):
        """Test importer can be used as context manager."""
        with DocumentImporter(db_session=db_session) as importer:
            assert importer is not None

    def test_import_document_missing_file(self, db_session, test_supplier):
        """Test importing missing file raises error."""
        importer = DocumentImporter(db_session=db_session)
        missing_file = Path("nonexistent.pdf")

        with pytest.raises(FileNotFoundError):
            importer.import_document(missing_file, test_supplier.id)

    def test_multiple_documents_different_suppliers(self, db_session, test_fixtures_path):
        """Test importing multiple documents from different suppliers."""
        importer = DocumentImporter(db_session=db_session)

        # Create suppliers
        supplier1 = importer.get_or_create_supplier("Zakprest", "Documente Zakprest")
        supplier2 = importer.get_or_create_supplier("TERAPLAST", "PEHD Apa - TERAPLAST")

        # Import documents - use different files to avoid hash collision
        pdf1 = test_fixtures_path / "Documente Zakprest" / "2. ISO 9001.pdf"
        pdf2 = test_fixtures_path / "PEHD Apa - TERAPLAST" / "Certificat ISO 14001 SRAC 2025_2026.pdf"

        doc1, imported1 = importer.import_document(pdf1, supplier1.id)
        doc2, imported2 = importer.import_document(pdf2, supplier2.id)

        assert imported1 is True
        assert imported2 is True
        assert doc1.supplier_id == supplier1.id
        assert doc2.supplier_id == supplier2.id

        # Verify both in database
        count = db_session.query(Document).count()
        assert count == 2
