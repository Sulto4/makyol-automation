# AI Context Briefing — Makyol Document Automation System

> **Acest fișier conține tot contextul necesar pentru un AI (AutoCloud, Claude Code, Codex) care va lucra pe proiectul Makyol Automation. Citește-l complet înainte de a scrie cod.**

---

## CE ESTE PROIECTUL

Sistem de automatizare pentru procesarea documentelor tehnice ale materialelor de construcții. Compania turcă Makyol construiește un lot de autostradă în România (Autostrada Sibiu-Făgăraș) și trebuie să reloceze conducte de apă. Pentru fiecare material introdus în șantier, trebuie trimis un dosar de documente către supervizorul tehnic (TECNIC Consulting).

Dosarul conține 30-50 de PDF-uri per pachet (certificate ISO, fișe tehnice, declarații de conformitate, avize sanitare, agremente, certificate CE, etc.) de la producători din România, Turcia, China, Franța. Procesarea manuală durează zile.

**Sistemul automatizează 3 pași:**
1. **Clasificare** — identifică tipul fiecărui PDF (din 14 categorii)
2. **Extracție** — extrage date structurate (material, producător, distribuitor, dată expirare, adresă)
3. **Interpretare** (viitor) — verifică completitudinea, relații producător-distribuitor, documente expirate/lipsă

## STATUS ACTUAL

Am construit și validat un **MVP funcțional** — un script Python (`clasificare_documente_final.py`, 1700 linii) care face clasificare + extracție pe 309 documente reale cu 98% success rate. Auditul complet este în `AUDIT_RAPORT_EXTRACTIE_309.md`.

**Ce funcționează bine:**
- Clasificarea pe 3 nivele (filename regex → text rules → AI) — 99% acuratețe
- Extracția AI cu Gemini Flash — funcțională pe 303/309 documente
- Export Excel cu 18 coloane
- OCR fallback cu Tesseract

**Ce trebuie îmbunătățit (toate detaliate în audit):**
- Normalizarea companiilor (20+ companii cu variante multiple — rezolvat parțial, knowledge_base.json conține TOATE alias-urile)
- 6 documente scanate fără text (ISO Huayang) — necesită Gemini Vision fallback
- Câteva extracții greșite (material garbled, companie = listă clienți)
- Validare automată pe output (câmpuri prea lungi, caractere chinezești, etc.)

## FIȘIERE DISPONIBILE

### Documentație
- `DOCUMENTATIE_SISTEM.md` — documentație completă: business context, structura documentelor, pipeline tehnic, roadmap, specificații, companii cunoscute, reguli clasificare/extracție, testare
- `AUDIT_RAPORT_EXTRACTIE_309.md` — raport audit pe cele 309 documente: bug-uri critice, probleme normalizare, recomandări fix
- `PROMPT_CONTEXT.md` — acest fișier

### Date structurate
- `knowledge_base.json` — 30+ companii cu forme canonice, alias-uri, adrese, tipuri, țări, produse
- `extraction_schemas.json` — schema de extracție per categorie (14 categorii, câmpuri, reguli speciale, prompt-uri)
- `all_extraction_data_309.json` — TOATE cele 309 rânduri de date extrase (JSON)
- `all_unique_companies.json` — 97 nume unice de companii cu contextul în care apar
- `all_unique_addresses.json` — 111 adrese unice cu frecvența

### Cod sursă
- `clasificare_documente_final.py` — scriptul MVP complet (1700 linii Python)

### Documente originale
- `Pachete Makyol/` — 309 PDF-uri organizate în 9 subfoldere (1-9)
- `Fisiere Makyol Clasificate/` — aceleași documente clasificate pe cele 14 categorii
- `Pachete Makyol/raport_clasificare.xlsx` — raportul Excel generat cu 18 coloane

### Documente de referință
- `Adresa_Materiale_Supervizor_v2.docx` — exemplu de adresă oficială care se trimite la supervizor
- `Centralizator_Pachete.xlsx` — centralizator pachete (9 sheet-uri)

## CONFIGURARE TECHNICĂ

### API
- **OpenRouter API Key:** `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`
- **Endpoint:** `https://openrouter.ai/api/v1/chat/completions`
- **Model producție (extracție):** `google/gemini-2.0-flash-001` — rapid, ieftin (~$0.075/M input), acuratețe bună
- **Model alternativ (clasificare dificilă):** `anthropic/claude-sonnet-4` — mai precis, mai scump
- **Budget:** ~$10 disponibil pe cont
- **Temperature:** 0.0 (determinism maxim)
- **Max tokens:** 1000 per call

