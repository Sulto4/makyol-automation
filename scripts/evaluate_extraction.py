#!/usr/bin/env python3
"""
Evaluate extraction quality on sample documents.

For each category, takes a few sample documents, runs full pipeline,
then compares extracted fields against the actual PDF text to assess quality.

Usage (from project root):
    docker exec pdfextractor-pipeline python3 /app/scripts/evaluate_extraction.py
"""

import os
import sys
import json
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "/app")

from pipeline import process_document
from pipeline.text_extraction import extract_text_from_pdf

FOLDER_TO_CATEGORY = {
    "Agrement": "AGREMENT",
    "Autorizatii de comercializare sau de distributie": "AUTORIZATIE_DISTRIBUTIE",
    "Aviz Tehnic + Agrement": "AVIZ_TEHNIC_SI_AGREMENT",
    "Aviz tehnic": "AVIZ_TEHNIC",
    "Avize Sanitare": "AVIZ_SANITAR",
    "CE": "CE",
    "Certificat Calitate": "CERTIFICAT_CALITATE",
    "Certificat Garantie": "CERTIFICAT_GARANTIE",
    "Cui": "CUI",
    "Declaratii conformitate": "DECLARATIE_CONFORMITATE",
    "Fisa Tehnica": "FISA_TEHNICA",
    "Iso": "ISO",
    "Z.Altele": "ALTELE",
}

BASE_DIR = "/app/pachete_clasificate"
SAMPLES_PER_CATEGORY = 2  # Process 2 samples per category for speed

EXTRACTION_FIELDS = [
    "companie", "material", "data_expirare",
    "producator", "distribuitor", "adresa_producator",
]


def run_extraction_eval():
    """Run full pipeline on sample docs and report extraction quality."""
    print(f"\n{'='*80}")
    print(f"EXTRACTION QUALITY EVALUATION")
    print(f"{'='*80}")
    print(f"Samples per category: {SAMPLES_PER_CATEGORY}")
    print()

    total_docs = 0
    total_fields = 0
    filled_fields = 0
    category_results = {}
    all_results = []

    for folder_name, category in sorted(FOLDER_TO_CATEGORY.items()):
        folder_path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(folder_path):
            continue

        pdfs = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')])
        samples = pdfs[:SAMPLES_PER_CATEGORY]

        if not samples:
            continue

        print(f"\n--- {category} ({len(samples)} samples) ---")
        cat_filled = 0
        cat_total = 0

        for pdf_name in samples:
            filepath = os.path.join(folder_path, pdf_name)
            total_docs += 1

            t0 = time.time()
            try:
                result = process_document(filepath, filename=pdf_name)
            except Exception as e:
                print(f"  ERROR processing {pdf_name}: {e}")
                continue
            elapsed = time.time() - t0

            extraction = result.get("extraction", {})
            classified_as = result.get("classification", "?")
            method = result.get("method", "?")
            correct_class = classified_as == category

            # Count filled fields
            doc_filled = []
            doc_null = []
            for field in EXTRACTION_FIELDS:
                total_fields += 1
                cat_total += 1
                val = extraction.get(field)
                if val is not None and str(val).strip():
                    filled_fields += 1
                    cat_filled += 1
                    doc_filled.append(field)
                else:
                    doc_null.append(field)

            # Show document text snippet for manual verification
            text = extract_text_from_pdf(filepath)
            text_preview = text[:300].replace('\n', ' ').strip() if text else "(no text)"

            class_mark = "OK" if correct_class else f"!! ({classified_as})"

            print(f"\n  [{pdf_name[:55]}]")
            print(f"  Class: {class_mark} | Time: {elapsed:.1f}s | Model: {result.get('extraction', {}).get('extraction_model', '?')}")
            print(f"  Filled: {len(doc_filled)}/{len(EXTRACTION_FIELDS)} = {', '.join(doc_filled) if doc_filled else 'NONE'}")
            if doc_null:
                print(f"  Missing: {', '.join(doc_null)}")

            # Show extracted values
            for field in EXTRACTION_FIELDS:
                val = extraction.get(field)
                if val:
                    print(f"    {field:20s}: {str(val)[:100]}")

            # Show text preview for manual checking
            print(f"  Text preview: {text_preview[:200]}...")

            all_results.append({
                "filename": pdf_name,
                "true_category": category,
                "predicted_category": classified_as,
                "correct_classification": correct_class,
                "method": method,
                "extraction": {f: extraction.get(f) for f in EXTRACTION_FIELDS},
                "extraction_model": extraction.get("extraction_model"),
                "filled_count": len(doc_filled),
                "elapsed_s": round(elapsed, 1),
            })

        if cat_total > 0:
            cat_rate = cat_filled / cat_total * 100
            category_results[category] = {"filled": cat_filled, "total": cat_total, "rate": cat_rate}

    # Summary
    fill_rate = filled_fields / total_fields * 100 if total_fields else 0

    print(f"\n{'='*80}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'='*80}")
    print(f"Documents processed: {total_docs}")
    print(f"Overall fill rate:   {filled_fields}/{total_fields} = {fill_rate:.1f}%")
    print()
    print(f"{'Category':<35s} {'Fill Rate':>12s}")
    print("-" * 50)
    for cat in sorted(category_results.keys()):
        r = category_results[cat]
        print(f"  {cat:<33s} {r['filled']:>3d}/{r['total']:<3d} = {r['rate']:>5.1f}%")

    # Save results
    results_path = "/app/extraction_eval_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_docs": total_docs,
            "fill_rate": fill_rate,
            "category_results": category_results,
            "results": all_results,
        }, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    run_extraction_eval()
