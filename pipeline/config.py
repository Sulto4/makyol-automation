import logging
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


def fetch_settings_from_api(timeout: int = 5, retries: int = 5, retry_delay: float = 2.0) -> Optional[Dict[str, Any]]:
    """
    Fetch settings from the backend API with retries.
    Backend may not be ready at pipeline startup, so retry a few times.

    Args:
        timeout: Request timeout in seconds per attempt
        retries: Number of retry attempts
        retry_delay: Seconds to wait between retries

    Returns:
        Dictionary mapping setting keys to their values, or None if fetch fails
    """
    import time as _time

    for attempt in range(retries + 1):
        try:
            response = requests.get(SETTINGS_API_ENDPOINT, timeout=timeout)
            response.raise_for_status()

            response_data = response.json()

            # Handle backend API response format: {"success": true, "data": [...], "count": N}
            if isinstance(response_data, dict) and "data" in response_data:
                settings_list = response_data["data"]
            else:
                settings_list = response_data

            if not isinstance(settings_list, list):
                return None

            # Convert list of settings objects to key-value dictionary
            settings_dict = {}
            for setting in settings_list:
                if isinstance(setting, dict) and "key" in setting and "value" in setting:
                    settings_dict[setting["key"]] = setting["value"]

            print(f"[config] Settings loaded from API ({len(settings_dict)} keys)")
            return settings_dict
        except (requests.RequestException, ValueError, KeyError) as e:
            if attempt < retries:
                print(f"[config] Settings API unavailable (attempt {attempt+1}/{retries+1}): {e}. Retrying in {retry_delay}s...")
                _time.sleep(retry_delay)
            else:
                print(f"[config] Settings API unavailable after {retries+1} attempts. Using defaults.")
                return None


# Fetch settings from API (with retries — backend may start after pipeline)
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

# Startup config logging
_logger = logging.getLogger(__name__)
_masked_key = OPENROUTER_API_KEY[:8] + "..." + OPENROUTER_API_KEY[-4:] if len(OPENROUTER_API_KEY) > 12 else "***"
_logger.info("AI config loaded: MODEL=%s, API_KEY=%s", AI_MODEL, _masked_key)

# Tesseract Configuration (OS-aware)
# On Linux (Docker), always use system tesseract — ignore Windows DB setting
if platform.system() == "Windows":
    TESSERACT_CMD = _get_setting("tesseract_path", r"D:\Tesseract-OCR\tesseract.exe")
else:
    TESSERACT_CMD = "/usr/bin/tesseract"
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
