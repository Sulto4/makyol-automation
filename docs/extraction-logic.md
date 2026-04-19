---
title: Logica de clasificare + extracție
scope: extraction-logic
stability: stable
last_verified: 2026-04-19
related:
  - ./pipeline.md
  - ./architecture.md
  - ./database.md
code_refs:
  - pipeline/__init__.py
  - pipeline/classification.py
  - pipeline/country_detector.py
  - pipeline/extraction.py
  - pipeline/vision_fallback.py
  - pipeline/normalization.py
  - pipeline/validation.py
  - pipeline/schemas/knowledge_base.json
---

# Logica de clasificare + extracție

Acest doc explică **deciziile semantice** din pipeline: ce categorii recunoaștem, cum decidem care e care, de ce folosim Vision întotdeauna, ce heuristici ne protejează de ieșiri greșite, și cum normalizăm rezultatele. Pentru structura fișierelor vezi [pipeline.md](./pipeline.md).

## Cele 14 categorii

Definite în `pipeline/classification.py:30` (`VALID_CATEGORIES`):

| # | Categorie | Cu `data_expirare`? | Descriere scurtă |
|---|-----------|:-------------------:|------------------|
| 1 | `ISO` | ✓ | Certificat ISO (9001, 14001, 27001, 45001) |
| 2 | `CE` | ✓ | Marcaj CE / declarație de conformitate europeană |
| 3 | `FISA_TEHNICA` | ✗ | Fișă tehnică produs (nu expiră) |
| 4 | `AGREMENT` | ✓ | Agrement tehnic (valid cu scadență) |
| 5 | `AVIZ_TEHNIC` | ✓ | Aviz tehnic |
| 6 | `AVIZ_SANITAR` | ✓ | Aviz sanitar (Ministerul Sănătății) |
| 7 | `DECLARATIE_CONFORMITATE` | ✓ | Declarație de conformitate |
| 8 | `CERTIFICAT_CALITATE` | ✓ | Certificat de calitate |
| 9 | `AUTORIZATIE_DISTRIBUTIE` | ✓ | Autorizație de distribuție |
| 10 | `CUI` | ✗ | Certificat CUI (date firmă — nu expiră tipic) |
| 11 | `CERTIFICAT_GARANTIE` | ✓ | Certificat de garanție |
| 12 | `DECLARATIE_PERFORMANTA` | ✓ | Declarație de performanță (CPR/DoP) |
| 13 | `AVIZ_TEHNIC_SI_AGREMENT` | ✓ | Document combinat aviz + agrement |
| 14 | `ALTELE` | ✗ | Fallback — nu am identificat |

Frozenset-ul cu categoriile care **pot** avea `data_expirare` e în `pipeline/extraction.py:202` (`CATEGORIES_WITH_DATA_EXPIRARE`). G1 (normalizare) face **drop** pe `data_expirare` pentru celelalte chiar dacă AI returnează o valoare.

## Clasificare — cascade în 3 nivele

`classify_document` la `pipeline/classification.py:635`:

```
Input: filename, text, page_count, has_tables
  ▼
1. classify_by_filename(filename)     [classification.py:168]
     ├─► regex peste ~29 patterns cu confidențe 0.70-0.95
     ├─► patterns high-priority combinate primele (AVIZ_TEHNIC_SI_AGREMENT @ 0.95)
     └─► return (category, conf, "filename_regex") sau None
  ▼
2. classify_by_text(text, page_count, has_tables)   [classification.py:185]
     ├─► rulează DOAR dacă text are >50 chars
     ├─► markeri în primii 500 chars + text complet
     │    "ISO 9001" / "aviz sanitar" / "CE marking" / "WRAS approval" / etc.
     ├─► confidențe 0.85-0.95
     └─► return (category, conf, "text_rules: <marker>") sau None
  ▼
3. Reconciliere filename vs text:
     ├─► ambele la fel → ("filename+text_agree", max conf)
     ├─► text_rules wins cu markeri puternici → ("text_override", conf)
     ├─► filename wins altminteri → ("filename_wins", conf filename)
  ▼
4. classify_by_ai(text, filename)    [classification.py:509]
     ├─► doar dacă nici filename nici text nu au returnat nimic
     ├─► OpenRouter chat completion cu system prompt + VALID_CATEGORIES
     ├─► temperature 0.0 (deterministic)
     └─► return (category, conf, "ai")
  ▼
5. Fallback: ("ALTELE", 0.50, "fallback")
```

