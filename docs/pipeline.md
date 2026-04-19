---
title: Pipeline (Python/FastAPI)
scope: pipeline
stability: living
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./api-reference.md
  - ./extraction-logic.md
  - ./configuration.md
code_refs:
  - pipeline/__init__.py
  - pipeline/api.py
  - pipeline/classification.py
  - pipeline/extraction.py
  - pipeline/vision_fallback.py
  - pipeline/normalization.py
  - pipeline/Dockerfile
---

# Pipeline

Serviciul Python/FastAPI care clasifică și extrage date din PDF-uri. Rulează pe `:8001` intern în Docker. Primește PDF-uri, returnează JSON cu categorie + câmpuri extrase. Acest doc descrie structura codului. Pentru semantica deciziilor vezi [extraction-logic.md](./extraction-logic.md).

## Rol

- Clasifică un PDF într-una din 14 categorii
- Extrage câmpuri structurate (companie, material, data_expirare, producator, adresa, etc.) — în principal via Gemini 2.5 Flash Vision
- Normalizează rezultatele (fuzzy match KB, OCR fixes, validare)
- Returnează `review_status` care spune dacă documentul trebuie revizuit uman

Nu face: auth, persistență DB, export Excel — acelea sunt în backend.

## Directory layout

| Fișier | LOC | Rol |
|--------|-----|-----|
| `pipeline/__init__.py` | 571 | **Orchestrator** — `process_document()` leagă extraction + classification + vision + normalizare + validare |
| `pipeline/api.py` | 229 | FastAPI endpoints (`/api/pipeline/*`) |
| `pipeline/classification.py` | 740 | Cascade de clasificare: filename regex → text rules → AI |
| `pipeline/extraction.py` | 850 | `EXTRACTION_SCHEMA` (14 categorii) + `normalize_extraction_result` (OCR fixes, diacritice, truncări) + `extract_document_data` (text-only AI) |
| `pipeline/vision_fallback.py` | 410 | Randare PDF→imagine + call Vision AI (Gemini prin OpenRouter) |
| `pipeline/normalization.py` | 266 | Fuzzy match `companie`/`adresa` cu knowledge base (WRatio ≥92) |
| `pipeline/text_extraction.py` | 262 | Cascade pdfplumber → PyMuPDF → Tesseract OCR |
| `pipeline/date_normalizer.py` | 438 | Normalizare date RO (luni, formate, `scan_filename_dates` pentru G4) |
| `pipeline/validation.py` | 258 | `validate_extraction` — setează `review_status` cu motive structurate |
| `pipeline/config.py` | 242 | Settings singleton + hot-reload din backend (`_auth_headers` cu `INTERNAL_API_TOKEN`) |
| `pipeline/logging_config.py` | 119 | StructuredFormatter JSON; rotație zilnică la miezul nopții UTC |
| `pipeline/http_client.py` | 55 | Shared `requests.Session` cu pool HTTPAdapter |
| `pipeline/thread_pools.py` | 73 | `OCR_POOL` (3), `PAGE_RENDER_POOL` (4), `TEXT_ENGINE_POOL` (4) |
| `pipeline/regex_extraction.py` | 158 | Regex text fallback (când AI returnează None) |
| `pipeline/schemas/knowledge_base.json` | — | Companii cunoscute (canonical + aliases + CUI + address) |
| `pipeline/schemas/extraction_schemas.json` | — | JSON schema definitions (referință) |

## FastAPI app

`pipeline/api.py:57` (`app = FastAPI(title="Makyol Pipeline API", version="1.0.0")`).

**Startup hook** (`api.py:60-98`): `@app.on_event("startup")` → `check_ai_connectivity()` trimite un mesaj scurt către OpenRouter cu timeout 10s. Loghează `AI connectivity: OK` / `AUTH FAILED` (cu key masked) / `TIMEOUT`. Non-blocking — pipeline pornește indiferent.

