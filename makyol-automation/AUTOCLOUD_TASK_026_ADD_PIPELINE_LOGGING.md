# Task 026: Add Comprehensive Pipeline Logging & Observability

## Priority: HIGH (P1)
## Estimated effort: 3-4 hours
## Depends on: Task 025 (env fix)

## Problem

The current pipeline has minimal logging. When 300+ documents are processed and results are poor, there's no way to diagnose what happened. The backend TypeScript logger is decent but the Python pipeline logs almost nothing useful about the processing steps.

## Current State

### Python pipeline logging (INSUFFICIENT):
- `__init__.py`: logs "Text too short", "Classified by X", basic errors
- `classification.py`: logs classification result (category, method)
- `extraction.py`: logs "AI extraction timed out" or "request failed" — but NOT the response content or HTTP status
- `text_extraction.py`: logs engine fallback warnings — but NOT text lengths
- `vision_fallback.py`: logs errors only
- `normalization.py`: NO logging at all
- `validation.py`: logs validation issues

### TypeScript backend logging (OK but incomplete):
- `documentController.ts`: logs document ID, classification, extraction status
- Missing: pipeline response time, full pipeline response for debugging

## Requirements

### 1. Add structured logging to Python pipeline

Create `pipeline/logging_config.py`:

```python
"""Structured logging configuration for the pipeline."""
import logging
import json
import sys
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    """JSON structured log formatter."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
        }
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(level=logging.INFO):
    """Configure structured logging for the pipeline."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    root = logging.getLogger("pipeline")
    root.setLevel(level)
    root.addHandler(handler)
    
    # Suppress noisy libraries
    logging.getLogger("pdfminer").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### 2. Add detailed logging to each pipeline step

#### `pipeline/__init__.py` — process_document()
Log at each step with timing:

```python
import time

def process_document(pdf_path, filename=""):
    start_time = time.time()
    
    # Step 1: Text extraction
    t0 = time.time()
    text = extract_text_from_pdf(pdf_path)
    logger.info("Text extraction complete", extra={"extra_data": {
        "filename": filename,
        "text_length": len(text.strip()),
        "duration_ms": int((time.time() - t0) * 1000),
        "engine_used": "multi-engine",  # TODO: track which engine succeeded
    }})
    
    # Step 3: Classification
    t0 = time.time()
    category, confidence, method = classify_document(filename, text)
    logger.info("Classification complete", extra={"extra_data": {
        "filename": filename,
        "category": category,
        "confidence": confidence,
        "method": method,
        "duration_ms": int((time.time() - t0) * 1000),
    }})
    
    # Step 4: Extraction
    t0 = time.time()
    extraction = extract_document_data(text, category)
    non_null_fields = sum(1 for v in extraction.values() if v is not None)
    logger.info("Extraction complete", extra={"extra_data": {
        "filename": filename,
        "category": category,
        "non_null_fields": non_null_fields,
        "total_fields": len(extraction),
        "fields": {k: ("SET" if v else "null") for k, v in extraction.items()},
        "duration_ms": int((time.time() - t0) * 1000),
    }})
    
    # ... rest of pipeline ...
    
    total_ms = int((time.time() - start_time) * 1000)
    logger.info("Pipeline complete", extra={"extra_data": {
        "filename": filename,
        "total_duration_ms": total_ms,
        "classification": category,
        "confidence": confidence,
        "method": method,
        "non_null_fields": non_null_fields,
        "review_status": result["review_status"],
        "used_vision": result["used_vision"],
        "has_error": result["error"] is not None,
    }})
```

#### `pipeline/extraction.py` — extract_data_with_ai()
Log the AI request and response:

```python
def extract_data_with_ai(text, category):
    logger.info("Starting AI extraction", extra={"extra_data": {
        "category": category,
        "text_length": len(text),
        "truncated_to": min(len(text), 6000),
    }})
    
    try:
        response = requests.post(...)
        logger.info("AI extraction response", extra={"extra_data": {
            "status_code": response.status_code,
            "response_length": len(response.text),
            "model": AI_MODEL,
        }})
        # ... parse ...
        logger.info("AI extraction parsed", extra={"extra_data": {
            "fields_extracted": list(parsed.keys()),
            "non_null": sum(1 for v in parsed.values() if v is not None),
        }})
        
    except requests.exceptions.Timeout:
        logger.error("AI extraction TIMEOUT", extra={"extra_data": {
            "category": category,
            "timeout_seconds": 60,
        }})
    except requests.exceptions.RequestException as e:
        logger.error("AI extraction HTTP ERROR", extra={"extra_data": {
            "category": category,
            "error_type": type(e).__name__,
            "error_message": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "response_body": getattr(e.response, 'text', '')[:500] if hasattr(e, 'response') and e.response else None,
        }})
```

#### `pipeline/classification.py` — classify_by_ai()
Same treatment — log request, response, parsing result or error.

#### `pipeline/normalization.py`
Add logging for fuzzy matches:

```python
def normalize_company_name(raw_name):
    # ... after matching ...
    if was_matched:
        logger.debug("Company normalized", extra={"extra_data": {
            "raw": raw_name[:60],
            "canonical": canonical,
            "match_score": best_score,
        }})
```

### 3. Add per-document processing summary to backend

In `documentController.ts`, after pipeline response:

```typescript
logger.info(`Document ${document.id} processing summary`, {
    filename: originalFilename,
    classification: pipelineResponse.classification,
    confidence: pipelineResponse.confidence,
    method: pipelineResponse.method,
    extractedFields: Object.entries(pipelineResponse.extraction || {})
        .filter(([_, v]) => v != null).map(([k]) => k),
    nullFields: Object.entries(pipelineResponse.extraction || {})
        .filter(([_, v]) => v == null).map(([k]) => k),
    usedVision: pipelineResponse.used_vision,
    reviewStatus: pipelineResponse.review_status,
    error: pipelineResponse.error,
});
```

### 4. Add batch processing summary endpoint

Add `GET /api/pipeline/stats` to `pipeline/api.py`:

```python
@app.get("/api/pipeline/stats")
async def processing_stats():
    """Return processing statistics for debugging."""
    return {
        "total_processed": _stats["total"],
        "successful": _stats["success"],
        "failed": _stats["failed"],
        "avg_duration_ms": _stats["avg_duration"],
        "classification_methods": _stats["methods"],
        "categories": _stats["categories"],
        "ai_calls": _stats["ai_calls"],
        "ai_failures": _stats["ai_failures"],
    }
```

## Verification

1. Process a single document → check `docker compose logs pipeline` shows structured JSON with all steps
2. Process 5 documents → verify each has timing, classification method, extracted fields summary
3. When AI fails → error log must show HTTP status code, response body, and error type
4. `GET /api/pipeline/stats` returns meaningful counters

## Files to modify

- `pipeline/logging_config.py` — create new file
- `pipeline/__init__.py` — add step-by-step logging with timing
- `pipeline/extraction.py` — add AI request/response logging
- `pipeline/classification.py` — add AI request/response logging
- `pipeline/normalization.py` — add match logging
- `pipeline/api.py` — setup logging on startup, add /stats endpoint
- `src/controllers/documentController.ts` — add per-document summary log