**Outputul e `(category, confidence, method)`** — method e stocat în DB la `documents.metoda_clasificare` și e vizibil în UI.

**Methods posibile în DB** (CHECK constraint din migration 006):
`filename_regex`, `text_rules`, `ai`, `text_override`, `vision`, `filename+text_agree`, `filename_wins`, `fallback`.

## Extracție — Vision AI unconditional

`pipeline/__init__.py:29`:

```python
_USE_VISION_FOR_ALL = True
```

> **De ce Vision pe fiecare doc:** PDF-urile din portofoliu sunt eterogene — unele text-native (pdfplumber citește curat), altele scanate, altele cu fonturi non-standard unde OCR Tesseract ghicește fonetic. O condiționare "dacă text e scurt atunci Vision" era predictibilă pentru docs simple dar eșua neașteptat pe layout-uri complicate (multi-coloană, tabele inserate, semnături). Aplicând Vision la tot, outputul devine uniform la +1 call OpenRouter/doc. Costul acceptat; decizie luată când fill-rate pe `companie` a urcat de la ~40% la ~80% într-un experiment. Vezi ADR 0001 (Valul 3).

**Flow-ul extracției** (în `process_document`, `__init__.py:105`):

1. **Vision path (primar):** `extract_with_vision(images, category, filename)` la `vision_fallback.py:194`.
   - Randează PDF-ul la 300 DPI prin `PAGE_RENDER_POOL` (4 workers paraleli)
   - Selectează primele `(vision_max_pages - 1)` pagini + ultima pagină
   - Base64 encode fiecare ca PNG
   - Construiește payload multimodal: `[{type: "text"}, {type: "image_url"} × N]`
   - POST la OpenRouter cu `settings.ai_model` (`google/gemini-2.5-flash` default), temp `0.0`, max_tokens 4096, timeout 120s
   - Parsează răspuns JSON

2. **Text path (retry):** dacă Vision returnează None SAU toate câmpurile-cheie sunt null (`companie`, `material`, `data_expirare`, `producator`, `distribuitor`, `adresa_producator`) și textul are >50 chars:
   - `extract_document_data(text, category, filename)` la `extraction.py:799`
   - Doar text, același model, prompt bazat pe `EXTRACTION_SCHEMA`

3. **Regex path (last-resort):** dacă încă null → `pipeline/regex_extraction.py`. Etichetat `extraction_model = "regex_fallback"`.

## `EXTRACTION_SCHEMA`

`pipeline/extraction.py:34` — dict cu 14 chei (categorii). Fiecare categorie definește:
- `fields` — lista de câmpuri de extras (ex: `["companie", "data_expirare", "standard_iso", "adresa_producator"]`)
- `instructions` — prompt specific categoriei

Example (conceptual):
```json
"ISO": {
  "fields": ["companie", "data_expirare", "standard_iso", "adresa_producator"],
  "instructions": "Extract: certified company name, certificate expiration date, ISO standard (e.g. 9001:2015), manufacturer address..."
}
```

Vision-ul primește prompt-ul categoriei + lista de câmpuri + reguli generale (OCR errors, date formatting, Romanian diacritics, "no Chinese characters", max lengths). Schema-specific text e șablonul peste care AI returnează JSON.

## Heuristici de salvare: G1-G5

Aplicate în `normalize_extraction_result` (`extraction.py:402`) și `process_document` (`__init__.py`).

### G1 — Drop câmpuri invalide per categorie

