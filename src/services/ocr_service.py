"""
OCR Service for extracting text from scanned PDF documents.

This service uses Tesseract OCR to extract text from image-based PDF pages
and provides confidence scoring for quality assessment.
"""

from typing import Dict, List, Optional, Tuple
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """
    Service for performing OCR on scanned PDF documents.

    Handles conversion of PDF pages to images and text extraction using Tesseract,
    with confidence scoring to flag low-quality extractions.
    """

    def __init__(self, tesseract_lang: str = 'eng', dpi: int = 300, confidence_threshold: float = 0.85):
        """
        Initialize OCR service with configuration.

        Args:
            tesseract_lang: Language for Tesseract OCR (default: 'eng')
            dpi: DPI for PDF to image conversion (default: 300)
            confidence_threshold: Minimum confidence score (default: 0.85)
        """
        self.tesseract_lang = tesseract_lang
        self.dpi = dpi
        self.confidence_threshold = confidence_threshold
        logger.info(f"OCRService initialized with lang={tesseract_lang}, dpi={dpi}, threshold={confidence_threshold}")

    def get_page_as_image(self, pdf_path: str, page_number: int) -> Optional[Image.Image]:
        """
        Convert a specific PDF page to a PIL Image.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to convert (1-indexed)

        Returns:
            PIL Image object or None if conversion fails

        Raises:
            ValueError: If page_number is invalid
            FileNotFoundError: If PDF file doesn't exist
        """
        try:
            if page_number < 1:
                raise ValueError(f"Page number must be >= 1, got {page_number}")

            logger.debug(f"Converting page {page_number} of {pdf_path} to image at {self.dpi} DPI")

            # Convert specific page to image
            # pdf2image uses 1-based indexing for first_page/last_page
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=page_number,
                last_page=page_number
            )

            if not images:
                logger.warning(f"No image generated for page {page_number} of {pdf_path}")
                return None

            return images[0]

        except Exception as e:
            logger.error(f"Failed to convert page {page_number} to image: {str(e)}")
            raise

    def extract_text_from_page_image(self, image: Image.Image) -> Tuple[str, float]:
        """
        Extract text from a PIL Image using Tesseract OCR.

        Args:
            image: PIL Image object to perform OCR on

        Returns:
            Tuple of (extracted_text, confidence_score)
            - extracted_text: The OCR-extracted text
            - confidence_score: Float between 0 and 1 indicating confidence

        Raises:
            RuntimeError: If Tesseract OCR fails
        """
        try:
            logger.debug("Performing OCR on image")

            # Get detailed OCR data including confidence scores
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_lang,
                output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(
                image,
                lang=self.tesseract_lang
            )

            # Calculate confidence score
            confidence = self.calculate_confidence_score(ocr_data)

            logger.info(f"OCR extracted {len(text)} characters with confidence {confidence:.2f}")

            return text, confidence

        except pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not found. Please install Tesseract OCR.")
            raise RuntimeError("Tesseract OCR is not installed or not in PATH")
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            raise RuntimeError(f"OCR extraction failed: {str(e)}")

    def calculate_confidence_score(self, ocr_data: Dict) -> float:
        """
        Calculate aggregate confidence score from Tesseract OCR data.

        Tesseract provides confidence scores per word. This method computes
        a weighted average, filtering out low-confidence noise.

        Args:
            ocr_data: Dictionary from pytesseract.image_to_data with confidence scores

        Returns:
            Float between 0 and 1 representing overall confidence
        """
        try:
            confidences = ocr_data.get('conf', [])

            # Filter out -1 values (Tesseract uses -1 for non-word elements)
            valid_confidences = [float(c) for c in confidences if c != -1]

            if not valid_confidences:
                logger.warning("No valid confidence scores found in OCR data")
                return 0.0

            # Tesseract confidence is 0-100, normalize to 0-1
            avg_confidence = sum(valid_confidences) / len(valid_confidences)
            normalized_confidence = avg_confidence / 100.0

            logger.debug(f"Calculated confidence: {normalized_confidence:.4f} from {len(valid_confidences)} words")

            return normalized_confidence

        except Exception as e:
            logger.error(f"Failed to calculate confidence score: {str(e)}")
            return 0.0

    def process_pdf_page(self, pdf_path: str, page_number: int) -> Dict:
        """
        Complete OCR processing for a single PDF page.

        Combines page-to-image conversion, text extraction, and confidence scoring.

        Args:
            pdf_path: Path to the PDF file
            page_number: Page number to process (1-indexed)

        Returns:
            Dictionary with keys:
            - text: Extracted text
            - confidence: Confidence score (0-1)
            - page_number: Page number processed
            - requires_review: Boolean flag if confidence is below threshold

        Raises:
            Exception: If processing fails
        """
        try:
            logger.info(f"Processing page {page_number} of {pdf_path}")

            # Convert page to image
            image = self.get_page_as_image(pdf_path, page_number)
            if image is None:
                raise RuntimeError(f"Failed to convert page {page_number} to image")

            # Extract text and confidence
            text, confidence = self.extract_text_from_page_image(image)

            # Determine if manual review is needed
            requires_review = confidence < self.confidence_threshold

            result = {
                'text': text,
                'confidence': confidence,
                'page_number': page_number,
                'requires_review': requires_review
            }

            if requires_review:
                logger.warning(
                    f"Page {page_number} has low confidence ({confidence:.2f} < {self.confidence_threshold})"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to process page {page_number}: {str(e)}")
            raise
