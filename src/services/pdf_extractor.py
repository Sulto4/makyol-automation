"""
PDF Extraction Service for processing both text-based and scanned PDF documents.

This service handles text extraction from PDFs using pdfplumber for text-based pages
and integrates with OCR service for scanned pages.
"""

from typing import Optional
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

    def __init__(self, min_text_threshold: int = 10):
        """
        Initialize PDF extractor with configuration.

        Args:
            min_text_threshold: Minimum character count to consider a page as text-based
                              (default: 10). Pages with fewer characters are considered scanned.
        """
        self.min_text_threshold = min_text_threshold
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