Pentru categoriile care **nu** au `data_expirare` (FISA_TEHNICA, CUI, ALTELE), câmpul e șters chiar dacă AI returnează o valoare. Previne "o dată întâmplătoare dintr-o fișă tehnică" să contamineze dashboard-ul expirări.

### G2-G3 — OCR fixes + diacritice

- `_fix_ocr_errors()` (`extraction.py:226`) — corectează greșeli comune Tesseract (0↔O, 1↔l, etc.) în câmpuri-text
- `_fix_diacritics()` (`extraction.py:233`) — normalizează variantele de diacritice (ş vs ș cedilla)
- `_clean_company_name()` (`extraction.py:249`) — elimină CUI pattern-uri, SC prefix, SRL/SA suffix normalization

### G4 — Filename-date fallback

În `process_document`, **doar pentru categoriile din `CATEGORIES_WITH_DATA_EXPIRARE`**:

```python
if not extraction.data_expirare:
    candidates = scan_filename_dates(filename)  # date_normalizer.py:405
    if candidates:
        extraction.data_expirare = max(candidates)
```

`scan_filename_dates` recunoaște:
- Formate numerice: `DD.MM.YYYY`, `DD_MM_YYYY`, `DD-MM-YYYY`
- Formate cu luni în română: `"11 noiembrie 2024"`, `"5 martie 2027"`
- Ani 4-digit + 2-digit (cu euristică de prag secol)

**Alege cea mai târzie** — dacă filename are `Certificat_emis_05.03.2024_valid_05.03.2027.pdf`, rezultatul e `2027-03-05`.

### G5 — Suspicious-expiry guard (180 zile)

`pipeline/__init__.py:46`:
```python
_SUSPICIOUS_PAST_EXPIRY_DAYS = 180
```

Dacă `data_expirare` extras e **mai vechi de 180 de zile în trecut** ȘI filename nu confirmă (nu conține aceeași dată sau o dată fără trecut >180 zile):

```python
review_status = "REVIEW"
review_reasons.append({
  "reason": "suspicious_past_expiry",
  "field": "data_expirare",
  "message": "Dată de expirare mult în trecut, fără confirmare din filename. Verificați dacă nu e data emiterii."
})
```

> **De ce 180 zile:** certificatele care au expirat recent (de la câteva zile până la ~6 luni) sunt legitime și trebuie afișate ca expirate fără fricțiune. Pragul la 6 luni prinde cazul frecvent al AI-ului care confundă data de emitere cu data de expirare — "15 ianuarie 2020" apare ca `data_expirare` pentru un doc emis atunci, în timp ce cert-ul expiră în 2023.

## Knowledge base — fuzzy match pentru companii și adrese {#knowledge-base}

`pipeline/schemas/knowledge_base.json` conține 10 companii cunoscute (TERAPLAST, VALROM, REHAU, VALSIR, GEBERIT, WAVIN, PESTAN, ARMACELL, HENKEL, HUAYANG). Pentru fiecare:

```json
{
  "canonical": "TERAPLAST SA",
  "aliases": ["TERAPLAST SA", "TeraPlast SA", "SC TERAPLAST SA", "Teraplast S.A.", ...],
  "cui": "RO3094980",
  "canonical_address": "Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud",
  "address_aliases": [ ... ]
}
```

**Fuzzy match** (`normalization.py`):
- `normalize_company_name(raw)` la `normalization.py:122` — returnează `(canonical, was_matched)`
- `normalize_address(raw)` la `normalization.py:231` — idem

**Algoritm:**
1. Pre-procesare: strip Chinese, CUI patterns, SC prefix, SRL/SA suffix
2. Exact match pe `ALIAS_TO_CANONICAL` lookup
3. Altfel, `rapidfuzz.fuzz.WRatio(raw, alias)` contra fiecărui alias — threshold **≥ 92**
4. Extra requirement: primul cuvânt semnificativ (>3 chars) din input trebuie să aparțină în alias (evită `"TERACOTA"` match cu `"TERAPLAST"` la WRatio 88)

