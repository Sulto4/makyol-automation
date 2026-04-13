"""FastAPI service for the Makyol document processing pipeline."""

import logging
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel

from pipeline.logging_config import setup_logging

setup_logging()

from pipeline import process_document

logger = logging.getLogger(__name__)

# In-memory stats accumulator (resets on service restart)
_stats: dict = {
    "total_processed": 0,
    "total_success": 0,
    "total_failed": 0,
    "by_status": {},
}


def _track_result(result: dict) -> None:
    """Update stats accumulator after processing a document."""
    _stats["total_processed"] += 1
    status = result.get("review_status", "UNKNOWN")
    if status == "FAILED":
        _stats["total_failed"] += 1
    else:
        _stats["total_success"] += 1
    _stats["by_status"][status] = _stats["by_status"].get(status, 0) + 1


app = FastAPI(title="Makyol Pipeline API", version="1.0.0")


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
    return _stats


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
        _track_result(result)
        return result

    except Exception as e:
        logger.error("Processing failed for %s: %s", file.filename, e)
        _stats["total_processed"] += 1
        _stats["total_failed"] += 1
        _stats["by_status"]["FAILED"] = _stats["by_status"].get("FAILED", 0) + 1
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
