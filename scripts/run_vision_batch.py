"""Parallel batch runner for the vision-powered pipeline.

Walks one or more input roots, runs pipeline.process_document on every PDF
using a ThreadPoolExecutor (calls are I/O bound — blocked on OpenRouter).
Writes a JSON report with per-document status, durations, classification,
and extraction fields plus an aggregate summary.

Usage:
    python -m scripts.run_vision_batch --input "Pachete Makyol/1" --workers 8
    python -m scripts.run_vision_batch --input "Pachete Makyol" --workers 10 --output reports/full_run.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Allow running the script both as a module and directly
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline import process_document  # noqa: E402
from pipeline.logging_config import setup_logging  # noqa: E402

logger = logging.getLogger("vision_batch")

RETRYABLE_ERROR_TOKENS = ("429", "timed out", "timeout", "rate limit", "503", "502")
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_BACKOFF = 4.0  # seconds
SKIP_SUFFIXES = {".docx", ".doc", ".xlsx", ".xls", ".jpg", ".jpeg", ".png", ".db", ".tmp"}


def _discover_pdfs(root: Path) -> list[Path]:
    """Return a sorted list of PDF files under root, skipping hidden/Office files."""
    if not root.exists():
        logger.error("Input path does not exist: %s", root)
        return []

    pdfs: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name.startswith(".") or name.startswith("~$"):
            continue
        suffix = path.suffix.lower()
        if suffix in SKIP_SUFFIXES:
            continue
        if suffix != ".pdf":
            continue
        pdfs.append(path)
    return pdfs


def _is_retryable(result: dict) -> bool:
    err = (result.get("error") or "").lower()
    if not err:
        return False
    return any(token in err for token in RETRYABLE_ERROR_TOKENS)


def _process_with_retry(pdf_path: Path, max_retries: int, base_backoff: float) -> dict:
    """Call process_document with retry/backoff on transient errors (429/timeout)."""
    attempt = 0
    last_result: dict | None = None
    while attempt <= max_retries:
        start = time.time()
        try:
            result = process_document(str(pdf_path), filename=pdf_path.name)
        except Exception as exc:  # defensive: pipeline should not raise, but just in case
            result = {
                "filename": pdf_path.name,
                "classification": None,
                "extraction": {},
                "review_status": "FAILED",
                "error": f"uncaught: {exc}",
                "total_duration_ms": round((time.time() - start) * 1000, 1),
            }

        last_result = result
        if not _is_retryable(result):
            return result

        attempt += 1
        if attempt > max_retries:
            break
        # Exponential backoff with jitter — spreads retries so the whole pool
        # doesn't hammer OpenRouter at the exact same moment after a 429.
        delay = base_backoff * (2 ** (attempt - 1))
        delay += random.uniform(0, base_backoff)
        logger.warning(
            "Retry %d/%d for %s after %.1fs (error: %s)",
            attempt, max_retries, pdf_path.name, delay, result.get("error"),
        )
        time.sleep(delay)

    return last_result  # type: ignore[return-value]


def _slim_result(pdf_path: Path, input_root: Path, result: dict) -> dict:
    """Project process_document output into a stable report shape."""
    try:
        rel = str(pdf_path.relative_to(input_root))
    except ValueError:
        rel = str(pdf_path)
    return {
        "relative_path": rel,
        "filename": result.get("filename") or pdf_path.name,
        "classification": result.get("classification"),
        "confidence": result.get("confidence"),
        "method": result.get("method"),
        "review_status": result.get("review_status"),
        "used_vision": result.get("used_vision"),
        "extraction": result.get("extraction") or {},
        "error": result.get("error"),
        "total_duration_ms": result.get("total_duration_ms"),
    }


def _summarize(items: list[dict]) -> dict:
    total = len(items)
    succeeded = sum(1 for r in items if not r.get("error") and r.get("review_status") != "FAILED")
    failed = sum(1 for r in items if r.get("error") or r.get("review_status") == "FAILED")
    review = sum(1 for r in items if r.get("review_status") in ("REVIEW", "NEEDS_CHECK"))
    cats: dict[str, int] = {}
    for r in items:
        cat = r.get("classification") or "UNKNOWN"
        cats[cat] = cats.get(cat, 0) + 1
    durations = [r.get("total_duration_ms") for r in items if isinstance(r.get("total_duration_ms"), (int, float))]
    avg_ms = round(sum(durations) / len(durations), 1) if durations else 0
    return {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "review_flagged": review,
        "categories": cats,
        "avg_duration_ms": avg_ms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Parallel vision pipeline runner")
    parser.add_argument("--input", required=True, help="Input folder (recurses into subfolders)")
    parser.add_argument("--workers", type=int, default=8, help="Thread pool size (default 8)")
    parser.add_argument("--output", help="Output JSON report path (default: reports/vision_run_<ts>.json)")
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    parser.add_argument("--base-backoff", type=float, default=DEFAULT_BASE_BACKOFF)
    parser.add_argument("--limit", type=int, default=0, help="Stop after N PDFs (0 = all)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    setup_logging()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    input_root = Path(args.input).resolve()
    pdfs = _discover_pdfs(input_root)
    if args.limit:
        pdfs = pdfs[: args.limit]

    if not pdfs:
        logger.error("No PDFs found under %s", input_root)
        return 1

    output_path = Path(args.output) if args.output else (
        _REPO_ROOT / "reports" / f"vision_run_{int(time.time())}.json"
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Starting batch: %d PDFs, workers=%d, max_retries=%d, output=%s",
        len(pdfs), args.workers, args.max_retries, output_path,
    )

    started = time.time()
    items: list[dict] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        future_to_path = {
            pool.submit(_process_with_retry, pdf, args.max_retries, args.base_backoff): pdf
            for pdf in pdfs
        }
        for future in as_completed(future_to_path):
            pdf_path = future_to_path[future]
            try:
                raw = future.result()
            except Exception as exc:
                raw = {
                    "filename": pdf_path.name,
                    "error": f"future_failed: {exc}",
                    "review_status": "FAILED",
                }
            slim = _slim_result(pdf_path, input_root, raw)
            items.append(slim)
            completed += 1
            status = "OK" if not slim.get("error") else "ERR"
            logger.info(
                "[%d/%d] %s %s -> %s (%sms)",
                completed, len(pdfs), status,
                slim.get("relative_path"),
                slim.get("classification"),
                slim.get("total_duration_ms"),
            )

    elapsed = time.time() - started
    summary = _summarize(items)
    report = {
        "input_root": str(input_root),
        "workers": args.workers,
        "total_pdfs": len(pdfs),
        "elapsed_seconds": round(elapsed, 1),
        "summary": summary,
        "results": items,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(
        "Batch done in %.1fs: ok=%d failed=%d review=%d -> %s",
        elapsed, summary["succeeded"], summary["failed"], summary["review_flagged"], output_path,
    )
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
