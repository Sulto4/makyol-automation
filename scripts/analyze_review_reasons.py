"""Re-run validator on current DB rows and aggregate review reasons.

Works around the pre-P2 reality that:
  (a) the backend was not persisting pipeline's review_status, so
      documents.review_status is 'OK' everywhere even for the 94 docs we saw
      flagged REVIEW during the test run;
  (b) review reasons were never captured anywhere.

Strategy: pull every completed document + its extraction from Postgres (via
psql subprocess to avoid psycopg2 dep), feed the extraction dict to
pipeline.validation._collect_issues, and tally. This gives us the
counterfactual breakdown of what the validator *would* flag today, which is
what we actually need to decide where Pachet 3 should focus.
"""

from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/app")

from pipeline.validation import _collect_issues


# Input is a CSV dump produced by `psql \copy ... TO STDOUT WITH CSV HEADER`
# from the host; the pipeline container doesn't have psql, so we read the
# pre-dumped file instead of shelling out.
DUMP_CSV = Path("/app/scripts/_docs_dump.csv")


def _fetch_rows() -> list[dict]:
    if not DUMP_CSV.exists():
        print(f"Missing dump file: {DUMP_CSV}", file=sys.stderr)
        print("Run this first from host:", file=sys.stderr)
        print(
            "  docker exec pdfextractor-postgres psql ... \\copy (...) TO STDOUT WITH CSV HEADER > _docs_dump.csv",
            file=sys.stderr,
        )
        sys.exit(1)
    with DUMP_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [{k: (v if v else None) for k, v in row.items()} for row in reader]


# Map raw validator messages to a short, aggregatable reason key.
# (The validator returns human text like "data_expirare is not in DD.MM.YYYY
# format: '14 februarie 2027'" — group by pattern, not by payload, otherwise
# every doc becomes its own bucket.)
_REASON_PATTERNS = [
    (re.compile(r"^(\w+) is not in DD\.MM\.YYYY format"), "date_format"),
    (re.compile(r"^(\w+) exceeds \d+ chars"), "length_exceeded"),
    (re.compile(r"^(\w+) appears to be a comma-separated list"), "comma_list"),
    (re.compile(r"^material is too generic"), "material_generic"),
    (re.compile(r"^material appears to be Chinese-only"), "material_chinese"),
    (re.compile(r"^(\w+) contains repeated segments"), "repeated_segments"),
]


def _bucket(issue: str) -> tuple[str, str | None]:
    """Return (reason_key, field_name_if_known)."""
    for pat, key in _REASON_PATTERNS:
        m = pat.match(issue)
        if m:
            field = m.group(1) if m.groups() else None
            return key, field
    return "other", None


def main() -> int:
    rows = _fetch_rows()
    print(f"Loaded {len(rows)} completed documents from DB.\n")

    total_ok = 0
    total_review = 0
    reason_counts: Counter[str] = Counter()          # reason key -> count
    reason_field_counts: Counter[str] = Counter()     # "key:field"
    reason_by_category: dict[str, Counter] = defaultdict(Counter)
    examples: dict[str, list[str]] = defaultdict(list)

    per_doc_rows: list[dict] = []

    for r in rows:
        # _collect_issues expects the extraction dict; use the 5 main fields
        extraction = {
            "companie": r.get("companie"),
            "producator": r.get("producator"),
            "distribuitor": r.get("distribuitor"),
            "material": r.get("material"),
            "data_expirare": r.get("data_expirare"),
            "adresa_producator": r.get("adresa_producator"),
        }
        issues = _collect_issues(extraction)
        if issues:
            total_review += 1
            reasons_this_doc = []
            for iss in issues:
                key, field = _bucket(iss)
                reason_counts[key] += 1
                if field:
                    reason_field_counts[f"{key}:{field}"] += 1
                reasons_this_doc.append(key)
                cat = r.get("categorie") or "UNKNOWN"
                reason_by_category[cat][key] += 1
                if len(examples[key]) < 5:
                    examples[key].append(
                        f"[{r['id']}] {(r.get('original_filename') or '')[:55]!r} "
                        f"({cat}): {iss[:80]}"
                    )
            per_doc_rows.append({
                "id": r["id"],
                "categorie": r.get("categorie"),
                "filename": r.get("original_filename"),
                "reasons": ",".join(sorted(set(reasons_this_doc))),
                "issue_count": len(issues),
                "raw_issues": " | ".join(issues),
            })
        else:
            total_ok += 1

    # ---- Console summary ----
    print(f"Breakdown (what validator WOULD flag on current DB rows):")
    print(f"  OK:     {total_ok}")
    print(f"  REVIEW: {total_review}  ({100*total_review/len(rows):.1f}%)")
    print()
    print("Top reasons (count of distinct issues, a doc can contribute multiple):")
    for key, count in reason_counts.most_common():
        print(f"  {count:4d}  {key}")
    print()
    print("Top reason:field combinations:")
    for kf, count in reason_field_counts.most_common(12):
        print(f"  {count:4d}  {kf}")
    print()
    print("Per-category breakdown (reasons × categorie):")
    for cat in sorted(reason_by_category):
        ctr = reason_by_category[cat]
        parts = ", ".join(f"{k}={v}" for k, v in ctr.most_common())
        print(f"  {cat:28s} {parts}")
    print()
    print("Examples per reason (up to 5 each):")
    for key in reason_counts:
        print(f"\n  === {key} ===")
        for ex in examples[key]:
            print(f"     {ex}")

    # ---- CSV output ----
    out_dir = Path("/app/scripts")
    csv_path = out_dir / "review_reasons_breakdown.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id", "categorie", "filename", "reasons", "issue_count", "raw_issues"])
        w.writeheader()
        w.writerows(per_doc_rows)
    print(f"\nPer-doc CSV: {csv_path} ({len(per_doc_rows)} rows)")

    # ---- JSON summary ----
    json_path = out_dir / "review_reasons_summary.json"
    summary = {
        "total_documents": len(rows),
        "would_be_ok": total_ok,
        "would_be_review": total_review,
        "reason_counts": dict(reason_counts),
        "reason_field_counts": dict(reason_field_counts),
        "reason_by_category": {k: dict(v) for k, v in reason_by_category.items()},
        "examples": {k: v for k, v in examples.items()},
    }
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Summary JSON: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
