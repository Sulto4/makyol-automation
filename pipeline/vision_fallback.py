"""Gemini Vision extraction from PDF pages.

Converts selected pages to high-DPI PNG images via PyMuPDF, base64-encodes them,
and sends to OpenRouter as multimodal content (text prompt + image_url entries).
Uses the same AI model and category-specific extraction instructions as
text-based extraction so field semantics (companie vs producator vs distribuitor)
stay consistent across both paths.
"""

import base64
import json
import logging
import re

import fitz  # PyMuPDF
import requests

from pipeline.http_client import get_session
from pipeline.config import (
    AI_MAX_TOKENS,
    MAX_ADDRESS_LENGTH,
    MAX_COMPANY_LENGTH,
    MAX_MATERIAL_LENGTH,
    OPENROUTER_URL,
    VISION_DPI,
    settings,
)
from pipeline.extraction import EXTRACTION_SCHEMA

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Vision extraction prompt — uses the same category-specific instructions
# as text-based extraction (pipeline.extraction.EXTRACTION_SCHEMA) so the
# semantics of companie vs producator vs distribuitor stay consistent.
# ---------------------------------------------------------------------------

_VISION_PROMPT_TEMPLATE = """Esti un expert in extragerea datelor din documente din domeniul constructiilor si materialelor de constructii din Romania.

Analizeaza imaginile atasate dintr-un document PDF clasificat ca "{category}" si extrage informatiile cerute mai jos.

INSTRUCTIUNI SPECIFICE CATEGORIEI "{category}":
{category_instructions}

CAMPURI DE EXTRAS PENTRU ACEASTA CATEGORIE: {fields_list}

REGULI GENERALE PER CAMP:

- **companie** / **producator** / **distribuitor** — respecta distinctia din instructiunile de mai sus.
  - Extrage DOAR numele, fara CUI, adresa sau alte detalii.
  - NU combina mai multe companii intr-un singur camp.
  - Maxim {max_company} caractere fiecare.

- **material** — descriere concisa a produsului principal (tip, dimensiuni, standarde relevante).
  - NU folosi descrieri generice precum "Produse", "Materiale", "Diverse".
  - Maxim {max_material} caractere.

- **data_expirare** — data sau durata de VALABILITATE a documentului.
  - ATENTIE: NU confunda data EMITERII ("Data", "Emis la", "Date of issue",
    "Data intocmirii", "Data emiterii", "Issued on") cu data EXPIRARII.
    Data emiterii este cand a fost CREAT documentul — NU o returna ca data_expirare.
  - Cauta EXPLICIT cuvintele: "Valabil pana la", "Valid until", "Expires on",
    "Expiry date", "Data expirarii", "Valabilitate", "Termen de valabilitate",
    "Expira la". DOAR data asociata acestor expresii este data de expirare.
  - Format preferat: DD.MM.YYYY (ex: 31.12.2025).
  - Daca documentul da o durata textuala (ex: "2 ani de la receptie", "Pe durata contractului",
    "24 luni", "valabil pana la epuizare"), pastreaza-o CA ATARE in acel format textual.
  - Daca documentul da doar o durata + data emiterii (ex: "valabil 5 ani de la 01.01.2020"),
    calculeaza data: 01.01.2025.
  - Daca documentul NU mentioneaza EXPLICIT o data de expirare, durata de
    valabilitate sau termen, returneaza null. NU extrage vreo data aleatorie
    (cod document, data revizuirii, data testarii, data scrisorii) ca expirare.
  - NU inventa date.

- **adresa_producator** — adresa completa (strada, numar, oras, judet, cod postal).
  - Maxim {max_address} caractere.

- **nume_document** — titlul oficial al documentului (max 40 caractere, fara numere/date/coduri).
  - Exemple: "Agrement Tehnic", "Aviz Sanitar", "Certificat CE PED",
    "Certificat ISO 9001", "Certificat de Inregistrare", "Fisa Tehnica Produs",
    "Declaratie de Performanta", "Certificat de Garantie".

REGULI IMPORTANTE:
- Raspunde DOAR cu un JSON valid, fara explicatii sau text suplimentar.
- Foloseste null pentru campurile care nu pot fi determinate din imagini.
- NU inventa informatii care nu sunt vizibile in imagini.
- NU include caractere chinezesti in raspuns — daca documentul contine caractere chinezesti
  amestecate cu text latin, extrage DOAR textul latin.
- Daca imaginile sunt ilizibile, returneaza un JSON cu toate campurile null.
- Corecteaza GRESELI EVIDENTE de OCR (ex: "lndustrie" → "Industrie").

Format raspuns (include TOATE campurile — pune null unde nu se aplica):
{{
    "companie": "Numele Companiei" sau null,
    "material": "Descrierea materialului" sau null,
    "data_expirare": "DD.MM.YYYY sau durata textuala" sau null,
    "producator": "Numele Producatorului" sau null,
    "distribuitor": "Numele Distribuitorului" sau null,
    "adresa_producator": "Adresa completa" sau null,
    "nume_document": "Titlul documentului" sau null,
    "cui_number": "cod CUI" sau null,
    "standard_iso": "ISO 9001:2015" sau null
}}"""


