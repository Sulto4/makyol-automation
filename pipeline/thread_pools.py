"""Process-wide thread pools for CPU-heavy pipeline work.

Background: we run multiple documents concurrently (see BATCH_CONCURRENCY
in the backend), and each document internally uses its own ThreadPool
for page rendering + OCR. Without coordination, 5 concurrent docs × 4
internal OCR workers = 20 simultaneous Tesseract processes on a 16-core
host, which saturates CPU and blows up memory (each 300-DPI page image
is several MB in RAM).

Sharing a single module-level pool per workload caps *total* concurrency
regardless of how many docs are in flight, which is the correct
invariant for CPU-bound work. The backend's BATCH_CONCURRENCY setting
controls external queueing (pipeline HTTP calls); these pools control
internal CPU usage.

Pool sizes are deliberately conservative:
  * Tesseract OCR is memory- and CPU-heavy and holds its thread for
    seconds per page — keep the pool small (3).
  * PyMuPDF pixmap rendering is fast but blocks on image compression;
    4 threads saturate it cleanly on typical PDFs.
  * pdfplumber + PyMuPDF text racing happens twice per doc and is
    sub-second — a dedicated pool of 4 is plenty.

Tune via env vars if needed; defaults are chosen for a 16-core host.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor


def _env_int(key: str, default: int) -> int:
    """Read an integer env var, fall back to default on anything invalid."""
    raw = os.environ.get(key)
    if not raw:
        return default
    try:
        v = int(raw)
        return max(1, v)
    except (TypeError, ValueError):
        return default


# OCR is the heaviest workload — Tesseract holds a thread for multiple
# seconds per page at 300 DPI. Keep the pool small so a batch of scanned
# docs cannot peg every core.
OCR_POOL_SIZE = _env_int("PIPELINE_OCR_POOL_SIZE", 3)

# 300-DPI pixmap rendering: fast per page but still compute-intensive
# during PNG encoding. Size matches the typical vision doc (1–3 pages).
PAGE_RENDER_POOL_SIZE = _env_int("PIPELINE_RENDER_POOL_SIZE", 4)

# pdfplumber + PyMuPDF race. Two slots per doc is the minimum; a shared
# pool of 4 accommodates two concurrent docs without queueing on text
# extraction, which is the hot path for the common digital-PDF case.
TEXT_ENGINE_POOL_SIZE = _env_int("PIPELINE_TEXT_ENGINE_POOL_SIZE", 4)


# Module-level singletons. Intentionally never shut down — they live for
# the life of the FastAPI process. Under asyncio.to_thread the pipeline
# is called from FastAPI's default threadpool; these pools sit alongside
# that and are safe to share across docs because each submission carries
# its own state.
OCR_POOL = ThreadPoolExecutor(
    max_workers=OCR_POOL_SIZE, thread_name_prefix="pipeline-ocr"
)
PAGE_RENDER_POOL = ThreadPoolExecutor(
    max_workers=PAGE_RENDER_POOL_SIZE, thread_name_prefix="pipeline-render"
)
TEXT_ENGINE_POOL = ThreadPoolExecutor(
    max_workers=TEXT_ENGINE_POOL_SIZE, thread_name_prefix="pipeline-text"
)
