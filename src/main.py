"""CLI entry point and pipeline orchestrator for PDF processing automation.

Scans supplier folders under the input directory, extracts text from each PDF,
classifies document types, extracts metadata, and generates a formatted Word
output document summarising all construction material documentation.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from src.document_classifier import classify_with_confidence
from src.metadata_extractor import extract_all_metadata
from src.models import DocumentInfo, ProcessingResult, SupplierFolder
from src.pdf_extractor import extract_pdf_text, is_scanned_pdf
from src.word_generator import generate_word_output

logger = logging.getLogger(__name__)

# File extensions to skip when scanning for PDFs
SKIP_EXTENSIONS = {'.docx', '.doc', '.xlsx', '.xls', '.jpg', '.png', '.db', '.tmp'}
SKIP_FILENAMES = {'Thumbs.db', 'desktop.ini', '.DS_Store'}


def _setup_logging(verbose: bool) -> None:
    """Configure root logger with appropriate level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S',
    )


def scan_input_folders(input_dir: Path) -> list[SupplierFolder]:
    """Recursively scan input directory for supplier subfolders and their PDFs.

    Skips hidden/dot folders, non-PDF files (Thumbs.db, .docx, etc.),
    and returns a list of SupplierFolder objects with their PDF documents.

    Args:
        input_dir: Path to the root input directory (e.g. Documente/).

    Returns:
        List of SupplierFolder objects, each containing discovered PDF paths.
    """
    if not input_dir.exists():
        logger.error("Input directory does not exist: %s", input_dir)
        return []

    supplier_folders: list[SupplierFolder] = []

    for item in sorted(input_dir.iterdir()):
        # Skip non-directories, hidden/dot folders, and regular files
        if not item.is_dir():
            continue
        if item.name.startswith('.'):
            logger.debug("Skipping hidden folder: %s", item.name)
            continue

        folder = SupplierFolder(
            folder_path=str(item),
            folder_name=item.name,
        )

        # Collect PDF files in this supplier folder
        for pdf_file in sorted(item.rglob('*')):
            if not pdf_file.is_file():
                continue
            if pdf_file.name.startswith('.'):
                continue
            if pdf_file.name in SKIP_FILENAMES:
                logger.debug("Skipping known non-PDF: %s", pdf_file.name)
                continue
            if pdf_file.suffix.lower() in SKIP_EXTENSIONS:
                logger.debug("Skipping non-PDF file: %s", pdf_file.name)
                continue
            if pdf_file.suffix.lower() != '.pdf':
                logger.debug("Skipping non-PDF file: %s", pdf_file.name)
                continue

            doc = DocumentInfo(
                file_path=str(pdf_file),
                file_name=pdf_file.name,
                supplier_folder=item.name,
            )
            folder.documents.append(doc)

        if folder.documents:
            logger.info(
                "Found supplier folder: %s (%d PDFs)",
                item.name,
                len(folder.documents),
            )
            supplier_folders.append(folder)
        else:
            logger.debug("No PDFs found in folder: %s", item.name)

    return supplier_folders