**Endpoints** (5 total — vezi [api-reference.md#pipeline](./api-reference.md#pipeline---apipipeline)):
- `GET /api/pipeline/health` (`api.py:112`)
- `POST /api/pipeline/reload-settings` (`api.py:118`)
- `GET /api/pipeline/stats` (`api.py:135`)
- `POST /api/pipeline/process` (`api.py:145`)
- `POST /api/pipeline/batch` (`api.py:185`)

**In-memory stats** (`api.py:23-33`): `_stats` dict cu counts pe method, category, AI calls/failures. Resetat la restart serviciu.

**Asyncio offload** (`api.py:169`): `process_document` e sincron și blocant (PDF parse + HTTP OpenRouter). E rulat prin `asyncio.to_thread()` ca request-urile concurente să nu serializeze.

## `process_document` flow

`pipeline/__init__.py:105` — orchestratorul principal. Pașii înalți:

```
process_document(pdf_path, filename):
  1. Startup async:
     - text = extract_text_from_pdf(pdf_path)          # pdfplumber → PyMuPDF → Tesseract
     - page_count = get_page_count(pdf_path)
     - images_future = _render_executor.submit(_pdf_pages_to_base64, pdf_path)
                                                        # background render la 300 DPI

  2. Classification cascade:
     category, conf, method = classify_document(filename, text, page_count, has_tables)

  3. Extraction:
     if _USE_VISION_FOR_ALL:  # True @ __init__.py:29
       images = images_future.result()
       extraction = extract_with_vision(images, category, filename)
     if extraction is None or all fields null:
       extraction = extract_document_data(text, category, filename)   # text AI
     if extraction still null + text too short:
       extraction = regex_extraction.extract(text, category)          # regex fallback

  4. Post-processing:
     extraction = normalize_extraction_result(extraction, category, text)
       - OCR fixes, diacritics, date calc din duration, truncări
       - Drop data_expirare dacă category nu e în CATEGORIES_WITH_DATA_EXPIRARE
       - _clean_company_name, KB fuzzy match (normalize_company_name, normalize_address)

  5. G4 filename fallback (__init__.py, CATEGORIES_WITH_DATA_EXPIRARE only):
     if not extraction.data_expirare and filename are date candidates:
       extraction.data_expirare = max(scan_filename_dates(filename))

  6. G5 suspicious-expiry guard (__init__.py:46, 180 days):
     if extraction.data_expirare is >180 days in past
        AND not corroborated by filename:
       review_status = "REVIEW"
       review_reasons.append("suspicious past expiry")

  7. Validation (validation.py:122):
     result, review_status, review_reasons = validate_extraction(...)

  8. Return {
       filename, classification, confidence, method,
       extraction, review_status, review_reasons,
       used_vision, page_count, total_duration_ms,
       extraction_model  # "vision:<model>" sau "regex_fallback"
     }
```

## Classification cascade

`classify_document` la `classification.py:635`. Cascade în 3 nivele:

| Nivel | Funcție | LOC | Returnează |
|-------|---------|-----|-----------|
| 1. Filename regex | `classify_by_filename` | `classification.py:168` | Match regex din lista `_FILENAME_PATTERNS` (29 patterns, confidențe 0.70-0.95) sau `None` |
| 2. Text rules | `classify_by_text` | `classification.py:185` | Markers în primii 500 chars + full text (ISO, CE, aviz sanitar, etc.), confidențe 0.85-0.95 |
| 3. AI fallback | `classify_by_ai` | `classification.py:509` | OpenRouter chat completion, returnează categorie din `VALID_CATEGORIES` |

**14 categorii valide** (`classification.py:30`):
`ISO`, `CE`, `FISA_TEHNICA`, `AGREMENT`, `AVIZ_TEHNIC`, `AVIZ_SANITAR`, `DECLARATIE_CONFORMITATE`, `CERTIFICAT_CALITATE`, `AUTORIZATIE_DISTRIBUTIE`, `CUI`, `CERTIFICAT_GARANTIE`, `DECLARATIE_PERFORMANTA`, `AVIZ_TEHNIC_SI_AGREMENT`, `ALTELE`.

Logica de reconciliere filename-vs-text (`filename+text_agree`, `filename_wins`, `text_override`) e în `classify_document`. Detaliile semantice în [extraction-logic.md](./extraction-logic.md#clasificare).

## Extraction

### `EXTRACTION_SCHEMA` (`extraction.py:34`)

Dict cu 14 chei (categorii), fiecare cu:
- `fields` — lista de câmpuri de extras (ex: `["companie", "data_expirare", "standard_iso", "adresa_producator"]`)
- `instructions` — prompt specific categoriei pentru AI

**`CATEGORIES_WITH_DATA_EXPIRARE`** (`extraction.py:202`) — frozenset cu categoriile la care `data_expirare` e câmp valid. Folosit la G1 (drop `data_expirare` pentru categoriile fără) și la G4 (filename fallback doar pentru acestea).

### Vision path

`extract_with_vision` (`vision_fallback.py:194`):
1. `_pdf_pages_to_base64(pdf_path)` (`vision_fallback.py:158`) — randează selectate pagini la 300 DPI (`VISION_DPI` în `config.py:114`) via PyMuPDF în `PAGE_RENDER_POOL`
2. `_select_page_indices(total_pages, vision_max_pages)` — alege `(N-1)` pagini de început + ultima
3. Construiește payload multimodal: `{type: "text", ...}` + N × `{type: "image_url", image_url: {url: "data:image/png;base64,..."}}`
4. POST la `OPENROUTER_URL` (`config.py:111`) cu `settings.ai_model`, `settings.ai_temperature`, `AI_MAX_TOKENS=4096` (timeout 120s)
5. Parsează răspuns JSON

### Text path (fallback)

`extract_document_data` (`extraction.py:799`) — trimite `(text, category, filename)` la OpenRouter cu prompt-ul bazat pe schema. Folosit când Vision returnează None sau toate câmpurile extrase sunt null.

### Regex path (last-resort)

`pipeline/regex_extraction.py` — pattern matching pe text când text-AI nu merge (tipic când OpenRouter e down sau cheia e invalidă). `extraction_model` devine `regex_fallback`.

## Knowledge base (fuzzy match)

`pipeline/schemas/knowledge_base.json` — 10 companii cunoscute (TERAPLAST, VALROM, REHAU, VALSIR, GEBERIT, WAVIN, PESTAN, ARMACELL, HENKEL, HUAYANG) cu:
- `canonical` — numele oficial de folosit
- `aliases` — variante de scriere/OCR
- `cui` — CUI-ul românesc
- `canonical_address` + `address_aliases`

**Funcții de normalizare** (`normalization.py`):
- `normalize_company_name(raw_name)` la `normalization.py:122` — returnează `(canonical, was_matched)`. Folosește `rapidfuzz.WRatio ≥ 92` cu cerință overlap primul cuvânt >3 chars (evită false positives).
- `normalize_address(raw_address)` la `normalization.py:231` — idem pentru adrese.

Detalii semantice în [extraction-logic.md#knowledge-base](./extraction-logic.md#knowledge-base).

## Hot-reload settings

`pipeline/config.py:201-242` — `reload_settings()`:
1. Re-cheamă `fetch_settings_from_api()` (cu retries, header `Authorization: Bearer <INTERNAL_API_TOKEN>`)
2. Actualizează singleton `settings` via `_apply_from_api_cache()`
3. Rescrie `pytesseract.pytesseract.tesseract_cmd` dacă path-ul s-a schimbat
4. Returnează `{changed: [...], current: {...}}`

Triggerat de backend la `POST /api/pipeline/reload-settings` după fiecare `PUT /api/settings/:key`.

## Thread pools

`pipeline/thread_pools.py` — 3 pool-uri module-level, tunabile prin env:

| Pool | Default | Env var | Scop |
|------|---------|---------|------|
| `OCR_POOL` | 3 | `PIPELINE_OCR_POOL_SIZE` | Apeluri Tesseract (CPU-bound) |
| `PAGE_RENDER_POOL` | 4 | `PIPELINE_PAGE_RENDER_POOL_SIZE` | Randare PDF→PNG pentru Vision |
| `TEXT_ENGINE_POOL` | 4 | `PIPELINE_TEXT_ENGINE_POOL_SIZE` | pdfplumber + PyMuPDF cascade |

## Logging

`pipeline/logging_config.py:17-40` — `StructuredFormatter` output JSON single-line. Rotație zilnică la miezul nopții UTC. Output la `/app/logs/pipeline.log` în container (bind mount `./logs/pipeline`).

Loguri cu `extra_data` dict pentru grouping în dashboard (durations, field counts, review reasons).

## Build & run

### Dockerfile (`pipeline/Dockerfile`)

- Base: `python:3.11-slim`
- System deps: `tesseract-ocr`, `tesseract-ocr-ron`, `tesseract-ocr-eng`, `curl`
- User non-root: `pipeline:1001`
- Copy `pipeline/`, install `requirements.txt`
- `EXPOSE 8001`, healthcheck `curl /api/pipeline/health` la 30s
- `CMD ["uvicorn", "pipeline.api:app", "--host", "0.0.0.0", "--port", "8001"]`

### Dependențe cheie (din `requirements.txt`)

- `fastapi`, `uvicorn[standard]` — framework
- `pdfplumber`, `PyMuPDF`, `pytesseract` — extracție text/OCR
- `Pillow` — image processing
- `rapidfuzz` — fuzzy match KB
- `requests` — OpenRouter
- `httpx` — async HTTP (startup check)
- `python-multipart` — FastAPI file upload

## Verify freshness

```bash
# _USE_VISION_FOR_ALL = True
grep -n "_USE_VISION_FOR_ALL" pipeline/__init__.py
# trebuie L29 = True

# 14 categorii valide
grep -A16 "^VALID_CATEGORIES = \[" pipeline/classification.py | head -16

# process_document la liniea așteptată
grep -n "^def process_document" pipeline/__init__.py
# trebuie L105

# Schema extraction
grep -n "^EXTRACTION_SCHEMA = {" pipeline/extraction.py
# trebuie L34

# Categoriile cu data_expirare
grep -n "^CATEGORIES_WITH_DATA_EXPIRARE = frozenset" pipeline/extraction.py
# trebuie L202

# Vision DPI setat
grep -n "VISION_DPI" pipeline/config.py
# trebuie 300

# INTERNAL_API_TOKEN folosit la fetch settings
grep -n "_auth_headers" pipeline/config.py
# trebuie L22 + folosit la fetch

# 5 endpoints FastAPI
grep -E "^@app\.(get|post)" pipeline/api.py | wc -l
# trebuie 5

# Rulează un health check direct
curl -s http://localhost:8001/api/pipeline/health
# {"status":"ok","service":"python-pipeline"}
```
