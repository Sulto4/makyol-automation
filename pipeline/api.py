"""FastAPI service for the Makyol document processing pipeline."""

import asyncio
import logging
import os
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from pipeline.logging_config import setup_logging

setup_logging()

from pipeline import process_document
from pipeline.config import OPENROUTER_API_KEY, OPENROUTER_URL, AI_MODEL

logger = logging.getLogger(__name__)

# In-memory stats accumulator (resets on service restart)
_stats: dict = {
    "total_processed": 0,
    "successful": 0,
    "failed": 0,
    "total_duration_ms": 0,
    "classification_methods": {},
    "categories": {},
    "ai_calls": 0,
    "ai_failures": 0,
}


def _track_result(result: dict) -> None:
    """Update stats accumulator after processing a document."""
    _stats["total_processed"] += 1
    if result.get("error") or result.get("review_status") == "FAILED":
        _stats["failed"] += 1
    else:
        _stats["successful"] += 1
    # Track duration
    _stats["total_duration_ms"] += result.get("total_duration_ms", 0)
    # Track classification method
    method = result.get("method", "unknown")
    _stats["classification_methods"][method] = _stats["classification_methods"].get(method, 0) + 1
    # Track category
    category = result.get("classification") or result.get("category") or "unknown"
    _stats["categories"][category] = _stats["categories"].get(category, 0) + 1
    # Track AI calls — if method is "ai", that counts as an AI call
    if method == "ai":
        _stats["ai_calls"] += 1
        if result.get("error") or result.get("review_status") == "FAILED":
            _stats["ai_failures"] += 1


app = FastAPI(title="Makyol Pipeline API", version="1.0.0")


@app.on_event("startup")
async def check_ai_connectivity():
    """Verify AI provider connectivity at startup (non-blocking)."""
    masked_key = (
        OPENROUTER_API_KEY[:8] + "..." + OPENROUTER_API_KEY[-4:]
        if len(OPENROUTER_API_KEY) > 12
        else "***"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": AI_MODEL,
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                },
            )
        if resp.status_code == 200:
            logger.info("AI connectivity: OK (model=%s)", AI_MODEL)
        elif resp.status_code in (401, 403):
            logger.critical(
                "AI connectivity: AUTH FAILED (status=%s, key=%s, response=%s)",
                resp.status_code,
                masked_key,
                resp.text[:500],
            )
        else:
            logger.error(
                "AI connectivity: UNEXPECTED STATUS %s (response=%s)",
                resp.status_code,
                resp.text[:500],
            )
    except httpx.TimeoutException:
        logger.critical("AI connectivity: TIMEOUT after 10s (url=%s)", OPENROUTER_URL)
    except Exception as exc:
        logger.critical("AI connectivity: FAILED (%s: %s)", type(exc).__name__, exc)


class BatchRequest(BaseModel):
    """Request body for batch processing."""
    folder_path: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    service: str


@app.get("/api/pipeline/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", service="python-pipeline")


@app.get("/api/pipeline/stats")
async def get_stats():
    """Return current in-memory processing statistics."""
    result = dict(_stats)
    total = result["total_processed"]
    total_dur = result.pop("total_duration_ms")
    result["avg_duration_ms"] = round(total_dur / total, 1) if total > 0 else 0
    return result


@app.post("/api/pipeline/process")
async def process_single(file: UploadFile = File(...)):
    """Upload and process a single PDF document.

    Accepts a PDF file via multipart upload, runs it through the full
    pipeline (text extraction → classification → data extraction →
    normalization → validation), and returns structured results.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    tmp_path = None
    try:
        # Write uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        # process_document is synchronous and does blocking I/O (PDF
        # parsing, OpenRouter HTTP calls). Running it directly here would
        # block the asyncio event loop and serialize all concurrent
        # requests. Offload to a thread so multiple docs can be in flight
        # at once — backend now sends up to BATCH_CONCURRENCY=3.
        result = await asyncio.to_thread(
            process_document, tmp_path, filename=file.filename
        )
        _track_result(result)
        return result

    except Exception as e:
        logger.error("Processing failed for %s: %s", file.filename, e)
        _track_result({"error": str(e), "review_status": "FAILED"})
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/api/pipeline/batch")
async def process_batch(request: BatchRequest):
    """Process all PDF files in a folder.

    Scans the given folder_path for PDF files and processes each one
    through the pipeline, returning results for all documents.
    """
    folder = Path(request.folder_path)
    if not folder.is_dir():
        raise HTTPException(status_code=400, detail="Folder not found")

    pdf_files = sorted(folder.glob("*.pdf"))
    if not pdf_files:
        raise HTTPException(status_code=400, detail="No PDF files found in folder")

    results = []
    for pdf_path in pdf_files:
        try:
            result = process_document(str(pdf_path), filename=pdf_path.name)
            _track_result(result)
            results.append(result)
        except Exception as e:
            logger.error("Batch processing failed for %s: %s", pdf_path.name, e)
            error_result = {
                "filename": pdf_path.name,
                "error": str(e),
                "review_status": "FAILED",
            }
            _track_result(error_result)
            results.append(error_result)

    return {"total": len(pdf_files), "results": results}


if __name__ == "__main__":
    import sys
    from pathlib import Path as _Path

    # Ensure the project root is on sys.path when running directly
    _root = str(_Path(__file__).resolve().parent.parent)
    if _root not in sys.path:
        sys.path.insert(0, _root)

    import uvicorn
    uvicorn.run("pipeline.api:app", host="0.0.0.0", port=8001)
