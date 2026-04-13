# Task 025: Fix Pipeline Environment Configuration & Silent AI Failures

## Priority: CRITICAL (P0)
## Estimated effort: 2-3 hours
## Depends on: None

## Problem

The Python pipeline service running in Docker is missing critical environment variables, causing AI classification (Level 3) and AI extraction to fail silently. When `extract_data_with_ai()` or `classify_by_ai()` fail, they return `None` without any visible error — resulting in zero extracted data (material, companie, producator, etc. all null) and fallback classification to "ALTELE".

The original Python script achieved 67% company extraction, 66% material extraction, and 80% correct classification on 309 documents. The current pipeline shows near-zero extraction rates.

## Root Causes

1. **`OPENROUTER_API_KEY` not passed to pipeline container** — `docker-compose.yml` does not set this env var for the `pipeline` service. The code falls back to a hardcoded key in `pipeline/config.py`, but this is fragile (key expiration, rotation).

2. **AI failures are silent** — When AI calls fail (timeout, auth error, rate limit, network error from Docker), the functions return `None` and processing continues with null fields. No error is surfaced to the user or logged prominently.

3. **`knowledge_base.json` may not be accessible in Docker** — The normalization module loads `KNOWLEDGE_BASE_PATH = SCHEMAS_DIR / "knowledge_base.json"` at import time. If the file is missing in the Docker image, normalization silently fails.

## Requirements

### 1. Fix docker-compose.yml environment variables

Add these to the `pipeline` service in `docker-compose.yml`:

```yaml
pipeline:
  environment:
    PORT: 8001
    DB_HOST: postgres
    DB_PORT: 5432
    DB_USER: postgres
    DB_PASSWORD: postgres
    DB_NAME: pdfextractor
    OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:-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}
    AI_MODEL: ${AI_MODEL:-google/gemini-2.0-flash-001}
```

### 2. Add `.env` file support

Create a `.env.example` file at project root with all required variables:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
AI_MODEL=google/gemini-2.0-flash-001
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=pdfextractor
```

Update `docker-compose.yml` to load from `.env`:
```yaml
env_file:
  - .env
```

### 3. Make AI failures non-silent in pipeline

In `pipeline/extraction.py`, `extract_data_with_ai()`:
- Log the FULL error details at ERROR level (not just a one-liner)
- Include the HTTP status code, response body, and the document filename
- When AI extraction returns None, log a WARNING with the filename: "AI extraction returned no data for {filename}, all fields will be null"

In `pipeline/classification.py`, `classify_by_ai()`:
- Same treatment — log full error details
- When AI classification returns None, log: "AI classification failed for {filename}, falling back to ALTELE"

In `pipeline/__init__.py`, `process_document()`:
- After extraction step, if ALL extracted fields are null, set `result["error"] = "Extraction returned no data — possible AI API failure"`
- Set `result["review_status"] = "NEEDS_CHECK"` in this case

### 4. Add startup health check for AI connectivity

In `pipeline/api.py`, add a startup event that:
- Tests the OpenRouter API key with a minimal request (1 token)
- Logs SUCCESS or FAILURE prominently
- If the key is invalid, log a CRITICAL error: "OPENROUTER_API_KEY is invalid or expired — AI classification and extraction will NOT work"

```python
@app.on_event("startup")
async def verify_ai_connectivity():
    """Verify OpenRouter API key works at startup."""
    # ... test call ...
```

### 5. Verify knowledge_base.json is in Docker image

In `pipeline/Dockerfile`, ensure the schemas directory is copied:
```dockerfile
COPY pipeline/schemas/ ./pipeline/schemas/
```

Add a startup check in `pipeline/normalization.py`:
```python
if not KNOWLEDGE_BASE_PATH.exists():
    logger.critical("knowledge_base.json not found at %s", KNOWLEDGE_BASE_PATH)
```

## Verification

After implementing:
1. `docker compose up --build` — pipeline startup logs should show "AI connectivity: OK" or clear error
2. Upload a single PDF via frontend — check backend logs show classification method and extracted fields
3. If AI fails, logs should show exactly WHY (HTTP status, error message)
4. `docker compose logs pipeline | grep -i "error\|warn\|critical"` should show no silent failures

## Files to modify

- `docker-compose.yml` — add environment variables
- `.env.example` — create new file
- `pipeline/config.py` — use env vars properly
- `pipeline/extraction.py` — improve error logging
- `pipeline/classification.py` — improve error logging
- `pipeline/__init__.py` — detect all-null extraction
- `pipeline/api.py` — add startup AI health check
- `pipeline/Dockerfile` — verify schemas are copied
- `pipeline/normalization.py` — add file existence check