def _build_prompt(category: str) -> str:
    """Render the vision prompt with per-category instructions from the schema."""
    schema = EXTRACTION_SCHEMA.get(category, EXTRACTION_SCHEMA["ALTELE"])
    instructions = schema.get("instructions", "Extrage toate informatiile disponibile.")
    # Include nume_document in the field list like the text-based path does.
    fields = list(set(schema.get("fields", []) + ["nume_document"]))
    return _VISION_PROMPT_TEMPLATE.format(
        category=category,
        category_instructions=instructions,
        fields_list=", ".join(sorted(fields)),
        max_company=MAX_COMPANY_LENGTH,
        max_material=MAX_MATERIAL_LENGTH,
        max_address=MAX_ADDRESS_LENGTH,
    )


def _select_page_indices(total_pages: int, max_pages: int | None = None) -> list[int]:
    """Pick which pages to send to vision.

    Strategy: favor the first pages (cover/header/product info) plus the
    last page (signatures/expiry). `max_pages` caps the total images sent
    so cost stays bounded; when the document has fewer pages than that
    budget we just send them all.

    Edge cases:
      * max_pages == 1 → first page only.
      * max_pages == 2 → first + last (no middle gap to worry about).
      * max_pages >= total_pages → return every page.
      * Otherwise → first (max_pages - 1) pages + last page.
    """
    if max_pages is None:
        max_pages = settings.vision_max_pages
    # Defensive: someone could set max_pages to 0 via the settings UI;
    # fall back to 1 so we still send at least one image.
    if max_pages < 1:
        max_pages = 1

    if total_pages <= 0:
        return []
    if total_pages <= max_pages:
        return list(range(total_pages))
    if max_pages == 1:
        return [0]
    # First (max_pages - 1) pages + the final page. De-duplicate in case
    # max_pages - 1 == total_pages - 1 already covers the last index.
    head = list(range(max_pages - 1))
    last = total_pages - 1
    if last not in head:
        head.append(last)
    return head


def _pdf_pages_to_base64(pdf_path: str) -> list[str]:
    """Convert selected pages of a PDF to base64-encoded PNG images.

    Pages are chosen by _select_page_indices: first two + last page for
    documents longer than 2 pages, otherwise every page.

    Pages render through the process-wide PAGE_RENDER_POOL so total
    in-flight pixmap work is bounded regardless of how many documents the
    backend is processing concurrently. This is what keeps a
    concurrency-5 batch from spawning 15 simultaneous 300-DPI renders.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of base64-encoded PNG strings, in page order.
    """
    from pipeline.thread_pools import PAGE_RENDER_POOL

    doc = fitz.open(pdf_path)
    try:
        indices = _select_page_indices(len(doc))
        if not indices:
            return []

        def _render_one(idx: int) -> str:
            pix = doc[idx].get_pixmap(dpi=VISION_DPI)
            png_bytes = pix.tobytes("png")
            return base64.b64encode(png_bytes).decode("ascii")

        # map() iterates futures in submission order → page order preserved.
        return list(PAGE_RENDER_POOL.map(_render_one, indices))
    finally:
        doc.close()


