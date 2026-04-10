"""Document importer with SHA256 hashing for deduplication."""

import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.models.database import SessionLocal, Base, engine
from src.models.document import Document
from src.models.supplier import Supplier
from src.importers.document_classifier import DocumentClassifier, ClassificationResult

logger = logging.getLogger(__name__)


class ImportSummary:
    """Track import statistics for document importer.

    Tracks overall counts and per-supplier breakdown for documents
    found, imported, skipped, classified, and unclassified.

    Attributes:
        found: Total documents found
        imported: Total documents successfully imported
        skipped: Total documents skipped (duplicates)
        classified: Total documents with successful classification
        unclassified: Total documents without classification
        by_supplier: Per-supplier breakdown dictionary
    """

    def __init__(self):
        """Initialize import summary counters."""
        # Overall counters
        self.found = 0
        self.imported = 0
        self.skipped = 0
        self.classified = 0
        self.unclassified = 0

        # Per-supplier breakdown: {supplier_name: {found: X, imported: Y, ...}}
        self.by_supplier: Dict[str, Dict[str, int]] = {}

    def add_found(self, supplier_name: Optional[str] = None):
        """Increment found counter.

        Args:
            supplier_name: Optional supplier name for per-supplier tracking
        """
        self.found += 1
        if supplier_name:
            self._ensure_supplier(supplier_name)
            self.by_supplier[supplier_name]['found'] += 1

    def add_imported(self, supplier_name: Optional[str] = None, is_classified: bool = True):
        """Increment imported counter and classification counters.

        Args:
            supplier_name: Optional supplier name for per-supplier tracking
            is_classified: Whether the document was successfully classified
        """
        self.imported += 1
        if is_classified:
            self.classified += 1
        else:
            self.unclassified += 1

        if supplier_name:
            self._ensure_supplier(supplier_name)
            self.by_supplier[supplier_name]['imported'] += 1
            if is_classified:
                self.by_supplier[supplier_name]['classified'] += 1
            else:
                self.by_supplier[supplier_name]['unclassified'] += 1

    def add_skipped(self, supplier_name: Optional[str] = None):
        """Increment skipped counter.

        Args:
            supplier_name: Optional supplier name for per-supplier tracking
        """
        self.skipped += 1
        if supplier_name:
            self._ensure_supplier(supplier_name)
            self.by_supplier[supplier_name]['skipped'] += 1

    def _ensure_supplier(self, supplier_name: str):
        """Ensure supplier entry exists in breakdown dictionary.

        Args:
            supplier_name: Supplier name to ensure exists
        """
        if supplier_name not in self.by_supplier:
            self.by_supplier[supplier_name] = {
                'found': 0,
                'imported': 0,
                'skipped': 0,
                'classified': 0,
                'unclassified': 0
            }

    def __str__(self) -> str:
        """Return formatted summary report.

        Returns:
            str: Multi-line formatted summary with overall and per-supplier stats
        """
        lines = [
            "Import Summary:",
            f"  Total Found: {self.found}",
            f"  Imported: {self.imported}",
            f"  Skipped (duplicates): {self.skipped}",
            f"  Classified: {self.classified}",
            f"  Unclassified: {self.unclassified}"
        ]

        if self.by_supplier:
            lines.append("\nPer Supplier:")
            for supplier, stats in sorted(self.by_supplier.items()):
                lines.append(f"  {supplier}:")
                lines.append(f"    Found: {stats['found']}")
                lines.append(f"    Imported: {stats['imported']}")
                lines.append(f"    Skipped: {stats['skipped']}")
                lines.append(f"    Classified: {stats['classified']}")
                lines.append(f"    Unclassified: {stats['unclassified']}")

        return '\n'.join(lines)


