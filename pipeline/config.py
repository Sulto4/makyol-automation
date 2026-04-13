import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional
import requests

# Base directory for pipeline package (reliable path resolution)
PIPELINE_DIR = Path(__file__).parent
SCHEMAS_DIR = PIPELINE_DIR / "schemas"

# Backend API configuration
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:3000")
SETTINGS_API_ENDPOINT = f"{BACKEND_API_URL}/api/settings"


def fetch_settings_from_api(timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Fetch settings from the backend API.

    Args:
        timeout: Request timeout in seconds (default: 5)

    Returns:
        Dictionary mapping setting keys to their values, or None if fetch fails
    """
    try:
        response = requests.get(SETTINGS_API_ENDPOINT, timeout=timeout)
        response.raise_for_status()

        settings_list = response.json()
        if not isinstance(settings_list, list):
            return None

        # Convert list of settings objects to key-value dictionary
        settings_dict = {}
        for setting in settings_list:
            if isinstance(setting, dict) and "key" in setting and "value" in setting:
                settings_dict[setting["key"]] = setting["value"]

        return settings_dict
    except (requests.RequestException, ValueError, KeyError):
        # API unavailable or invalid response - will fallback to defaults
        return None


# Fetch settings from API (with fallback to defaults)
_api_settings = fetch_settings_from_api()


def _get_setting(key: str, default: Any) -> Any:
    """
    Get setting value from API response or return default.

    Args:
        key: Setting key to retrieve
        default: Default value if setting not found

    Returns:
        Setting value from API or default value
    """
    if _api_settings is not None and key in _api_settings:
        return _api_settings[key]
    return default


# AI Configuration
OPENROUTER_API_KEY = _get_setting(
    "openrouter_api_key",
    os.environ.get(
        "OPENROUTER_API_KEY",
        "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",
    ),
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = _get_setting("ai_model", "google/gemini-2.0-flash-001")
AI_TEMPERATURE = _get_setting("ai_temperature", 0.0)  # NON-NEGOTIABLE default
AI_MAX_TOKENS = 4096

# Tesseract Configuration (OS-aware)
_default_tesseract = (
    r"D:\Tesseract-OCR\tesseract.exe"
    if platform.system() == "Windows"
    else "/usr/bin/tesseract"
)
TESSERACT_CMD = _get_setting("tesseract_path", _default_tesseract)
OCR_LANGUAGES = "ron+eng"

# Vision fallback threshold
MIN_TEXT_LENGTH = 20  # chars below which vision fallback activates
VISION_MAX_PAGES = _get_setting("vision_max_pages", 3)
VISION_DPI = 300

# Validation limits
MAX_COMPANY_LENGTH = 80
MAX_MATERIAL_LENGTH = 300
MAX_ADDRESS_LENGTH = 250
MAX_RETRIES = 1

# File paths — always use SCHEMAS_DIR for reliable resolution
KNOWLEDGE_BASE_PATH = SCHEMAS_DIR / "knowledge_base.json"
EXTRACTION_SCHEMAS_PATH = SCHEMAS_DIR / "extraction_schemas.json"
