"""
Configuration package for the OCR document processing application.

This package contains all application configuration settings,
including OCR parameters, service configurations, and environment-specific settings.
"""

from .settings import (
    OCR_CONFIG,
    OCR_ADVANCED_CONFIG,
    get_ocr_config,
    get_advanced_config,
    validate_config,
)

__all__ = [
    'OCR_CONFIG',
    'OCR_ADVANCED_CONFIG',
    'get_ocr_config',
    'get_advanced_config',
    'validate_config',
]