### Mediu de execuție
- **OS:** Windows (user-ul rulează local)
- **Python:** `python` (nu `python3`)
- **Tesseract OCR:** instalat la `D:\Tesseract-OCR\tesseract.exe`
- **Limbi OCR:** `ron+eng` (română + engleză)
- **Dependențe Python:** pdfplumber, PyMuPDF (fitz), pytesseract, Pillow, openpyxl, requests

### Costuri estimate per lot 300 documente
- Clasificare AI: ~$0.30-0.50 (doar ~12% ajung la AI)
- Extracție AI: ~$0.50-1.00 (toate documentele)
- Validare AI (opțional): ~$0.20-0.50
- Total: ~$1-2 per lot

## CELE 14 CATEGORII DE DOCUMENTE

| Cod | Ce este | Material? | Data expirare? | Companie = ? |
|-----|---------|-----------|----------------|--------------|
| `ISO` | Certificat ISO | NU (null) | DA (dată fixă) | Compania certificată |
| `CE` | Certificat CE/PED | DA | DA | Organismul de CERTIFICARE (TÜV, Lloyd's) |
| `FISA_TEHNICA` | Fișă tehnică produs | DA | NU de obicei | — |
| `AGREMENT` | Agrement tehnic construcții | DA | DA | Compania titulară |
| `AVIZ_TEHNIC` | Aviz tehnic | DA | DA | Organism tehnic |
| `AVIZ_TEHNIC_SI_AGREMENT` | Combinat aviz+agrement | DA | DA | — |
| `AVIZ_SANITAR` | Aviz sanitar (apă potabilă) | DA | DA | Compania titulară |
| `DECLARATIE_CONFORMITATE` | Declarație HG 668/2017 | DA | NU | Compania declarantă |
| `DECLARATIE_PERFORMANTA` | Declarație UE 305/2011 | DA | NU | — |
| `CERTIFICAT_CALITATE` | Certificat 3.1 / MTC | DA | NU | Producătorul/Laboratorul |
| `CERTIFICAT_GARANTIE` | Certificat garanție | DA | DA (durată) | — |
| `AUTORIZATIE_DISTRIBUTIE` | Autorizație de la producător | DA (generic) | DA | — |
| `CUI` | Certificat de Înregistrare | NU (null) | NU | Compania înregistrată |
| `ALTELE` | Necategorizat | Opțional | — | — |

**Distincție critică la CE:** `producator` = fabricantul (HEBEI HUAYANG), `companie` = certificatorul (TÜV Rheinland). NU sunt aceeași entitate.

**Distincție critică la ISO:** ISO certifică sisteme de management, NU materiale. `material` trebuie FORȚAT la null.

## PIPELINE-UL CLASIFICARE (3 NIVELE)

### Nivel 1: Filename Regex
25+ patterns ordonate pe prioritate. Rezolvă ~71% din documente. Zero cost, determinist.

Ordinea e critică:
1. AVIZ_TEHNIC_SI_AGREMENT (înainte de individual)
2. AVIZ_SANITAR
3. CUI
4. ISO
5. CE (attention la boundary — "CE" e scurt)
6. DECLARATIE_PERFORMANTA (înainte de DC generic)
7. DECLARATIE_CONFORMITATE
8. CERTIFICAT_GARANTIE
9. CERTIFICAT_CALITATE
10. AGREMENT
11. AVIZ_TEHNIC
12. AUTORIZATIE_DISTRIBUTIE
13. FISA_TEHNICA

### Nivel 2: Text Content Rules
Scor pe baza markerilor din primele 500 chars (titlu) + restul textului. Rezolvă ~13%.

### Nivel 3: AI Classification
Prompt cu categoriile + primii 2000 chars de text → Gemini Flash → JSON cu category + confidence + reasoning.

### Text Override
Dacă textul conține markeri CE foarte puternici (directive UE, PED, etc.), override-ul forțează CE chiar dacă filename-ul sugerează altceva. **BUG CUNOSCUT:** 8.CC.pdf (probabil Certificat Calitate) forțat la CE.

## PIPELINE-UL EXTRACȚIE

1. Extrage text din PDF: pdfplumber → PyMuPDF → Tesseract OCR (250 DPI, ron+eng)
2. Trimite la AI: system prompt (reguli generale) + user prompt (filename + categorie + text[:5000] + instrucțiuni specifice categoriei)
3. AI returnează JSON cu câmpurile cerute
4. Post-procesare: normalizare companii, fix diacritice, fix OCR, validare lungimi, forțare null pe ISO material

## BUG-URI CUNOSCUTE (din audit 309 docs)

### Critice
1. **#214** — CUI scanat fără text, marcat OK în loc de NO_TEXT
2. **#235** — "Petrobras Exxon Mobile..." extras ca un singur câmp companie
3. **#287, #299** — Material garbled din PDF cu font encoding corupt
4. **#160, #294, #307** — 8.CC.pdf misclasificat (CE vs CERTIFICAT_CALITATE)
5. **#261** — NIMFA COM certificat calitate fără extracție

### Sistemic
- 20+ grupuri companii nenormalizate (rezolvat în knowledge_base.json)
- 6 ISO-uri NO_TEXT (scanuri pure, necesită Vision AI)
- 5 intrări cu caractere chinezești
- 9 intrări cu material generic "Produse"
- 4 companii cu CUI în câmpul companie
- 17 grupuri adrese inconsistente

## ROADMAP

### Faza 2 (NEXT): Hardening pipeline
- Knowledge base complet → fuzzy match companii
- Schema validation pe output → retry cu feedback
- Gemini Vision fallback → rezolvă NO_TEXT
- Extracție + Validare în doi pași → prinde erori AI

### Faza 3: Interpretare
- Relații producător-distribuitor
- Completitudine per material
- Alerte documente expirate/lipsă
- Conformitate per tip companie

### Faza 4: Aplicație
- FastAPI back-end + React front-end
- Upload PDF, dashboard, filtre, alerting
- Vizualizare PDF inline, editare manuală
- Export Excel/Word

### Faza 5: Automatizare comunicare
- Email-uri automate către companii cu documente expirate
- Tracking

## STRUCTURA MODULARĂ RECOMANDATĂ

```
makyol-automation/
├── pipeline/
│   ├── text_extraction.py      # PDF → text (pdfplumber + PyMuPDF + OCR + Vision)
│   ├── classification.py       # 3-level classification
│   ├── extraction.py           # AI data extraction
│   ├── normalization.py        # Company names, addresses, diacritics
│   ├── validation.py           # Schema validation + AI verification
│   └── knowledge_base.json     # Companies, aliases, addresses
├── api/
│   ├── main.py                 # FastAPI app
│   ├── routers/                # documents, reports, alerts
│   ├── models/                 # SQLAlchemy / DB models
│   ├── schemas/                # Pydantic schemas
│   └── services/               # Business logic
├── frontend/                   # React/Next.js
├── tests/
│   ├── test_classification.py
│   ├── test_extraction.py
│   ├── test_normalization.py
│   └── fixtures/               # Sample PDFs + expected results
├── data/
│   ├── knowledge_base.json
│   ├── extraction_schemas.json
│   └── test_fixtures.json
└── docs/
    ├── DOCUMENTATIE_SISTEM.md
    ├── AUDIT_RAPORT_EXTRACTIE_309.md
    └── PROMPT_CONTEXT.md
```

## REGULI CRITICE PENTRU IMPLEMENTARE

1. **Temperature 0.0** pe toate call-urile AI — determinism maxim
2. **Retry cu backoff** pe API calls — OpenRouter poate fi lent
3. **Nu rescrie PDF extraction** — pdfplumber + PyMuPDF funcționează bine, doar adaugă Vision fallback
4. **Testează cu sample-uri reale** — fișiere din `Pachete Makyol/`, nu date sintetice
5. **Normalizare DUPĂ extracție** — AI-ul extrage raw, post-procesarea normalizează
6. **ISO material = null ALWAYS** — nu lăsa AI-ul să pună standarde în câmpul material
7. **CE: producator ≠ companie** — cele mai frecvente erori sunt aici
8. **Caractere românești** — diacriticele trebuie normalizate (Ţ→Ț, ş→ș)
9. **Companii cu CUI** — strip "(CUI: XXXXX)" din câmpul companie
10. **OCR non-determinism** — aceeași scanare poate da rezultate diferite; cache-ul ajută
