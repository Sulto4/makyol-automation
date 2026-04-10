"""Folder scanner for recursive PDF discovery in supplier folders."""

from pathlib import Path
from typing import Iterator, Tuple, Optional
import logging

from src.config.settings import settings

logger = logging.getLogger(__name__)


class FolderScanner:
    """Scanner for discovering PDF files in supplier document folders.

    Uses pathlib.Path.rglob for recursive scanning and yields results
    for memory efficiency on large folder structures.

    Attributes:
        base_path: Base path for document folders (default from settings)
    """

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the folder scanner.

        Args:
            base_path: Optional base path for documents.
                      Defaults to settings.base_document_path if not provided.
        """
        self.base_path = base_path if base_path is not None else settings.base_document_path
        if not isinstance(self.base_path, Path):
            self.base_path = Path(self.base_path)

    def scan_folder(self, folder_path: Path) -> Iterator[Path]:
        """Recursively scan a folder for PDF files.

        Uses Path.rglob('**/*.pdf') for efficient recursive scanning.
        Yields results as a generator for memory efficiency.

        Args:
            folder_path: Path to the folder to scan

        Yields:
            Path: Paths to discovered PDF files
        """
        if not folder_path.exists():
            logger.warning(f"Folder does not exist: {folder_path}")
            return

        if not folder_path.is_dir():
            logger.warning(f"Path is not a directory: {folder_path}")
            return

        # Use rglob for recursive scanning
        # Track seen files to avoid duplicates on case-insensitive filesystems
        seen_files = set()

        for pattern in ["*.pdf", "*.PDF"]:
            for pdf_file in folder_path.rglob(pattern):
                if pdf_file.is_file():
                    # Use resolved path to handle case-insensitive duplicates
                    resolved_path = pdf_file.resolve()
                    if resolved_path not in seen_files:
                        seen_files.add(resolved_path)
                        yield pdf_file

    def scan_all_suppliers(self) -> Iterator[Tuple[Path, Optional[str]]]:
        """Scan all known supplier folders for PDF files.

        Iterates through all supplier folders defined in settings and
        discovers all PDF files, associating each with its supplier.

        Yields:
            Tuple[Path, Optional[str]]: (pdf_file_path, supplier_name)
                supplier_name is None if the supplier folder doesn't exist
        """
        for supplier_name, folder_name in settings.supplier_folders.items():
            supplier_folder = self.base_path / folder_name

            if not supplier_folder.exists():
                logger.warning(
                    f"Supplier folder not found: {supplier_folder} "
                    f"(supplier: {supplier_name})"
                )
                continue

            logger.info(f"Scanning supplier folder: {supplier_name} ({supplier_folder})")

            for pdf_file in self.scan_folder(supplier_folder):
                yield (pdf_file, supplier_name)

    def get_supplier_from_path(self, file_path: str) -> Optional[str]:
        """Determine supplier name from a file path.

        Parses the file path to identify which supplier folder it belongs to
        based on the known supplier folder mappings in settings.

        Args:
            file_path: Path to a file (absolute or relative)

        Returns:
            str: Supplier name if matched, None otherwise
        """
        file_path_obj = Path(file_path)

        # Get the path parts as strings for matching
        path_parts = file_path_obj.parts

        # Check each supplier folder name against the path parts
        for supplier_name, folder_name in settings.supplier_folders.items():
            if folder_name in path_parts:
                return supplier_name

        # No match found
        return None
