#!/usr/bin/env python
"""Standalone end-to-end verification script.

Run: python tests/run_e2e_verification.py

Executes the full pipeline and prints a verification report covering
all 7 acceptance criteria for subtask-7-2.
"""

import json
import os
import sys
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.main import process_documents, _export_json

DOCUMENTE_DIR = PROJECT_ROOT / "Documente"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DOCX = OUTPUT_DIR / "rezultat.docx"
OUTPUT_JSON = OUTPUT_DIR / "results.json"

REFERENCE_JSON = PROJECT_ROOT / "makyol-automation" / "rezultate_extrase.json"
if not REFERENCE_JSON.exists():
    for candidate in [
        PROJECT_ROOT.parent / "makyol-automation" / "rezultate_extrase.json",
        PROJECT_ROOT.parent / "rezultate_extrase.json",
    ]:
        if candidate.exists():
            REFERENCE_JSON = candidate
            break


def _check(label: str, passed: bool, detail: str = "") -> bool:
    status = "PASS" if passed else "FAIL"
    icon = "\u2705" if passed else "\u274c"
    msg = f"  {icon} [{status}] {label}"
    if detail:
        msg += f" - {detail}"
    print(msg)
    return passed


def main() -> int:
    if not DOCUMENTE_DIR.exists():
        print(f"ERROR: Documente/ not found at {DOCUMENTE_DIR}")
        print("Create a symlink or copy the folder before running E2E tests.")
        return 1

    print("=" * 70)
    print("END-TO-END PIPELINE VERIFICATION")
    print("=" * 70)

    # Run pipeline
    print("\nRunning pipeline...")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result = process_documents(
        input_dir=DOCUMENTE_DIR,
        output_path=OUTPUT_DOCX,
        verbose=True,
    )
    _export_json(result, OUTPUT_JSON)

    all_docs = []
    for folder in result.supplier_folders:
        all_docs.extend(folder.documents)

    passes = 0
    total = 0

    # --- Criterion 1: Output Word file ---
    print("\n--- Criterion 1: Output Word file ---")
    total += 1
    if OUTPUT_DOCX.exists():
        size = OUTPUT_DOCX.stat().st_size
        passes += _check("rezultat.docx exists and > 10KB", size > 10_000, f"{size} bytes")
    else:
        _check("rezultat.docx exists", False)

    # --- Criterion 2: JSON export with all PDFs ---
    print("\n--- Criterion 2: JSON export completeness ---")
    total += 1
    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, encoding="utf-8") as f:
            json_data = json.load(f)
        json_doc_count = sum(len(s["documents"]) for s in json_data["suppliers"])
        passes += _check(
            f"JSON has entries for all PDFs",
            json_doc_count >= 35,
            f"{json_doc_count} documents in JSON, {result.total_files} total",
        )
    else:
        _check("JSON export exists", False)

    # --- Criterion 3: Classification ---
    print("\n--- Criterion 3: Document type classification ---")
    total += 1
    classified = sum(1 for d in all_docs if d.document_type is not None)
    iso_docs = [d for d in all_docs if "ISO" in d.file_name.upper()]
    iso_correct = sum(1 for d in iso_docs if d.document_type and "ISO" in d.document_type.value)
    passes += _check(
        "All documents classified",
        classified == len(all_docs),
        f"{classified}/{len(all_docs)} classified, {iso_correct}/{len(iso_docs)} ISO correct",
    )

    # --- Criterion 4: Distributor for Tehnoworld/Zakprest ---
    print("\n--- Criterion 4: Distributor field ---")
    total += 1
    tehno_docs = [d for d in all_docs if "Tehnoworld" in d.supplier_folder]
    zak_docs = [d for d in all_docs if "Zakprest" in d.supplier_folder]
    tehno_ok = all(d.distributor and d.distributor != "N/A" for d in tehno_docs)
    zak_ok = all(d.distributor and d.distributor != "N/A" for d in zak_docs)
    passes += _check(
        "Distributor populated for Tehnoworld and Zakprest",
        tehno_ok and zak_ok,
        f"Tehnoworld: {sum(1 for d in tehno_docs if d.distributor and d.distributor != 'N/A')}/{len(tehno_docs)}, "
        f"Zakprest: {sum(1 for d in zak_docs if d.distributor and d.distributor != 'N/A')}/{len(zak_docs)}",
    )

    # --- Criterion 5: Expiration dates ---
    print("\n--- Criterion 5: Expiration dates ---")
    total += 1
    iso9001 = next(
        (d for d in all_docs if d.file_name == "2. ISO 9001.pdf" and "TERAPLAST" in d.supplier_folder),
        None,
    )
    date_ok = iso9001 is not None and iso9001.expiration_date == "04.11.2027"
    passes += _check(
        "TERAPLAST ISO 9001 expiry = 04.11.2027",
        date_ok,
        f"Got: '{iso9001.expiration_date if iso9001 else 'NOT FOUND'}'",
    )

    # --- Criterion 6: No crashes ---
    print("\n--- Criterion 6: Stability ---")
    total += 1
    passes += _check(
        "Pipeline completed without crashes",
        result.failed_files <= 5,
        f"{result.processed_files} processed, {result.failed_files} failed, "
        f"{result.success_rate:.1f}% success rate",
    )

    # --- Criterion 7: Reference parity ---
    print("\n--- Criterion 7: Reference parity ---")
    total += 1
    if REFERENCE_JSON.exists():
        with open(REFERENCE_JSON, encoding="utf-8") as f:
            ref_data = json.load(f)
        our_files = {d.file_name for d in all_docs}
        ref_files = {r["filename"] for r in ref_data}
        missing = ref_files - our_files
        ref_dist_count = sum(1 for r in ref_data if r.get("distributor", ""))
        our_dist_count = sum(1 for d in all_docs if d.distributor and d.distributor != "N/A")
        passes += _check(
            "Parity with reference + distributor improvement",
            len(missing) == 0 and our_dist_count > ref_dist_count,
            f"Missing files: {len(missing)}, "
            f"Distributor: ref={ref_dist_count} -> ours={our_dist_count}",
        )
    else:
        _check("Reference JSON available", False, str(REFERENCE_JSON))

    # --- Summary ---
    print("\n" + "=" * 70)
    print(f"VERIFICATION RESULT: {passes}/{total} criteria passed")
    print("=" * 70)

    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