def process_documents(
    input_dir: Path,
    output_path: Path,
    verbose: bool = False,
) -> ProcessingResult:
    """Main pipeline: scan -> extract -> classify -> metadata -> Word output.

    Args:
        input_dir: Path to the root input directory containing supplier folders.
        output_path: Path for the generated Word document.
        verbose: Whether to enable verbose/debug logging.

    Returns:
        ProcessingResult with counts and error details.
    """
    result = ProcessingResult()

    # Step 1: Scan input folders
    logger.info("Scanning input directory: %s", input_dir)
    supplier_folders = scan_input_folders(input_dir)

    if not supplier_folders:
        logger.warning("No supplier folders with PDFs found in %s", input_dir)
        return result

    result.supplier_folders = supplier_folders
    all_documents: list[DocumentInfo] = []
    ocr_count = 0

    # Step 2: Process each PDF
    for folder in supplier_folders:
        for doc in folder.documents:
            result.total_files += 1
            pdf_path = Path(doc.file_path)

            try:
                # Extract text
                logger.debug("Extracting text from: %s", doc.file_name)
                text = extract_pdf_text(pdf_path)
                doc.extracted_text = text

                if is_scanned_pdf(pdf_path):
                    ocr_count += 1

                # Classify document type
                doc_type, confidence = classify_with_confidence(
                    doc.file_name, text
                )
                doc.document_type = doc_type
                doc.confidence = confidence
                logger.debug(
                    "Classified %s as %s (confidence: %.1f)",
                    doc.file_name,
                    doc_type.value,
                    confidence,
                )

                # Extract metadata
                metadata = extract_all_metadata(
                    text, doc.supplier_folder, doc_type
                )
                doc.material = metadata.get('material', 'N/A')
                doc.expiration_date = metadata.get('expiration_date', 'N/A')
                doc.producer = metadata.get('producer', 'N/A')
                doc.distributor = metadata.get('distributor', 'N/A')

                result.processed_files += 1
                all_documents.append(doc)

            except Exception as exc:
                error_msg = f"Error processing {doc.file_name}: {exc}"
                logger.error(error_msg)
                doc.errors.append(str(exc))
                result.errors.append(error_msg)
                result.failed_files += 1
                # Still include the document with partial data
                all_documents.append(doc)

    # Step 3: Generate Word output
    logger.info("Generating Word document: %s", output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        generate_word_output(all_documents, output_path)
        logger.info("Word document generated successfully.")
    except Exception as exc:
        error_msg = f"Error generating Word output: {exc}"
        logger.error(error_msg)
        result.errors.append(error_msg)

    # Print summary
    _print_summary(result, ocr_count)

    return result


def _print_summary(result: ProcessingResult, ocr_count: int) -> None:
    """Print a human-readable summary of processing results."""
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"  Total PDFs found:        {result.total_files}")
    print(f"  Successfully processed:  {result.processed_files}")
    print(f"  Scanned PDFs (OCR used): {ocr_count}")
    print(f"  Failed:                  {result.failed_files}")
    print(f"  Success rate:            {result.success_rate:.1f}%")
    print("-" * 60)

    for folder in result.supplier_folders:
        print(f"  {folder.folder_name}: {len(folder.documents)} documents")

    if result.errors:
        print("-" * 60)
        print("ERRORS:")
        for error in result.errors:
            print(f"  - {error}")

    print("=" * 60)


def _export_json(result: ProcessingResult, json_path: Path) -> None:
    """Export extracted data as JSON for debugging or downstream use."""
    data = {
        'total_files': result.total_files,
        'processed_files': result.processed_files,
        'failed_files': result.failed_files,
        'success_rate': result.success_rate,
        'suppliers': [],
    }

    for folder in result.supplier_folders:
        supplier_data = {
            'folder_name': folder.folder_name,
            'documents': [],
        }
        for doc in folder.documents:
            supplier_data['documents'].append({
                'file_name': doc.file_name,
                'document_type': doc.document_type.value if doc.document_type else None,
                'material': doc.material,
                'expiration_date': doc.expiration_date,
                'producer': doc.producer,
                'distributor': doc.distributor,
                'confidence': doc.confidence,
                'errors': doc.errors,
            })
        data['suppliers'].append(supplier_data)

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("JSON export saved to: %s", json_path)


def main() -> None:
    """Parse CLI arguments and run the processing pipeline."""
    parser = argparse.ArgumentParser(
        description=(
            'PDF Processing Automation for Construction Material Documentation. '
            'Scans supplier folders, extracts metadata from PDFs, and generates '
            'a formatted Word document summary.'
        ),
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        default=Path('Documente/'),
        help='Input directory containing supplier subfolders (default: Documente/)',
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=Path('output/rezultat.docx'),
        help='Output Word document path (default: output/rezultat.docx)',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose/debug logging output',
    )
    parser.add_argument(
        '--json', '-j',
        type=Path,
        default=None,
        metavar='JSON_PATH',
        help='Export extracted data as JSON to the specified path',
    )

    args = parser.parse_args()

    _setup_logging(args.verbose)

    logger.info("Starting PDF processing pipeline...")
    logger.info("Input directory: %s", args.input)
    logger.info("Output file: %s", args.output)

    result = process_documents(
        input_dir=args.input,
        output_path=args.output,
        verbose=args.verbose,
    )

    if args.json:
        _export_json(result, args.json)

    if result.failed_files > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
