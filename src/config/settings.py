"""
Application configuration settings for OCR processing.

This module contains all configuration parameters for the OCR service,
including Tesseract settings, image processing parameters, and quality thresholds.
"""

import os


# OCR Configuration
OCR_CONFIG = {
    # Tesseract language for OCR processing
    # Can be overridden with OCR_TESSERACT_LANG environment variable
    # Common values: 'eng', 'fra', 'deu', 'spa', 'ita', 'por'
    # Use '+' for multiple languages: 'eng+fra'
    'TESSERACT_LANG': os.getenv('OCR_TESSERACT_LANG', 'eng'),

    # DPI (dots per inch) for PDF to image conversion
    # Higher DPI = better OCR accuracy but slower processing
    # Can be overridden with OCR_DPI environment variable
    # Recommended: 300 for good balance between quality and speed
    # Range: 150 (fast, lower quality) to 600 (slow, high quality)
    'OCR_DPI': int(os.getenv('OCR_DPI', '300')),

    # Minimum confidence threshold for OCR quality
    # Documents below this threshold are flagged for manual review
    # Can be overridden with OCR_CONFIDENCE_THRESHOLD environment variable
    # Range: 0.0 (accept all) to 1.0 (perfect confidence only)
    # Default 0.85 means 85% confidence minimum
    'OCR_CONFIDENCE_THRESHOLD': float(os.getenv('OCR_CONFIDENCE_THRESHOLD', '0.85')),
}


# Additional OCR settings (for future expansion)
OCR_ADVANCED_CONFIG = {
    # Tesseract Page Segmentation Mode (PSM)
    # 3 = Fully automatic page segmentation (default)
    # 6 = Assume a single uniform block of text
    'PSM_MODE': int(os.getenv('OCR_PSM_MODE', '3')),

    # Tesseract OCR Engine Mode (OEM)
    # 3 = Default, based on what is available (recommended)
    # 1 = Neural nets LSTM engine only
    'OEM_MODE': int(os.getenv('OCR_OEM_MODE', '3')),

    # Maximum image dimensions for processing (to prevent memory issues)
    'MAX_IMAGE_WIDTH': int(os.getenv('OCR_MAX_IMAGE_WIDTH', '4096')),
    'MAX_IMAGE_HEIGHT': int(os.getenv('OCR_MAX_IMAGE_HEIGHT', '4096')),
}


def get_ocr_config() -> dict:
    """
    Get OCR configuration dictionary.

    Returns:
        Dictionary with OCR configuration parameters
    """
    return OCR_CONFIG.copy()


def get_advanced_config() -> dict:
    """
    Get advanced OCR configuration dictionary.

    Returns:
        Dictionary with advanced OCR configuration parameters
    """
    return OCR_ADVANCED_CONFIG.copy()


def validate_config() -> bool:
    """
    Validate OCR configuration values.

    Returns:
        True if configuration is valid, False otherwise

    Raises:
        ValueError: If configuration values are invalid
    """
    # Validate DPI range
    if not 50 <= OCR_CONFIG['OCR_DPI'] <= 1200:
        raise ValueError(f"OCR_DPI must be between 50 and 1200, got {OCR_CONFIG['OCR_DPI']}")

    # Validate confidence threshold range
    if not 0.0 <= OCR_CONFIG['OCR_CONFIDENCE_THRESHOLD'] <= 1.0:
        raise ValueError(
            f"OCR_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0, "
            f"got {OCR_CONFIG['OCR_CONFIDENCE_THRESHOLD']}"
        )

    # Validate Tesseract language is not empty
    if not OCR_CONFIG['TESSERACT_LANG']:
        raise ValueError("TESSERACT_LANG cannot be empty")

    return True


# Validate configuration on import
validate_config()