class DocumentImporter:
    """Importer for adding documents to the database with deduplication.

    Uses SHA256 file hashing to prevent duplicate imports. Integrates with
    DocumentClassifier for automatic document type detection.

    Attributes:
        classifier: DocumentClassifier instance for document type detection
        db_session: Optional database session (creates new if not provided)
    """

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize the document importer.

        Args:
            db_session: Optional SQLAlchemy session. If not provided,
                       creates a new session for each operation.
        """
        self.classifier = DocumentClassifier()
        self.db_session = db_session
        self._owns_session = db_session is None

        # Initialize database tables
        Base.metadata.create_all(engine)

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content.

        Reads file in chunks for memory efficiency on large files.

        Args:
            file_path: Path to the file to hash

        Returns:
            str: Hexadecimal SHA256 hash of file content

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file cannot be read
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256_hash = hashlib.sha256()

        # Read file in 8KB chunks for memory efficiency
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    def document_exists(self, file_hash: str, session: Session) -> bool:
        """Check if a document with the given hash already exists.

        Args:
            file_hash: SHA256 hash to check
            session: Database session

        Returns:
            bool: True if document exists, False otherwise
        """
        existing = session.query(Document).filter(
            Document.file_hash == file_hash
        ).first()

        return existing is not None

    def get_or_create_supplier(
        self,
        name: str,
        folder_path: str
    ) -> Supplier:
        """Get existing supplier or create new one if it doesn't exist.

        Uses supplier name for lookup. If supplier exists, returns it.
        If not, creates a new supplier with the given name and folder_path.

        Args:
            name: Supplier name (e.g., 'Zakprest')
            folder_path: Relative folder path for supplier documents
                        (e.g., 'Documente/Documente Zakprest')

        Returns:
            Supplier: Existing or newly created supplier object

        Raises:
            IntegrityError: If folder_path conflicts with existing supplier
        """
        session = self.db_session if self.db_session else SessionLocal()

        try:
            # Check if supplier already exists by name
            existing = session.query(Supplier).filter(
                Supplier.name == name
            ).first()

            if existing:
                logger.debug(f"Supplier '{name}' already exists (id: {existing.id})")
                return existing

            # Create new supplier
            supplier = Supplier(
                name=name,
                folder_path=folder_path
            )

            session.add(supplier)
            session.commit()
            session.refresh(supplier)

            logger.info(f"Created new supplier: {name} (folder: {folder_path})")

            return supplier

        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error creating supplier '{name}': {e}")
            raise

        except Exception as e:
            session.rollback()
            logger.error(f"Error creating supplier '{name}': {e}")
            raise

        finally:
            # Only close session if we created it
            if self._owns_session and not self.db_session:
                session.close()

    def import_document(
        self,
        file_path: Path,
        supplier_id: int,
        classification: Optional[ClassificationResult] = None
    ) -> Tuple[Optional[Document], bool]:
        """Import a document into the database.

        Calculates file hash, checks for duplicates, classifies if needed,
        and creates database record. Uses transactions for atomicity.

        Args:
            file_path: Path to the document file
            supplier_id: ID of the supplier this document belongs to
            classification: Optional pre-computed classification result.
                          If not provided, will classify automatically.

        Returns:
            Tuple[Optional[Document], bool]: (Document object or None, was_imported)
                - Document object if imported successfully
                - None if duplicate or error
                - was_imported is True if new document, False if duplicate

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If supplier_id is invalid
        """
        session = self.db_session if self.db_session else SessionLocal()

        try:
            # Calculate file hash for deduplication
            file_hash = self.calculate_file_hash(file_path)

            # Check if document already exists
            if self.document_exists(file_hash, session):
                logger.info(f"Document already exists (hash: {file_hash[:8]}...): {file_path.name}")
                return None, False

            # Classify document if not already classified
            if classification is None:
                classification = self.classifier.classify(file_path.name)

            # Determine if document needs manual review
            # Review needed if: unclassified OR low confidence
            needs_review = (
                classification.doc_type is None or
                classification.confidence < 0.5
            )

            # Create document record
            document = Document(
                supplier_id=supplier_id,
                file_path=str(file_path),
                filename=file_path.name,
                document_type=classification.doc_type,
                classification_confidence=classification.confidence,
                file_hash=file_hash,
                needs_review=needs_review
            )

            session.add(document)
            session.commit()
            session.refresh(document)

            logger.info(
                f"Imported document: {file_path.name} "
                f"(type: {classification.doc_type or 'unclassified'}, "
                f"confidence: {classification.confidence:.2f}, "
                f"needs_review: {needs_review})"
            )

            return document, True

        except IntegrityError as e:
            session.rollback()
            logger.warning(f"Integrity error importing {file_path.name}: {e}")
            return None, False

        except Exception as e:
            session.rollback()
            logger.error(f"Error importing document {file_path.name}: {e}")
            raise

        finally:
            # Only close session if we created it
            if self._owns_session and not self.db_session:
                session.close()

    def close(self):
        """Close the database session if owned by this importer."""
        if self._owns_session and self.db_session:
            self.db_session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.close()
