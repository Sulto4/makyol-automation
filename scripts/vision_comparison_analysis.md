# Vision vs Text-based Extraction — Analiză comparativă

**Dataset**: 328 documente procesate în ambele variante (244 fișiere unice). 0 rânduri 100% identice — fiecare doc are cel puțin `extraction_model` schimbat.

## Distribuția diferențelor

| Tip | Număr |
|---|---|
| Doar extraction_model schimbat (pur cosmetic) | 5 |
| Extracție cu diferențe de conținut | 304 |
| Clasificare + extracție schimbate | 19 |
| Tranziții reale de categorie | 5 |

## Tranziții de categorie (toate îmbunătățiri)

| Fișier | Pre | Post | Verdict |
|---|---|---|---|
| 3. Instructiuni montaj.pdf | ALTELE (0.30, fallback) | FISA_TEHNICA (0.95, ai) | ✅ Vision corect |
| AT-003-05_1222-2025 compensatori.pdf | ∅ (gol) | AGREMENT (0.99) | ✅ Recovery (failed înainte) |
| Agrement tehnic 003 05 1279 Saint Gobain.pdf | ∅ | AGREMENT (0.98) | ✅ Recovery |
| Aviz si AT 017-05-4295-2025.pdf | ∅ | AVIZ_TEHNIC_SI_AGREMENT (0.98) | ✅ Recovery |
| Fise tehnice si declaratii de performanta_Boma.pdf | ∅ | DECLARATIE_PERFORMANTA (0.95) | ✅ Recovery |

**Concluzie clasificare**: Vision recuperează 4 documente care eșuaseră complet în extracția text-based. Zero regresii de clasificare.

## Câmpuri afectate (pe 304 rânduri cu diferențe reale)

| Câmp | % afectate |
|---|---|
| adresa_producator | 75% (233) |
| companie | 62% (191) |
| material | 58% (179) |
| producator | 55% (171) |
| data_expirare | 26% (81) |

## Unde VISION CÂȘTIGĂ clar

1. **Adrese pe PDF-uri scanate** — OCR-ul dădea garbage ("in Bucuresti str", "va aducem la cunostinta Tehno World are demarat..."), vision citește curat ("Str Stinjeneilor, nr 4, Sector 4, Bucuresti").
2. **Fix-uri de adrese greșite din KB** — Teraplast era "Str. Industriei Bistrita" (vechi/eronat), vision confirmă "Calea Teraplast, Sat Saratel" (real, direct de pe document).
3. **Documente cu semnături/ștampile** (Saint Gobain, Boma, Huayang) — vision extrage și din zonele cu imagini.
4. **Eliminarea caracterelor chinezești din output** — material "直缝埋弧焊钢管" (pre) → "Teava sudata longitudinal submersa" (post).
5. **10. CUI.pdf** — fix major: pre avea greșit `companie=VALROM, adresa=Str. Uzinei Valcea`; post corect `companie=ZAKPREST CONSTRUCT SRL, adresa=Str. Stanjeneilor Sector 4 Bucuresti`.

## Unde VISION PIERDE — regresii sistemice

### 1. SWAP `producator` ↔ `companie` (cel mai frecvent)

Vision pune aproape totul în `companie` și lasă `producator` gol. Exemple:
- `3. DOP.pdf`: pre `producator=TIANJIN KEFA`, post `companie=TIANJIN KEFA, producator=∅`
- `Fisa tehnica tevi GAZ`: pre `producator=TERAPLAST`, post `companie=TERAPLAST, producator=∅`
- `Autorizatie Petrouzinex/Saint Gobain`: pre `producator=SAINT-GOBAIN`, post `companie=SAINT-GOBAIN, producator=∅`
- `proextop-catalog`: pre `producator=PROEXTOP`, post `companie=PROEXTOP, producator=∅`
- Apare în **~30+ documente**.

### 2. Confuzie organism de certificare vs companie certificată

Pe documente AVT/Aviz Tehnic:
- `5. AVT.pdf`, `Aviz Tehnic PVC multistrat`: pre `companie=VALROM INDUSTRIE SRL` (compania certificată), post `companie=AXA CERT SRL` (organismul de certificare).
- Normalizator-ul are listă de `cert_bodies` doar pentru ISO, nu și pentru AVIZ_TEHNIC.

