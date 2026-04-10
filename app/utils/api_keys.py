"""
API Key Utilities

Functions for validating API keys against configured keys.
"""

from typing import Optional
from app.config import settings


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate an API key against the configured valid API keys.

    Args:
        api_key: The API key to validate

    Returns:
        bool: True if the API key is valid, False otherwise
    """
    if not api_key:
        return False

    valid_keys = settings.get_api_keys_list()
    return api_key in valid_keys


def is_api_key_configured() -> bool:
    """
    Check if at least one valid API key is configured.

    Returns:
        bool: True if API keys are configured, False otherwise
    """
    valid_keys = settings.get_api_keys_list()
    # Filter out default placeholder keys
    actual_keys = [
        key for key in valid_keys
        if key and key != "your-secure-api-key-here"
    ]
    return len(actual_keys) > 0
