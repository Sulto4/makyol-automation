"""FastAPI service for the Makyol document processing pipeline."""

import logging
import os
import tempfile
from pathlib import Path

import httpx
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from pipeline import process_document
from pipeline.config import OPENROUTER_API_KEY, OPENROUTER_URL, AI_MODEL

logger = logging.getLogger(__name__)

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

        result = process_document(tmp_path, filename=file.filename)
        return result

    except Exception as e:
        logger.error("Processing failed for %s: %s", file.filename, e)
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
            results.append(result)
        except Exception as e:
            logger.error("Batch processing failed for %s: %s", pdf_path.name, e)
            results.append({
                "filename": pdf_path.name,
                "error": str(e),
                "review_status": "FAILED",
            })

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