### 3. Date de expirare non-standard pierdute

- `8. CG.pdf`: pre `data_expirare="2 ani de la receptie"`, post `data_expirare=∅`.
- Vision respectă strict formatul DD.MM.YYYY; text-based accepta durate ca text.

### 4. Halucinație companie

- `A13__L4_0276_teava PEID Valrom`: post `companie=TECNIC` (inexistent — pare citit de pe watermark/logo). Pre avea corect VALROM.

### 5. Override-uri human_review pierdute

- `Aviz si AT 017-05-4295-2025.pdf`: pre avea `metoda_clasificare=human_review, confidence=1.00` (corectură manuală), post overwrite la `filename+text_agree, 0.98`.

## Cauza rădăcină a regresiei majore

Promptul vision (`_VISION_EXTRACTION_PROMPT`) e **unul generic pentru toate categoriile**:
```
companie — Numele companiei principale (producator sau emitent)
producator — Numele producatorului (daca e diferit de companie)
```

Vs. promptul text-based (`extraction.py::EXTRACTION_SCHEMA`) are **14 seturi de instrucțiuni per-categorie**, cu reguli specifice:
- **CE**: "'companie' = ORGANISMUL DE CERTIFICARE (TÜV, Bureau Veritas). 'producator' = fabricantul."
- **AUTORIZATIE_DISTRIBUTIE**: extrage DISTRIBUITOR + PRODUCATOR separat.
- **ISO**: doar `companie` (compania certificată), nu `material`.
- **FISA_TEHNICA**: `producator` = fabricantul, nu `companie`.
- etc.

**Vision pierde aceste reguli category-specific.**

## Recomandări (în ordine de impact)

### Prioritate 1 — Per-category vision prompt (rezolvă swap producator/companie)
Modifică `pipeline/vision_fallback.py::extract_with_vision` să primească schema per-categorie din `EXTRACTION_SCHEMA` și să injecteze instrucțiunile în prompt, așa cum face `extract_data_with_ai` pentru text-based. Estimat: recuperează ~30-40% din regresii.

### Prioritate 2 — Permite durate textuale pentru data_expirare
În promptul vision, adaugă: "Dacă documentul menționează durată (ex: '2 ani de la receptie', 'Pe durata contractului'), extrage ca text."

### Prioritate 3 — Extinde `cert_bodies` filter pentru AVIZ_TEHNIC
În `pipeline/__init__.py` există deja filtrul pentru ISO care blochează cert body-uri în `companie`. Extinde la AVIZ_TEHNIC, AVIZ_TEHNIC_SI_AGREMENT, AGREMENT (add AXA CERT SRL, SRAC etc. la listă).

### Prioritate 4 — Hybrid: vision pentru adresă/scan, text pentru producator/companie când text e bun
Dacă text_length > 800 ȘI text nu are garbage, rulează AMBELE extracții și merge: `companie`/`producator` din text, `adresa_producator` din vision. Mai scump (2x AI calls) dar mai acurat.

### Prioritate 5 — Respectă human_review
În pipeline, verifică `metoda_clasificare=human_review` înainte de a scrie și skip write dacă review-ul uman e mai recent.

## Verdict final

**Vision e NET POZITIV** pe dataset:
- ✅ 4 recoveries complete + 1 upgrade de clasificare
- ✅ Adrese corecte pe PDF-uri scanate (unde pre avea garbage)
- ✅ Reparat erori de date din KB (Teraplast)
- ✅ Elimină caractere chinezești din output

**Dar are regresii fixabile** — nu inherent la vision, ci la prompt engineering:
- ❌ Swap producator/companie (~30+ docs) → fix prin per-category prompt
- ❌ AXA CERT în loc de compania certificată (~5 docs) → fix prin cert_bodies extins
- ❌ Durate textuale pierdute (~2-3 docs) → fix prin prompt update

**Nu recomand rollback la text-based**. Recomand implementarea priorităților 1-3 (estimat 1-2h de lucru) pentru a păstra câștigurile vision și a elimina regresiile.
