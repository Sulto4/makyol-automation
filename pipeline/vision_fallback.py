"""Gemini Vision fallback for scanned PDFs with insufficient extracted text.

Converts first N pages to high-DPI PNG images via PyMuPDF, base64-encodes them,
and sends to OpenRouter as multimodal content (text prompt + image_url entries).
Uses the same AI model and extraction prompts as text-based extraction.
Targets scanned certificates (e.g., ISO Huayang) where OCR yields <20 chars.
"""

import base64
import json
import logging
import re

import fitz  # PyMuPDF
import requests

from pipeline.config import (
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_TEMPERATURE,
    MAX_ADDRESS_LENGTH,
    MAX_COMPANY_LENGTH,
    MAX_MATERIAL_LENGTH,
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    VISION_DPI,
    VISION_MAX_PAGES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Vision extraction prompt (same extraction rules as text-based prompt)
# ---------------------------------------------------------------------------

_VISION_EXTRACTION_PROMPT = """Esti un expert in extragerea datelor din documente din domeniul constructiilor si materialelor de constructii din Romania.

Analizeaza imaginile atasate dintr-un document PDF clasificat ca "{category}" si extrage urmatoarele informatii:

1. **companie** — Numele companiei principale mentionate in document (producator sau emitent).
   - Extrage DOAR numele companiei, fara CUI, adresa, sau alte detalii.
   - Daca sunt mai multe companii, alege compania PRINCIPALA (emitentul/producatorul).
   - NU include liste separate prin virgula cu mai multe companii.
   - Maxim {max_company} caractere.

2. **material** — Descrierea materialului/produsului.
   - Extrage o descriere CONCISA a materialului sau produsului principal.
   - Include tipul produsului, dimensiunile relevante, standardele (daca sunt mentionate scurt).
   - NU include descrieri generice precum "Produse", "Materiale", "Diverse".
   - NU repeta informatii deja prezente in alte campuri.
   - Maxim {max_material} caractere.

3. **data_expirare** — Data de expirare a documentului.
   - Format: DD.MM.YYYY (ex: 31.12.2025).
   - Daca documentul mentioneaza o durata de valabilitate (ex: "valabil 5 ani de la 01.01.2020"),
     calculeaza data de expirare: 01.01.2020 + 5 ani = 01.01.2025.
   - Daca nu exista data de expirare clara, returneaza null.
   - NU inventa date — daca nu este clar, returneaza null.

4. **producator** — Numele producatorului (daca este diferit de companie).
   - Daca producatorul este acelasi cu compania, returneaza null.
   - Maxim {max_company} caractere.

5. **distribuitor** — Numele distribuitorului (daca este mentionat).
   - Returneaza null daca nu este mentionat un distribuitor.
   - Maxim {max_company} caractere.

6. **adresa_producator** — Adresa producatorului sau a companiei.
   - Extrage adresa completa daca este disponibila.
   - Include strada, numar, oras, judet, cod postal daca sunt mentionate.
   - Maxim {max_address} caractere.

7. **adresa_distribuitor** — Adresa distribuitorului (daca este mentionata).
   - Extrage adresa completa daca este disponibila.
   - Include strada, numar, oras, judet, cod postal daca sunt mentionate.
   - Returneaza null daca nu este mentionat un distribuitor sau adresa acestuia.
   - Maxim {max_address} caractere.

REGULI IMPORTANTE:
- Raspunde DOAR cu un JSON valid, fara explicatii sau text suplimentar.
- Foloseste null pentru campurile care nu pot fi determinate din imagini.
- NU inventa informatii care nu sunt vizibile in imagini.
- NU include caractere chinezesti in raspuns — daca documentul contine caractere chinezesti
  amestecate cu text latin, extrage DOAR textul latin.
- Daca imaginile sunt ilizibile, returneaza un JSON cu toate campurile null.
- Corecteaza GRESELI EVIDENTE de OCR (ex: "lndustrie" → "Industrie").

Format raspuns:
{{
    "companie": "Numele Companiei" sau null,
    "material": "Descrierea materialului" sau null,
    "data_expirare": "DD.MM.YYYY" sau null,
    "producator": "Numele Producatorului" sau null,
    "distribuitor": "Numele Distribuitorului" sau null,
    "adresa_producator": "Adresa completa" sau null,
    "adresa_distribuitor": "Adresa distribuitorului" sau null
}}"""


def _pdf_pages_to_base64(pdf_path: str) -> list[str]:
    """Convert first pages of a PDF to base64-encoded PNG images.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of base64-encoded PNG strings (one per page, up to VISION_MAX_PAGES).
    """
    images_b64 = []
    doc = fitz.open(pdf_path)
    try:
        page_count = min(len(doc), VISION_MAX_PAGES)
        for i in range(page_count):
            page = doc[i]
            pix = page.get_pixmap(dpi=VISION_DPI)
            png_bytes = pix.tobytes("png")
            b64_str = base64.b64encode(png_bytes).decode("ascii")
            images_b64.append(b64_str)
    finally:
        doc.close()
    return images_b64


def extract_with_vision(pdf_path: str, category: str) -> dict | None:
    """Extract structured data from a scanned PDF using Gemini Vision.

    Converts PDF pages to images and sends them as multimodal content
    to the AI model via OpenRouter.

    Args:
        pdf_path: Path to the PDF file.
        category: Document category from classification.

    Returns:
        Extraction result dict, or None on failure.
    """
    # Convert pages to base64 images
    try:
        images_b64 = _pdf_pages_to_base64(pdf_path)
    except Exception as e:
        logger.error("Failed to convert PDF pages to images: %s", e)
        return None

    if not images_b64:
        logger.warning("No pages extracted from %s", pdf_path)
        return None

    # Build multimodal content: text prompt + image entries
    prompt_text = _VISION_EXTRACTION_PROMPT.format(
        category=category,
        max_company=MAX_COMPANY_LENGTH,
        max_material=MAX_MATERIAL_LENGTH,
        max_address=MAX_ADDRESS_LENGTH,
    )

    content_parts = [{"type": "text", "text": prompt_text}]
    for b64_img in images_b64:
        content_parts.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{b64_img}",
            },
        })

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": AI_MODEL,
        "messages": [{"role": "user", "content": content_parts}],
        "temperature": AI_TEMPERATURE,  # 0.0 — NON-NEGOTIABLE
        "max_tokens": AI_MAX_TOKENS,
    }

    try:
        response = requests.post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=120
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Strip markdown code fences if present
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content.strip())

        parsed = json.loads(content)
        return parsed

    except requests.exceptions.Timeout:
        logger.error("Vision extraction timed out for %s", pdf_path)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Vision extraction request failed: %s", e)
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("Vision extraction response parsing failed: %s", e)
        return None
