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
_api_settings: Optional[Dict[str, Any]] = fetch_settings_from_api()


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


# ---------------------------------------------------------------------------
# Derived constants — values callers actually consume.
#
# These are module-level globals so existing `from pipeline.config import X`
# imports keep working, BUT the *authoritative* values for reload-able
# settings live in the _PipelineSettings singleton below. Consumers that
# need hot-reload semantics (model, temperature, api key, vision pages,
# tesseract path) should read `settings.<attr>` at request time rather
# than capturing the module-level name at import time. See reload_settings()
# for the update path.
# ---------------------------------------------------------------------------

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MAX_TOKENS = 4096
OCR_LANGUAGES = "ron+eng"
VISION_DPI = 300
MIN_TEXT_LENGTH = 20  # chars below which vision fallback activates

# Validation limits — not reloadable (compiled into prompts / validators).
MAX_COMPANY_LENGTH = 80
MAX_MATERIAL_LENGTH = 300
MAX_ADDRESS_LENGTH = 250
MAX_RETRIES = 1

# File paths
KNOWLEDGE_BASE_PATH = SCHEMAS_DIR / "knowledge_base.json"
EXTRACTION_SCHEMAS_PATH = SCHEMAS_DIR / "extraction_schemas.json"


class _PipelineSettings:
    """Mutable container for settings that should hot-reload on UI save.

    Consumers should import the singleton `settings` and read attributes
    at request time (e.g. `settings.ai_model`, `settings.openrouter_api_key`)
    so that a call to `reload_settings()` propagates immediately without
    needing to restart the container.

    The attributes here intentionally mirror the names of the legacy
    module-level constants so consumers can flip to the new form with a
    one-line import change.
    """

    # Populated by _apply_from_api_cache. Declared for type-checker clarity.
    openrouter_api_key: str
    ai_model: str
    ai_temperature: float
    tesseract_cmd: str
    vision_max_pages: int

    def __init__(self) -> None:
        self._apply_from_api_cache()

    def _apply_from_api_cache(self) -> None:
        """Re-derive settings from the current _api_settings dict."""
        self.openrouter_api_key = _get_setting(
            "openrouter_api_key",
            os.environ.get(
                "OPENROUTER_API_KEY",
                "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",
            ),
        )
        self.ai_model = _get_setting("ai_model", "google/gemini-2.5-flash")
        self.ai_temperature = _get_setting("ai_temperature", 0.0)
        self.vision_max_pages = _get_setting("vision_max_pages", 3)

        # Tesseract is OS-aware. Linux containers always use the system
        # binary; the DB setting is a Windows-only override.
        if platform.system() == "Windows":
            self.tesseract_cmd = _get_setting(
                "tesseract_path", r"D:\Tesseract-OCR\tesseract.exe"
            )
        else:
            self.tesseract_cmd = "/usr/bin/tesseract"


settings = _PipelineSettings()


# ---------------------------------------------------------------------------
# Legacy constant aliases.
#
# Kept so older consumers that did `from pipeline.config import AI_MODEL`
# still compile. These are captured at import time and are NOT updated
# by reload_settings() — that's the whole reason we have the singleton.
# New code and anything on the hot path should use settings.* instead.
# ---------------------------------------------------------------------------

OPENROUTER_API_KEY = settings.openrouter_api_key
AI_MODEL = settings.ai_model
AI_TEMPERATURE = settings.ai_temperature
VISION_MAX_PAGES = settings.vision_max_pages
TESSERACT_CMD = settings.tesseract_cmd

_logger = logging.getLogger(__name__)
_masked_key = (
    settings.openrouter_api_key[:8] + "..." + settings.openrouter_api_key[-4:]
    if len(settings.openrouter_api_key) > 12
    else "***"
)
_logger.info("AI config loaded: MODEL=%s, API_KEY=%s", settings.ai_model, _masked_key)


def reload_settings() -> Dict[str, Any]:
    """Re-fetch settings from the backend and update the `settings` singleton.

    Invoked by the /api/pipeline/reload-settings HTTP endpoint which the
    backend calls fire-and-forget after every settings upsert. Returns a
    summary dict so callers can log what changed.
    """
    global _api_settings
    previous = {
        "ai_model": settings.ai_model,
        "ai_temperature": settings.ai_temperature,
        "vision_max_pages": settings.vision_max_pages,
        # Key is masked in logs; we intentionally don't include the full value.
        "openrouter_api_key_tail": settings.openrouter_api_key[-4:]
        if settings.openrouter_api_key
        else "",
        "tesseract_cmd": settings.tesseract_cmd,
    }
    _api_settings = fetch_settings_from_api()
    settings._apply_from_api_cache()

    # pytesseract caches its binary path at module load time in
    # text_extraction.py. If the Tesseract path changed, propagate the
    # update so OCR still works without a container restart.
    try:
        import pytesseract as _pt  # local import to avoid cycles
        _pt.pytesseract.tesseract_cmd = settings.tesseract_cmd
    except Exception as exc:  # pragma: no cover — best effort
        _logger.warning("Failed to refresh pytesseract binary path: %s", exc)

    current = {
        "ai_model": settings.ai_model,
        "ai_temperature": settings.ai_temperature,
        "vision_max_pages": settings.vision_max_pages,
        "openrouter_api_key_tail": settings.openrouter_api_key[-4:]
        if settings.openrouter_api_key
        else "",
        "tesseract_cmd": settings.tesseract_cmd,
    }
    changed = {k: (previous[k], current[k]) for k in current if previous[k] != current[k]}
    _logger.info("Settings reloaded. Changed keys: %s", sorted(changed.keys()) or "(none)")
    return {"changed": list(changed.keys()), "current": current}