> **De ce threshold 92:** empiric — ajunge să prindă variante comune (spații extra, diacritice diferite, prescurtări) fără false positives pe companii cu prefixe similare.

## `extraction_model` label

Coloană DB în `extraction_results.extraction_model`. Valori:

| Valoare | Ce înseamnă |
|---------|-------------|
| `vision:<model>` (ex: `vision:gemini-2.5-flash`) | Extras de Vision AI (default) |
| `text:<model>` | Extras de text AI (retry când Vision eșuează) |
| `regex_fallback` | Extras prin pattern regex (last-resort) |

**Construit dinamic** din `settings.ai_model` (`__init__.py` după fix-ul din 2026-04-18 care elimina hardcode-ul `"gemini-2.0-flash"`). Se schimbă imediat ce schimbi modelul din UI.

Vezi `extraction_model` în UI pentru fiecare document — e indicatorul cel mai direct dacă extracția rulează pe calea Vision sau a căzut pe regex.

## `review_status` + `review_reasons`

Câmp pe `extraction_results` care spune dacă documentul trebuie revizuit uman.

| Valoare | Când |
|---------|------|
| `OK` | extracție curată, fără probleme semnalate |
| `REVIEW` | G5 suspicious-expiry, sau alte validări soft (ex: material prea scurt/lung, companie match cert body, caractere chinezești rămase, etc.) |
| `NEEDS_CHECK` | toate câmpurile-cheie au rămas null după retry text — ceva e fundamental greșit (doc corupt? AI offline? model ales invalid?) |
| `FAILED` | excepție neprinsă în pipeline |

`review_reasons` e un JSONB array cu obiecte:
```json
[
  {"reason": "suspicious_past_expiry", "field": "data_expirare", "message": "..."},
  {"reason": "company_short", "field": "companie", "message": "..."}
]
```

UI-ul folosește asta în AlertsPage — grupează docs pe motiv.

## `adresa_distribuitor` — detecție țară și alertă non-RO

Câmpul `adresa_distribuitor` e extras paralel cu `adresa_producator` pentru 12 din 14 categorii (toate exceptând `CERTIFICAT_CALITATE` și `ALTELE`). AI-ul e instruit explicit să-l returneze **null** dacă documentul nu identifică un distribuitor distinct — NU să copieze adresa producătorului.

### De ce îl extragem

Distribuitorul autorizat pentru un material în Makyol ar trebui să fie în România (lanțul de aprovizionare local). Un distribuitor străin semnalează fie (a) un document alocat greșit (era certificat al producătorului, nu autorizație de distribuție), fie (b) o rută neașteptată care merită verificare umană.

### Detector de țară

`pipeline/country_detector.py::detect_address_country(addr)` returnează `"RO"`, `"OTHER"` sau `None` (pentru input gol).

**Ordine decizie:**
1. **Semnale străine (oricare ⇒ OTHER, prioritare):** ~30 nume de țări în variante native + engleză + română (`italia`/`italy`/`italien`, `germania`/`germany`/`deutschland`, `turcia`/`turkey`/`türkiye`, `china`/`p.r.c.`, `france`, `spain`, `poland`, `hungary`, `netherlands`, etc.).
2. **Semnale RO (oricare ⇒ RO):**
   - keyword `romania` (fără diacritice, după normalizare)
   - prefix postcode `RO-123456` sau `RO 123456`
   - prefixe stradale RO: `str.`, `strada`, `bd.`, `bulevardul`, `aleea`, `calea`, `piata`, `sos.`, `soseaua`, `intrarea`, `dn<nr>`
   - hint-uri administrative: `jud.`, `judetul`, `sector [1-6]`, `mun.`, `com.`, `sat`
   - cod postal 6 cifre
   - ~50 orașe RO (capitale de județ + orașe industriale)
3. **Default (nimic nu se potrivește) ⇒ OTHER.** Conservator — favorizează verificarea umană. Dovadă că logica e corectă: o adresă românească reală aproape întotdeauna conține cel puțin un prefix stradal sau un nume de oraș.

