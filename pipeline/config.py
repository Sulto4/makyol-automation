import logging
import os
import platform
from pathlib import Path

# Base directory for pipeline package (reliable path resolution)
PIPELINE_DIR = Path(__file__).parent
SCHEMAS_DIR = PIPELINE_DIR / "schemas"

# AI Configuration
OPENROUTER_API_KEY = os.environ.get(
    "OPENROUTER_API_KEY",
    "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",
)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
AI_MODEL = os.environ.get("AI_MODEL", "google/gemini-2.0-flash-001")
AI_TEMPERATURE = 0.0  # NON-NEGOTIABLE
AI_MAX_TOKENS = 4096

# Startup config logging
_logger = logging.getLogger(__name__)
_masked_key = OPENROUTER_API_KEY[:8] + "..." + OPENROUTER_API_KEY[-4:] if len(OPENROUTER_API_KEY) > 12 else "***"
_logger.info("AI config loaded: MODEL=%s, API_KEY=%s", AI_MODEL, _masked_key)

# Tesseract Configuration (OS-aware)
if platform.system() == "Windows":
    TESSERACT_CMD = r"D:\Tesseract-OCR\tesseract.exe"
else:
    TESSERACT_CMD = "/usr/bin/tesseract"
OCR_LANGUAGES = "ron+eng"

# Vision fallback threshold
MIN_TEXT_LENGTH = 20  # chars below which vision fallback activates
VISION_MAX_PAGES = 3
VISION_DPI = 300

# Validation limits
MAX_COMPANY_LENGTH = 80
MAX_MATERIAL_LENGTH = 300
MAX_ADDRESS_LENGTH = 250
MAX_RETRIES = 1

# File paths — always use SCHEMAS_DIR for reliable resolution
KNOWLEDGE_BASE_PATH = SCHEMAS_DIR / "knowledge_base.json"
EXTRACTION_SCHEMAS_PATH = SCHEMAS_DIR / "extraction_schemas.json"
