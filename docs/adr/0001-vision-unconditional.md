---
status: accepted
date: 2026-04-18
supersedes: —
---

# ADR 0001 — Vision AI aplicat necondiționat la fiecare document

## Context

Pipeline-ul inițial avea extracție text-only (pdfplumber → PyMuPDF → Tesseract → regex), cu Vision AI ca **fallback condiționat** când:
- Textul extras avea sub `MIN_TEXT_LENGTH = 20` caractere (probabil scanat)
- SAU câmpurile-cheie lipseau după text extraction

Problema: condiționarea era imprevizibilă. PDF-uri cu text "curat" dar layout complex (multi-coloană, tabele inserate, fonturi non-standard, semnături grafice) treceau text extraction cu succes aparent dar cu fill-rate slab pe câmpuri. Schimbări minore în PDF (un font diferit) basculau între cele două căi cu rezultate diferite. Fill-rate pe `companie` a oscilat între 40-60% pe setul de 300+ docs.

## Decizie

**Vision AI rulează necondiționat pentru fiecare document.**

```
pipeline/__init__.py:29
_USE_VISION_FOR_ALL = True
```

Fiecare PDF e randat la **300 DPI** prin PyMuPDF (`VISION_DPI` în `pipeline/config.py:114`), primele `(vision_max_pages - 1)` + ultima pagină sunt trimise multimodal la Gemini 2.5 Flash via OpenRouter. Text extraction tot rulează — dar doar ca input pentru classifier (nu pentru extracție). Calea text-AI și regex rămân ca fallback când Vision returnează None sau toate câmpurile sunt null.

## Consecințe

**Pozitive:**
- Output uniform calitativ: ce-ai dat la Vision pentru un doc curat se comportă la fel și pentru unul complicat
- Fill-rate pe `companie` a urcat de la ~40% la ~80% într-un experiment controlat
- Fill-rate pe `data_expirare` a urcat 165 → 179 pe benchmark-ul 328 docs (2026-04-18)
- Cod mai simplu — nu mai avem logică de branching bazată pe euristici text

**Negative:**
- **Cost OpenRouter crește liniar cu numărul de docs.** Un call Vision = ~0.001 USD pe Gemini 2.5 Flash, dar la reprocess-all pe 300 docs devine 0.30 USD per run
- Latență +5-20s/doc față de text-only
- Dependență totală de disponibilitatea OpenRouter. Dacă API-ul pică, cădem pe regex pentru TOT (fill-rate 20-30%)
- Cheia OpenRouter devine infrastructură critică — rotirea ei prost gestionată = toate extragerile se degradează silent

## Cost de reversare

**Imediat.** Flip `_USE_VISION_FOR_ALL = False` → comportamentul condițional vechi revine. Toată logica text-only e încă în `pipeline/extraction.py::extract_document_data` și regex în `pipeline/regex_extraction.py`. Testat prin commentarea flag-ului în dev.

## Referințe

- [extraction-logic.md#extracție-vision-ai-unconditional](../extraction-logic.md#extracție--vision-ai-unconditional)
- [pipeline.md#process_document-flow](../pipeline.md#process_document-flow)
- [configuration.md#hot-reload](../configuration.md#hot-reload) — `ai_model` e hot-reloadabil
