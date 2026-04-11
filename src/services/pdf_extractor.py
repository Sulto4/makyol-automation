"""
PDF Extraction Service for processing both text-based and scanned PDF documents.

This service handles text extraction from PDFs using pdfplumber for text-based pages
and integrates with OCR service for scanned pages.
"""

from typing import Optional, Dict, List
import pdfplumber
import logging

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Custom exception for PDF extraction errors."""
    pass


class PDFExtractor:
    """
    Service for extracting text from PDF documents.

    Handles both text-based PDFs (using pdfplumber) and scanned PDFs
    by detecting text-less pages and routing them to OCR processing.
    """

    def __init__(self, min_text_threshold: int = 10, ocr_service=None):
        """
        Initialize PDF extractor with configuration.

        Args:
            min_text_threshold: Minimum character count to consider a page as text-based
                              (default: 10). Pages with fewer characters are considered scanned.
            ocr_service: Optional OCRService instance for processing scanned pages.
                        If None, OCRService will be imported and instantiated when needed.
        """
        self.min_text_threshold = min_text_threshold
        self._ocr_service = ocr_service
        logger.info(f"PDFExtractor initialized with min_text_threshold={min_text_threshold}")

    def is_page_scanned(self, pdf_path: str, page_number: int) -> bool:
        """
        Detect if a PDF page is scanned (has no extractable text layer).

        A page is considered scanned if the extracted text contains fewer characters
        than the minimum threshold, indicating it's an image-based page rather than
        a text-based page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to check (0-indexed for pdfplumber)

        Returns:
            True if the page is scanned (text-less), False if it has extractable text

        Raises:
            PDFExtractionError: If the PDF cannot be opened or page is invalid
            FileNotFoundError: If the PDF file doesn't exist
        """
        try:
            logger.debug(f"Checking if page {page_number} of {pdf_path} is scanned")

            with pdfplumber.open(pdf_path) as pdf:
                # Validate page number
                if page_number < 0 or page_number >= len(pdf.pages):
                    raise PDFExtractionError(
                        f"Invalid page number {page_number}. PDF has {len(pdf.pages)} pages."
                    )

                # Extract text from the page
                page = pdf.pages[page_number]
                text = page.extract_text()

                # Handle None or empty text
                if text is None:
                    text = ""

                # Remove whitespace for accurate character count
                text_cleaned = text.strip()
                char_count = len(text_cleaned)

                # Determine if page is scanned based on character count
                is_scanned = char_count < self.min_text_threshold

                logger.debug(
                    f"Page {page_number}: {char_count} characters extracted, "
                    f"scanned={is_scanned} (threshold={self.min_text_threshold})"
                )

                return is_scanned

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to check if page {page_number} is scanned: {str(e)}")
            raise PDFExtractionError(f"Error checking page {page_number}: {str(e)}")

    def extract_text_from_page(self, pdf_path: str, page_number: int) -> str:
        """
        Extract text from a specific PDF page.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to extract (0-indexed for pdfplumber)

        Returns:
            Extracted text as string (empty string if no text found)

        Raises:
            PDFExtractionError: If extraction fails
            FileNotFoundError: If the PDF file doesn't exist
        """
        try:
            logger.debug(f"Extracting text from page {page_number} of {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                # Validate page number
                if page_number < 0 or page_number >= len(pdf.pages):
                    raise PDFExtractionError(
                        f"Invalid page number {page_number}. PDF has {len(pdf.pages)} pages."
                    )

                # Extract text from the page
                page = pdf.pages[page_number]
                text = page.extract_text()

                # Handle None case
                if text is None:
                    text = ""

                logger.info(f"Extracted {len(text)} characters from page {page_number}")

                return text

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from page {page_number}: {str(e)}")
            raise PDFExtractionError(f"Error extracting text from page {page_number}: {str(e)}")

    def get_page_count(self, pdf_path: str) -> int:
        """
        Get the total number of pages in a PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Total number of pages

        Raises:
            PDFExtractionError: If PDF cannot be opened
            FileNotFoundError: If the PDF file doesn't exist
        """
        try:
            logger.debug(f"Getting page count for {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                page_count = len(pdf.pages)

            logger.info(f"PDF has {page_count} pages")
            return page_count

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to get page count: {str(e)}")
            raise PDFExtractionError(f"Error getting page count: {str(e)}")

    @property
    def ocr_service(self):
        """
        Lazy-load OCR service when needed.

        Returns:
            OCRService instance
        """
        if self._ocr_service is None:
            from .ocr_service import OCRService
            from ..config.settings import OCR_CONFIG

            self._ocr_service = OCRService(
                tesseract_lang=OCR_CONFIG.get('TESSERACT_LANG', 'eng'),
                dpi=OCR_CONFIG.get('OCR_DPI', 300),
                confidence_threshold=OCR_CONFIG.get('OCR_CONFIDENCE_THRESHOLD', 0.85)
            )
            logger.info("OCRService lazy-loaded")

        return self._ocr_service

    def extract_text(self, pdf_path: str) -> Dict:
        """
        Extract text from all pages of a PDF, routing scanned pages to OCR.

        This method intelligently processes each page:
        1. Attempts text extraction with pdfplumber first
        2. If page is scanned (no text), routes to OCR service
        3. Combines results in page order
        4. Tracks OCR usage and confidence scores

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing:
            - full_text: Combined text from all pages
            - ocr_pages: List of page numbers that used OCR (1-indexed)
            - page_confidence_scores: Dict mapping page number to confidence score
            - total_pages: Total number of pages processed

        Raises:
            PDFExtractionError: If extraction fails
            FileNotFoundError: If the PDF file doesn't exist
        """
        try:
            logger.info(f"Starting text extraction for {pdf_path}")

            # Get total page count
            page_count = self.get_page_count(pdf_path)

            # Initialize result tracking
            all_text_parts: List[str] = []
            ocr_pages: List[int] = []
            page_confidence_scores: Dict[int, float] = {}

            # Process each page
            for page_idx in range(page_count):
                page_num_display = page_idx + 1  # 1-indexed for display

                logger.debug(f"Processing page {page_num_display}/{page_count}")

                # Check if page is scanned
                is_scanned = self.is_page_scanned(pdf_path, page_idx)

                if is_scanned:
                    # Route to OCR service
                    logger.info(f"Page {page_num_display} is scanned, routing to OCR")

                    try:
                        # OCRService expects 1-indexed page numbers
                        ocr_result = self.ocr_service.process_pdf_page(pdf_path, page_num_display)

                        # Extract OCR text
                        page_text = ocr_result.get('text', '')
                        confidence = ocr_result.get('confidence', 0.0)

                        # Track OCR usage
                        ocr_pages.append(page_num_display)
                        page_confidence_scores[page_num_display] = confidence

                        logger.info(
                            f"Page {page_num_display} OCR complete: "
                            f"{len(page_text)} chars, confidence={confidence:.2f}"
                        )

                    except Exception as e:
                        logger.error(f"OCR failed for page {page_num_display}: {str(e)}")
                        # Continue with empty text rather than failing entirely
                        page_text = ""
                        ocr_pages.append(page_num_display)
                        page_confidence_scores[page_num_display] = 0.0
                else:
                    # Extract text normally with pdfplumber
                    logger.debug(f"Page {page_num_display} has text layer, using pdfplumber")
                    page_text = self.extract_text_from_page(pdf_path, page_idx)

                # Add page text to results (maintain page order)
                all_text_parts.append(page_text)

            # Combine all text with page breaks
            full_text = "\n\n".join(all_text_parts)

            result = {
                'full_text': full_text,
                'ocr_pages': ocr_pages,
                'page_confidence_scores': page_confidence_scores,
                'total_pages': page_count
            }

            logger.info(
                f"Extraction complete: {page_count} pages processed, "
                f"{len(ocr_pages)} pages used OCR, {len(full_text)} total characters"
            )

            return result

        except FileNotFoundError:
            logger.error(f"PDF file not found: {pdf_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise PDFExtractionError(f"Error extracting text: {str(e)}")

    def get_extraction_metadata(self, extraction_result: Dict) -> Dict:
        """
        Generate metadata dictionary for database storage from extraction results.

        Creates a metadata structure suitable for storing in the database's JSONB
        metadata field, tracking OCR usage and page-level confidence scores.

        Args:
            extraction_result: Dictionary from extract_text() containing:
                - ocr_pages: List of page numbers that used OCR
                - page_confidence_scores: Dict of page number to confidence score
                - total_pages: Total number of pages

        Returns:
            Dictionary containing:
            - is_ocr_processed: Boolean indicating if any page used OCR
            - ocr_pages: List of page numbers (1-indexed) that were OCR processed
            - page_confidence_scores: Dict mapping page number strings to confidence scores
                                     (keys as strings for JSON compatibility)

        Example:
            >>> result = extractor.extract_text('doc.pdf')
            >>> metadata = extractor.get_extraction_metadata(result)
            >>> # metadata = {
            >>>     "is_ocr_processed": True,
            >>>     "ocr_pages": [1, 3, 5],
            >>>     "page_confidence_scores": {"1": 0.92, "3": 0.78, "5": 0.85}
            >>> }
        """
        logger.debug("Generating extraction metadata")

        # Extract data from extraction result
        ocr_pages = extraction_result.get('ocr_pages', [])
        page_confidence_scores = extraction_result.get('page_confidence_scores', {})

        # Determine if OCR was used
        is_ocr_processed = len(ocr_pages) > 0

        # Convert page numbers in confidence scores to strings for JSON compatibility
        # JSONB in PostgreSQL requires string keys for nested objects
        page_confidence_scores_str = {
            str(page_num): score
            for page_num, score in page_confidence_scores.items()
        }

        # Build metadata structure
        metadata = {
            'is_ocr_processed': is_ocr_processed,
            'ocr_pages': ocr_pages,
            'page_confidence_scores': page_confidence_scores_str
        }

        logger.info(
            f"Metadata generated: is_ocr_processed={is_ocr_processed}, "
            f"ocr_pages_count={len(ocr_pages)}"
        )

        return metadata