def extract_with_vision(
    pdf_path: str,
    category: str,
    *,
    images_b64: list[str] | None = None,
    total_pages: int | None = None,
) -> dict | None:
    """Extract structured data from a scanned PDF using Gemini Vision.

    Converts PDF pages to images and sends them as multimodal content
    to the AI model via OpenRouter.

    Args:
        pdf_path: Path to the PDF file.
        category: Document category from classification.
        images_b64: Optional pre-rendered base64 PNG pages. When passed,
            the orchestrator has already started rendering in parallel
            with classification; we skip the re-render here and go straight
            to the API call. Must be paired with `total_pages`.
        total_pages: Optional page count of the source PDF. Only used for
            logging the selection decision when `images_b64` is supplied.

    Returns:
        Extraction result dict, or None on failure.
    """
    import time as _time
    total_start = _time.time()

    # Convert pages to base64 images — unless the caller already did so.
    convert_start = _time.time()
    try:
        if images_b64 is None:
            # Gather page count separately so we can log the selection decision.
            try:
                _doc = fitz.open(pdf_path)
                total_pages = len(_doc)
                _doc.close()
            except Exception:
                total_pages = 0
            selected_indices = _select_page_indices(total_pages)
            images_b64 = _pdf_pages_to_base64(pdf_path)
        else:
            # Trust the pre-rendered images — derive selected_indices for
            # logging parity. If total_pages wasn't provided, we emit 0.
            total_pages = total_pages if total_pages is not None else 0
            selected_indices = _select_page_indices(total_pages) if total_pages else list(range(len(images_b64)))
    except Exception as e:
        logger.error(
            "Failed to convert PDF pages to images: %s", e,
            extra={"extra_data": {
                "step": "vision_image_convert",
                "pdf_path": pdf_path, "error": str(e),
            }},
        )
        return None

    if not images_b64:
        logger.warning(
            "No pages extracted from %s", pdf_path,
            extra={"extra_data": {"step": "vision_image_convert", "pdf_path": pdf_path}},
        )
        return None

    convert_duration_ms = round((_time.time() - convert_start) * 1000, 1)
    total_image_bytes = sum(len(b) for b in images_b64) * 3 // 4  # base64 → raw
    logger.info(
        "Vision images prepared",
        extra={"extra_data": {
            "step": "vision_image_convert",
            "pdf_path": pdf_path,
            "total_pages": total_pages,
            "selected_pages": selected_indices,
            "image_count": len(images_b64),
            "image_bytes_approx": total_image_bytes,
            "dpi": VISION_DPI,
            "duration_ms": convert_duration_ms,
        }},
    )

    # Build multimodal content: category-specific text prompt + image entries
    prompt_text = _build_prompt(category)
    logger.debug(
        "Vision prompt built",
        extra={"extra_data": {
            "step": "vision_prompt",
            "category": category,
            "prompt_chars": len(prompt_text),
            "prompt_preview": prompt_text[:400],
        }},
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
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.ai_model,
        "messages": [{"role": "user", "content": content_parts}],
        "temperature": settings.ai_temperature,
        "max_tokens": AI_MAX_TOKENS,
    }

    api_start = _time.time()
    try:
        response = get_session().post(
            OPENROUTER_URL, headers=headers, json=payload, timeout=120
        )
        api_duration_ms = round((_time.time() - api_start) * 1000, 1)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]
        usage = result.get("usage") or {}
        logger.info(
            "Vision API response received",
            extra={"extra_data": {
                "step": "vision_api",
                "category": category,
                "status_code": response.status_code,
                "duration_ms": api_duration_ms,
                "model": settings.ai_model,
                "response_chars": len(content),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
                "total_tokens": usage.get("total_tokens"),
                "response_preview": content[:500],
            }},
        )

        # Strip markdown code fences if present
        content = re.sub(r"^```json\s*", "", content.strip())
        content = re.sub(r"\s*```$", "", content.strip())

        parsed = json.loads(content)
        non_null = [k for k, v in parsed.items() if v is not None]
        logger.info(
            "Vision extraction parsed",
            extra={"extra_data": {
                "step": "vision_extract",
                "category": category,
                "total_duration_ms": round((_time.time() - total_start) * 1000, 1),
                "field_names": list(parsed.keys()),
                "non_null_count": len(non_null),
                "non_null_fields": non_null,
            }},
        )
        return parsed

    except requests.exceptions.Timeout:
        logger.error(
            "Vision extraction timed out for %s", pdf_path,
            extra={"extra_data": {
                "step": "vision_api", "pdf_path": pdf_path,
                "timeout_seconds": 120,
                "duration_ms": round((_time.time() - api_start) * 1000, 1),
            }},
        )
        return None
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, "status_code", None) if hasattr(e, "response") else None
        response_body = getattr(e.response, "text", None) if hasattr(e, "response") else None
        logger.error(
            "Vision extraction request failed: %s", e,
            extra={"extra_data": {
                "step": "vision_api", "pdf_path": pdf_path,
                "error": str(e),
                "status_code": status_code,
                "response_body": response_body[:500] if response_body else None,
            }},
        )
        return None
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error(
            "Vision extraction response parsing failed: %s", e,
            extra={"extra_data": {
                "step": "vision_parse", "pdf_path": pdf_path,
                "error": str(e), "error_type": type(e).__name__,
                "content_preview": content[:500] if "content" in dir() else None,
            }},
        )
        return None
