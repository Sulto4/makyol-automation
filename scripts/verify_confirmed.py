#!/usr/bin/env python3
"""Deep verification: filter false positives from batch reports, keep only confirmed issues."""
import json
import re
import sys
import requests
from collections import Counter

sys.path.insert(0, "/app")
from pipeline.text_extraction import extract_text_from_pdf

BACKEND = "http://backend:3000"

def load_all_issues():
    all_issues = []
    for rpath in [
        "/app/scripts/verify_batch1_report.json",
        "/app/scripts/batch2_report.json",
        "/app/scripts/batch3_report.json",
        "/app/scripts/batch4_report.json",
        "/app/scripts/batch5_report.json",
    ]:
        try:
            with open(rpath) as f:
                data = json.load(f)
                all_issues.extend(data.get("errors", []) or data.get("issues", []))
        except Exception:
            pass
    return all_issues


def value_in_text(value, text_lower, field):
    """Multi-strategy check if extracted value appears in document text."""
    if not value or not text_lower:
        return False

    val_lower = str(value).lower().strip()

    # Direct substring
    if val_lower in text_lower:
        return True

    # Company names: strip legal suffixes
    if field in ("companie", "producator"):
        cleaned = re.sub(r"\s*(s\.?r\.?l\.?|s\.?a\.?|s\.?c\.?)\s*$", "", val_lower, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^s\.?c\.?\s+", "", cleaned, flags=re.IGNORECASE).strip()
        if len(cleaned) > 3 and cleaned in text_lower:
            return True
        words = [w for w in cleaned.split() if len(w) > 3]
        if words and all(w in text_lower for w in words):
            return True

    # Addresses: check key parts
    if field == "adresa_producator":
        parts = [p.strip() for p in re.split(r"[,;]", val_lower) if len(p.strip()) > 3]
        if parts and sum(1 for p in parts if p in text_lower) >= max(1, len(parts) * 0.5):
            return True

    # Dates: try variant formats
    if field == "data_expirare":
        m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", str(value))
        if m:
            d, mo, y = m.groups()
            months = {
                "01": "ianuarie", "02": "februarie", "03": "martie", "04": "aprilie",
                "05": "mai", "06": "iunie", "07": "iulie", "08": "august",
                "09": "septembrie", "10": "octombrie", "11": "noiembrie", "12": "decembrie",
            }
            variants = [
                f"{d}.{mo}.{y}", f"{d}/{mo}/{y}", f"{int(d)}.{int(mo)}.{y}",
                f"{int(d)} {months.get(mo.zfill(2), '')} {y}",
            ]
            if any(v.lower() in text_lower for v in variants if v):
                return True

    return False


def main():
    all_issues = load_all_issues()
    print(f"Total raw issues from reports: {len(all_issues)}", flush=True)

    confirmed = []
    false_positives = 0
    skipped = 0

    for idx, issue in enumerate(all_issues):
        doc_id = issue.get("doc_id")
        field = issue.get("field")
        issue_type = issue.get("issue")

        if not doc_id or not field:
            skipped += 1
            continue

        if (idx + 1) % 50 == 0:
            print(f"  Processing {idx+1}/{len(all_issues)}...", flush=True)

        try:
            resp = requests.get(f"{BACKEND}/api/documents/{doc_id}", timeout=5)
            if resp.status_code != 200:
                skipped += 1
                continue
            doc_data = resp.json()
            doc = doc_data.get("document", {})
            ext = doc_data.get("extraction") or {}
        except Exception:
            skipped += 1
            continue

        file_path = "/app/" + doc.get("file_path", "")
        try:
            text = extract_text_from_pdf(file_path)
        except Exception:
            text = ""

        if not text or len(text) < 20:
            skipped += 1
            continue

        text_lower = text.lower()
        current_value = ext.get(field)
        category = doc.get("categorie", "")
        filename = doc.get("original_filename", "")

        if issue_type == "SUSPICIOUS":
            if current_value is None:
                false_positives += 1
                continue
            if value_in_text(current_value, text_lower, field):
                false_positives += 1
                continue
            confirmed.append({
                "doc_id": doc_id,
                "filename": filename,
                "category": category,
                "field": field,
                "issue": "WRONG_VALUE",
                "extracted": str(current_value)[:120],
            })

        elif issue_type == "MISSED":
            if current_value is not None:
                false_positives += 1
                continue
            # Skip legitimately NULL fields
            legit_null = (
                (field == "material" and category in ("CUI", "ISO", "ALTELE"))
                or (field == "data_expirare" and category in ("FISA_TEHNICA", "CUI", "ALTELE", "DECLARATIE_PERFORMANTA"))
                or (field in ("producator", "adresa_producator") and category in ("CUI", "ALTELE"))
            )
            if legit_null:
                false_positives += 1
                continue

            has_data = False
            if field == "data_expirare":
                has_data = bool(re.search(r"valabil[aă]?\s+(?:pân[aă]\s+la\s+)?(?:data\s+de\s+)?\d", text_lower))
            elif field == "companie":
                has_data = bool(re.search(r"s\.?c\.?\s+\w{3,}.*?s\.?r\.?l|s\.?c\.?\s+\w{3,}.*?s\.?a", text_lower))
            elif field == "adresa_producator":
                has_data = bool(re.search(r"(?:str\.?|strada|b-dul|calea)\s+\w+.*?(?:nr\.?|numar)", text_lower))
            elif field == "material":
                has_data = bool(re.search(r"(?:tev[ie]|fitinguri|garnitur|robinet|material|produs)", text_lower))
            elif field == "producator":
                has_data = bool(re.search(r"(?:producator|manufacturer|fabricat)\s*:?\s*\w", text_lower))

            if has_data:
                confirmed.append({
                    "doc_id": doc_id,
                    "filename": filename,
                    "category": category,
                    "field": field,
                    "issue": "MISSED",
                    "extracted": "NULL",
                })
            else:
                false_positives += 1

    print(f"\nFalse positives filtered: {false_positives}", flush=True)
    print(f"Skipped (no file/text): {skipped}", flush=True)
    print(f"CONFIRMED issues: {len(confirmed)}", flush=True)

    field_counts = Counter(f"{i['field']}:{i['issue']}" for i in confirmed)
    cat_counts = Counter(i["category"] for i in confirmed)

    print("\nBY FIELD:", flush=True)
    for k, v in field_counts.most_common():
        print(f"  {k}: {v}", flush=True)

    print("\nBY CATEGORY:", flush=True)
    for k, v in cat_counts.most_common():
        print(f"  {k}: {v}", flush=True)

    with open("/app/scripts/confirmed_issues_report.json", "w") as f:
        json.dump({
            "total_raw": len(all_issues),
            "false_positives": false_positives,
            "skipped": skipped,
            "confirmed": len(confirmed),
            "issues": confirmed,
            "by_field": dict(field_counts),
            "by_category": dict(cat_counts),
        }, f, indent=2, ensure_ascii=False)

    print(f"\nReport saved to /app/scripts/confirmed_issues_report.json", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("CONFIRMED ISSUES", flush=True)
    print("=" * 70, flush=True)
    for i, issue in enumerate(confirmed, 1):
        print(
            f"{i:3d}. [{issue['doc_id']}] {issue['filename'][:42]:42s} "
            f"| {issue['category']:22s} | {issue['field']:18s} "
            f"| {issue['issue']:11s} | {issue['extracted'][:50]}",
            flush=True,
        )


if __name__ == "__main__":
    main()