Normalizare input: lowercase + strip diacritics (NFKD) înainte de matching.

### Review reason: `distribuitor_not_romanian`

`pipeline/validation.py:254` emite un issue structurat când `detect_address_country(adresa_distribuitor) == "OTHER"`:

```json
{"reason": "distribuitor_not_romanian", "field": "adresa_distribuitor",
 "message": "adresa_distribuitor is not a Romanian address"}
```

Impact: `review_status` urcă la `REVIEW` (dacă nu era deja NEEDS_CHECK / FAILED). Documentul apare în `AlertsPage > Necesită review` cu reason-ul explicit.

**Important:** `adresa_producator` **NU** primește același check. Producătorii străini sunt legitimi (certificatele CE/PED vin frecvent din Italia, Germania, China). Doar distribuitorul e legat de geografie — el e partenerul local Makyol.

### Display rules (frontend)

- `DocumentDetail.tsx` — afișează `adresa_distribuitor` imediat după `adresa_producator`, cu un badge roșu `Non-RO` dacă `isRomanianAddress()` returnează `false`. Adresele goale afișează `N/A`.
- `DocumentsTable.tsx` — **nu** afișează coloana (simetric cu `adresa_producator`, care nici el nu e în tabel). Se evită zgomot pentru distribuitorii RO care sunt norma.
- Exporturi (CSV + Excel, pe frontend și arhiva backend) — **includ** coloana pentru audit trail, fără filtrare după țară.

### Future work (neimplementat)

- **Knowledge base pentru distribuitori.** `pipeline/schemas/knowledge_base.json` are doar adrese de producători. O extensie cu entry-uri de distribuitori canonici ar permite fuzzy matching similar cu `adresa_producator`. Până atunci, `adresa_distribuitor` e pastrat ca raw string (după truncate + OCR fix).
- **Setting configurabil pentru enable/disable.** Check-ul e hardcodat — nu poate fi dezactivat prin settings UI. Dacă devine zgomotos, adaugă un flag `VALIDATE_DISTRIBUITOR_COUNTRY` în `settings` table.

## Settings care afectează extracția

Toate hot-reloadabile (vezi [configuration.md#hot-reload](./configuration.md#hot-reload)):

| Setting | Default | Efect |
|---------|---------|-------|
| `ai_model` | `google/gemini-2.5-flash` | Modelul OpenRouter pentru Vision + text AI + classification |
| `ai_temperature` | `0.0` | Deterministic |
| `openrouter_api_key` | — | Autentificare OpenRouter |
| `vision_max_pages` | `3` | Pipeline randerează (N-1) primele + ultima |
| `tesseract_path` | `D:\Tesseract-OCR\tesseract.exe` | Binar Tesseract (Windows); Linux ignoră |
| `batch_concurrency` | `3` (backend, nu pipeline) | Câte `/process` concurent pornește backend la reprocess-all |

## Verify freshness

```bash
# 14 categorii
grep -c "^\s*'" pipeline/classification.py | head -1
grep -A17 "^VALID_CATEGORIES = \[" pipeline/classification.py | grep "'" | wc -l
# trebuie 14

# _USE_VISION_FOR_ALL = True
grep -n "_USE_VISION_FOR_ALL = " pipeline/__init__.py
# L29 = True

# G5 threshold 180 zile
grep -n "_SUSPICIOUS_PAST_EXPIRY_DAYS" pipeline/__init__.py
# L46 = 180

# CATEGORIES_WITH_DATA_EXPIRARE există
grep -n "^CATEGORIES_WITH_DATA_EXPIRARE = frozenset" pipeline/extraction.py
# L202

# rapidfuzz WRatio threshold 92
grep -nE "WRatio|ratio.*>=\s*92|score.*92" pipeline/normalization.py | head

# 10 companii în KB
python -c "import json; print(len(json.load(open('pipeline/schemas/knowledge_base.json'))['companies']))"
# 10

# Vision randat la 300 DPI
grep -n "VISION_DPI" pipeline/config.py
# 300
```
