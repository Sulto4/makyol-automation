"""Main CLI entry point for document scanner and importer."""

import argparse
import logging
import sys
from pathlib import Path

from src.config.settings import settings
from src.scanner.folder_scanner import FolderScanner
from src.importers.document_importer import DocumentImporter, ImportSummary
from src.models.database import Base, engine


def setup_logging(verbose: bool = False):
    """Configure logging for the application.

    Args:
        verbose: If True, set log level to DEBUG. Otherwise use INFO.
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    """Main entry point for the document scanner and importer CLI."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Scan supplier document folders and import PDFs into database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan default document folder
  python -m src.main

  # Scan custom folder location
  python -m src.main --base-path /path/to/documents

  # Dry run (show what would be imported without writing to database)
  python -m src.main --dry-run

  # Enable verbose logging
  python -m src.main --verbose
        """
    )

    parser.add_argument(
        '--base-path',
        type=str,
        default='Documente',
        help='Base path for document folders (default: Documente/)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Scan and classify documents without importing to database'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG level) logging'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("=== Document Scanner & Importer ===")
    logger.info(f"Base path: {args.base_path}")
    logger.info(f"Dry run: {args.dry_run}")

    # Convert base path to Path object
    base_path = Path(args.base_path)

    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)

    # Initialize database (create tables if they don't exist)
    if not args.dry_run:
        logger.info("Initializing database...")
        Base.metadata.create_all(engine)

    # Initialize components
    scanner = FolderScanner(base_path=base_path)
    summary = ImportSummary()

    if args.dry_run:
        logger.info("DRY RUN MODE - No database changes will be made")
        # In dry run, just scan and classify without importing
        for pdf_file, supplier_name in scanner.scan_all_suppliers():
            summary.add_found(supplier_name)
            logger.info(f"Found: {pdf_file.name} (supplier: {supplier_name})")
    else:
        # Full import mode
        importer = DocumentImporter()

        try:
            # Process each discovered PDF file
            for pdf_file, supplier_name in scanner.scan_all_suppliers():
                summary.add_found(supplier_name)

                try:
                    # Get or create supplier record
                    supplier_folder_path = str(pdf_file.parent)
                    supplier = importer.get_or_create_supplier(
                        name=supplier_name,
                        folder_path=supplier_folder_path
                    )

                    # Import document (includes classification)
                    document, was_imported = importer.import_document(
                        file_path=pdf_file,
                        supplier_id=supplier.id
                    )

                    if was_imported:
                        # Document was newly imported
                        is_classified = document.document_type is not None
                        summary.add_imported(supplier_name, is_classified)
                    else:
                        # Document already exists (duplicate)
                        summary.add_skipped(supplier_name)

                except Exception as e:
                    # Log error but continue processing other files
                    logger.error(
                        f"Error processing {pdf_file.name}: {e}",
                        exc_info=args.verbose
                    )
                    continue

        finally:
            # Clean up importer resources
            importer.close()

    # Print summary report
    logger.info("\n" + "="*50)
    logger.info("\n" + str(summary))
    logger.info("\n" + "="*50)

    # Return appropriate exit code
    if summary.found == 0:
        logger.warning("No documents found to process")
        sys.exit(1)

    logger.info("Processing complete!")
    sys.exit(0)


if __name__ == '__main__':
    main()
