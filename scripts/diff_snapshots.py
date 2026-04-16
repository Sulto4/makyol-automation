"""Compare pre-vision vs post-vision extraction snapshots.

Matches rows by original_filename. For filenames with duplicates on both
sides, pairs them in order. Reports field-level diffs for classification
(categorie, confidence, metoda_clasificare, review_status) and extraction
(companie, material, data_expirare, producator, adresa_producator,
extraction_model).

Output:
 - JSON: scripts/vision_diff_report.json (full structured diff)
 - Markdown: scripts/vision_diff_report.md (human-readable summary)
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PRE_CSV = REPO / "scripts" / "extraction_snapshot_before_rerun.csv"
POST_CSV = REPO / "scripts" / "extraction_snapshot_after_vision.csv"
OUT_JSON = REPO / "scripts" / "vision_diff_report.json"
OUT_MD = REPO / "scripts" / "vision_diff_report.md"

# Fields we compare. Order matters for report readability.
CLASSIFICATION_FIELDS = ("categorie", "confidence", "metoda_clasificare", "review_status")
EXTRACTION_FIELDS = (
    "companie", "material", "data_expirare",
    "producator", "adresa_producator", "extraction_model",
)
ALL_FIELDS = CLASSIFICATION_FIELDS + EXTRACTION_FIELDS


def _norm(v):
    if v is None:
        return ""
    s = str(v).strip()
    # Treat empty strings and common nulls as the same
    if s == "" or s.lower() in ("none", "null", "n/a"):
        return ""
    # Collapse internal newlines/tabs for comparison readability
    return " ".join(s.split())


def load_csv(path: Path) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("original_filename") or "").strip()
            if not name:
                continue
            groups[name].append(row)
    return groups


def pair_rows(pre_rows: list[dict], post_rows: list[dict]) -> list[tuple[dict | None, dict | None]]:
    """Pair duplicates in order; unmatched leftovers paired with None."""
    n = max(len(pre_rows), len(post_rows))
    pairs = []
    for i in range(n):
        pre = pre_rows[i] if i < len(pre_rows) else None
        post = post_rows[i] if i < len(post_rows) else None
        pairs.append((pre, post))
    return pairs


def diff_pair(pre: dict, post: dict) -> dict:
    """Return dict of field -> (pre_value, post_value) where they differ."""
    out = {}
    for f in ALL_FIELDS:
        pv = _norm(pre.get(f))
        ov = _norm(post.get(f))
        if pv != ov:
            out[f] = {"pre": pre.get(f), "post": post.get(f)}
    return out


def classify_diff(d: dict) -> str:
    """Bucket the kind of difference for aggregate stats."""
    if not d:
        return "identical"
    fields = set(d.keys())
    class_changed = bool(fields & set(CLASSIFICATION_FIELDS))
    extract_changed = bool(fields & set(EXTRACTION_FIELDS))
    if class_changed and extract_changed:
        return "both_changed"
    if class_changed:
        return "classification_only"
    return "extraction_only"


def main() -> int:
    if not PRE_CSV.exists() or not POST_CSV.exists():
        print("Missing snapshot file(s)", file=sys.stderr)
        return 1

    pre = load_csv(PRE_CSV)
    post = load_csv(POST_CSV)

    pre_names = set(pre)
    post_names = set(post)
    common = pre_names & post_names
    only_pre = pre_names - post_names
    only_post = post_names - pre_names

    diffs = []
    identical_count = 0
    kind_counts: dict[str, int] = defaultdict(int)
    category_transitions: dict[str, int] = defaultdict(int)

    for name in sorted(common):
        for pre_row, post_row in pair_rows(pre[name], post[name]):
            if pre_row is None or post_row is None:
                diffs.append({
                    "filename": name,
                    "kind": "unpaired_duplicate",
                    "pre_present": pre_row is not None,
                    "post_present": post_row is not None,
                })
                kind_counts["unpaired_duplicate"] += 1
                continue
            d = diff_pair(pre_row, post_row)
            if not d:
                identical_count += 1
                continue
            kind = classify_diff(d)
            kind_counts[kind] += 1
            entry = {
                "filename": name,
                "kind": kind,
                "pre_id": pre_row.get("id"),
                "post_id": post_row.get("id"),
                "fields": d,
            }
            diffs.append(entry)
            if "categorie" in d:
                key = f"{pre_row.get('categorie') or '∅'} → {post_row.get('categorie') or '∅'}"
                category_transitions[key] += 1

    # Filenames that appear only in one side
    for name in sorted(only_pre):
        diffs.append({
            "filename": name,
            "kind": "only_in_pre",
            "count_pre": len(pre[name]),
        })
        kind_counts["only_in_pre"] += 1
    for name in sorted(only_post):
        diffs.append({
            "filename": name,
            "kind": "only_in_post",
            "count_post": len(post[name]),
        })
        kind_counts["only_in_post"] += 1

    summary = {
        "pre_total_rows": sum(len(v) for v in pre.values()),
        "post_total_rows": sum(len(v) for v in post.values()),
        "pre_distinct_filenames": len(pre_names),
        "post_distinct_filenames": len(post_names),
        "common_filenames": len(common),
        "only_in_pre_filenames": len(only_pre),
        "only_in_post_filenames": len(only_post),
        "identical_paired_rows": identical_count,
        "diff_kind_counts": dict(kind_counts),
        "category_transitions_top": dict(sorted(
            category_transitions.items(), key=lambda kv: -kv[1]
        )[:20]),
    }

    report = {"summary": summary, "diffs": diffs}
    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Markdown summary
    lines = []
    lines.append("# Vision vs Text-based Extraction Diff Report\n")
    lines.append("## Summary\n")
    for k, v in summary.items():
        if isinstance(v, dict):
            lines.append(f"- **{k}**:")
            for kk, vv in v.items():
                lines.append(f"  - `{kk}`: {vv}")
        else:
            lines.append(f"- **{k}**: {v}")
    lines.append("")

    # Show up to N diffs per kind
    by_kind: dict[str, list[dict]] = defaultdict(list)
    for d in diffs:
        by_kind[d["kind"]].append(d)
    for kind, items in sorted(by_kind.items()):
        lines.append(f"\n## Kind: `{kind}` ({len(items)} entries)\n")
        for item in items[:200]:  # cap per kind
            lines.append(f"### `{item['filename']}`")
            if "fields" in item:
                for field, vals in item["fields"].items():
                    pre_v = (vals.get("pre") or "").replace("\n", " ⏎ ")
                    post_v = (vals.get("post") or "").replace("\n", " ⏎ ")
                    lines.append(f"- **{field}**")
                    lines.append(f"  - pre:  `{pre_v}`")
                    lines.append(f"  - post: `{post_v}`")
            else:
                lines.append(f"  - {item}")
            lines.append("")

    with OUT_MD.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nFull JSON: {OUT_JSON}")
    print(f"Markdown:   {OUT_MD}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
