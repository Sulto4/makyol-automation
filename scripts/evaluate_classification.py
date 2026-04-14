#!/usr/bin/env python3
"""
Evaluate classification accuracy against ground truth documents.

Reads PDFs from Fisiere Makyol Clasificate (folder name = true category),
runs each through the pipeline's classify_document(), and reports accuracy.

Usage (from project root):
    docker exec pdfextractor-pipeline python3 /app/scripts/evaluate_classification.py
"""

import os
import sys
import json
import time
from collections import defaultdict
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, "/app")

from pipeline import process_document
from pipeline.classification import classify_document
from pipeline.text_extraction import extract_text_from_pdf

# Ground truth: folder name → category
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
    "Declaratie de Performanta": "DECLARATIE_PERFORMANTA",
    "Declaratii conformitate": "DECLARATIE_CONFORMITATE",
    "Fisa Tehnica": "FISA_TEHNICA",
    "Iso": "ISO",
    "Z.Altele": "ALTELE",
}

BASE_DIR = "/app/pachete_clasificate"


def load_ground_truth():
    """Load all PDFs with their true categories from folder structure."""
    documents = []
    for folder_name, category in FOLDER_TO_CATEGORY.items():
        folder_path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(folder_path):
            continue
        for f in sorted(os.listdir(folder_path)):
            if f.lower().endswith('.pdf'):
                documents.append({
                    "filepath": os.path.join(folder_path, f),
                    "filename": f,
                    "true_category": category,
                })
    return documents


def run_classification_eval():
    """Run classification on all ground truth documents and report accuracy."""
    documents = load_ground_truth()

    if not documents:
        print(f"ERROR: No documents found in {BASE_DIR}")
        print("Make sure the classified documents folder is mounted.")
        return

    print(f"\n{'='*80}")
    print(f"CLASSIFICATION EVALUATION")
    print(f"{'='*80}")
    print(f"Documents: {len(documents)}")
    print()

    correct = 0
    total = 0
    errors = []
    category_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    method_counts = defaultdict(int)

    for i, doc in enumerate(documents):
        total += 1
        filename = doc["filename"]
        true_cat = doc["true_category"]

        try:
            text = extract_text_from_pdf(doc["filepath"])
            category, confidence, method = classify_document(filename, text)
        except Exception as e:
            category = "ERROR"
            confidence = 0
            method = f"error: {e}"

        is_correct = category == true_cat
        category_stats[true_cat]["total"] += 1
        method_counts[method] += 1

        if is_correct:
            correct += 1
            category_stats[true_cat]["correct"] += 1
            mark = "OK"
        else:
            mark = "XX"
            errors.append({
                "filename": filename,
                "true": true_cat,
                "predicted": category,
                "confidence": confidence,
                "method": method,
            })

        print(f"  [{i+1:3d}/{len(documents)}] {mark} {filename[:55]:55s} "
              f"TRUE={true_cat:28s} PRED={category:28s} [{method}]", flush=True)

    accuracy = correct / total * 100 if total else 0

    print(f"\n{'='*80}")
    print(f"RESULTS: {correct}/{total} = {accuracy:.1f}%")
    print(f"{'='*80}")

    print(f"\nMethods used:")
    for m, c in sorted(method_counts.items(), key=lambda x: -x[1]):
        print(f"  {m:25s}: {c:3d} ({c/total*100:.0f}%)")

    print(f"\n{'Category':<35s} {'Score':>10s} {'Acc':>7s}")
    print("-" * 55)
    for cat in sorted(category_stats.keys()):
        s = category_stats[cat]
        acc = s["correct"] / s["total"] * 100 if s["total"] else 0
        mark = "OK" if acc == 100 else "!!"
        print(f"  {cat:<33s} {s['correct']:>3d}/{s['total']:<3d}   {acc:>5.1f}% {mark}")

    if errors:
        print(f"\n{'='*80}")
        print(f"MISCLASSIFIED ({len(errors)}):")
        print(f"{'='*80}")
        for e in errors:
            print(f"  {e['filename'][:60]}")
            print(f"    TRUE: {e['true']:30s} PRED: {e['predicted']}")
            print(f"    Method: {e['method']} | Conf: {e['confidence']:.2f}")
            print()

    # Save results to JSON
    results_path = "/app/classification_eval_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "errors": errors,
            "category_stats": {k: dict(v) for k, v in category_stats.items()},
            "method_counts": dict(method_counts),
        }, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {results_path}")


if __name__ == "__main__":
    run_classification_eval()
