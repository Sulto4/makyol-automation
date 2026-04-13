# Documentație Completă — Sistem Automatizare Documente Makyol

**Versiune:** 1.0  
**Data:** 12 Aprilie 2026  
**Status:** MVP validat, pregătit pentru dezvoltare aplicație

---

## 1. CONTEXT DE BUSINESS

### 1.1 Proiectul

Makyol (constructor turc) construiește un lot de autostradă în România (Autostrada Sibiu-Făgăraș). În cadrul proiectului, trebuie relocate conducte de apă existente. Pentru a putea introduce materialele în șantier, constructorul Makyol trebuie să transmită către supervizorul tehnic (TECNIC Consulting Engineering România SRL) o adresă oficială însoțită de un dosar complet de documente care atestă conformitatea materialelor.

### 1.2 Problema

Fiecare material care intră în șantier are nevoie de un pachet de documente: certificate ISO ale producătorului, declarații de conformitate, fișe tehnice, avize sanitare, agremente tehnice, certificate CE (pentru producători din afara UE), certificate de calitate, certificate de garanție, autorizații de distribuție, CUI-uri ale companiilor implicate.

Un dosar tipic conține 30-50 de PDF-uri per pachet de materiale, iar Makyol lucrează cu 9+ pachete simultan (309 documente total în iterația curentă). Documentele vin de la producători diferiți (români, turci, chinezi), în limbi diferite (română, engleză, turcă, chineză), în formate diferite (PDF native, scanuri, copii).

Procesarea manuală a acestor documente — clasificare, extragere de date, verificare termene, identificare documente lipsă — durează zile de muncă și e predispusă la erori.

### 1.3 Ce trebuie să vadă utilizatorul final

Operatorul (persoana de la Makyol responsabilă cu documentele) trebuie să poată:

1. **Încărca PDF-uri** — drag & drop un set de documente, indiferent de ordine sau denumire
2. **Vedea un tabel centralizator** cu toate documentele, structurat pe coloane: Nume Document, Categorie, Nr. Pagini, Material, Data Expirare, Companie, Producător, Distribuitor, Adresă Producător
3. **Filtra și sorta** — pe material, producător, categorie, status expirare
4. **Vedea alerte** — documente expirate, documente lipsă per producător/material, companii fără ISO-uri valide, producători non-UE fără CE
5. **Deschide documentul original** — click pe un rând și vede PDF-ul
6. **Corecta manual** — dacă sistemul a extras greșit un câmp, operatorul poate corecta
7. **Exporta** — Excel sau Word cu tabelul final, gata de trimis la supervizor

### 1.4 Lanțul de companii

Într-un pachet tipic de documente apar trei tipuri de entități:

- **Producător** — compania care fabrică materialul (ex: TERAPLAST SA, HEBEI HUAYANG STEEL PIPE CO., SAINT-GOBAIN PAM Canalisation). Poate fi din România, UE, sau din afara UE (China, Turcia).
- **Distribuitor** — compania care importă/distribuie materialul în România (ex: TITAN STEEL TRADING SRL, PETROUZINEX SRL, ZAKPREST CONSTRUCT SRL).
- **Subcontractor/Furnizor** — compania care livrează direct către Makyol pentru șantier (ex: ZAKPREST CONSTRUCT SRL — care e și distribuitor în unele cazuri).

Un **material** poate avea mai mulți producători și mai mulți distribuitori. Sistemul trebuie să înțeleagă aceste relații.

### 1.5 Cerințe de conformitate per tip de companie

- **Producător din UE:** ISO-uri (9001, 14001 minim), Declarație de Conformitate, Fișă Tehnică, Certificat de Calitate
- **Producător din afara UE:** toate cele de mai sus PLUS Certificate CE/PED (sau document de excludere CE), Avize Tehnice românești
- **Distribuitor:** Autorizație de distribuție, CUI
- **Fiecare material:** Agrement Tehnic (dacă e necesar), Aviz Sanitar (dacă intră în contact cu apa potabilă), Declarație de Performanță

---

## 2. STRUCTURA DOCUMENTELOR

### 2.1 Cele 14 categorii de documente

| Cod | Categorie | Descriere | Pagini tipice | Cine emite |
|-----|-----------|-----------|---------------|------------|
| `ISO` | Certificate ISO | ISO 9001, 14001, 45001, 50001 — certifică sistemul de management al producătorului | 1-4 | Organism de certificare (TÜV, Lloyd's, LRQA) |
| `CE` | Certificate CE/PED | Marcaj CE, Directiva Echipamente sub Presiune (PED 2014/68/EU) | 2-4 | Organism notificat (TÜV, Bureau Veritas) |
| `FISA_TEHNICA` | Fișe Tehnice | Specificații tehnice ale produsului (dimensiuni, presiuni, materiale) | 3-16 | Producător |
| `AGREMENT` | Agremente Tehnice | Agrementare tehnică în construcții emisă de MDLPA/CTPC | 10-20 | Ministerul Dezvoltării (prin organisme evaluate) |
| `AVIZ_TEHNIC` | Avize Tehnice | Aviz tehnic emis de organisme tehnice | 1-2 | Organism tehnic |
| `AVIZ_TEHNIC_SI_AGREMENT` | Aviz Tehnic + Agrement | Document combinat care conține și aviz și agrement | 13-16 | Organisme evaluate |
| `AVIZ_SANITAR` | Avize Sanitare | Aviz sanitar pentru materiale în contact cu apa potabilă | 1-2 | Direcția de Sănătate Publică |
| `DECLARATIE_CONFORMITATE` | Declarații de Conformitate | Declarație conform HG 668/2017 că produsele respectă normele | 1-2 | Producător/Distribuitor |
| `DECLARATIE_PERFORMANTA` | Declarații de Performanță | Declarație conform Regulamentul UE 305/2011 (produse de construcții) | 1-3 | Producător |
| `CERTIFICAT_CALITATE` | Certificate de Calitate | Certificate 3.1 (EN 10204), MTC, certificate de testare fabrică | 1-2 | Producător/Laborator |
| `CERTIFICAT_GARANTIE` | Certificate de Garanție | Garanție pe produse (tipic 2-5 ani) | 1-2 | Producător/Distribuitor |
| `AUTORIZATIE_DISTRIBUTIE` | Autorizații de Distribuție | Autorizație de la producător pentru distribuitor | 1-2 | Producător |
| `CUI` | Certificate de Înregistrare | Certificat de Înregistrare la Registrul Comerțului (CUI) | 1-2 | ONRC |
| `ALTELE` | Altele | Documente care nu se încadrează în categoriile de mai sus | variabil | Diverși |

### 2.2 Structura pachetelor (din iterația curentă)

9 pachete organizate pe tip de material/furnizor:

| Pachet | Conținut | Producători principali | Nr. docs |
|--------|----------|----------------------|----------|
| 1 | Documente Zakprest + PEHD Apă TERAPLAST | TERAPLAST SA, ZAKPREST CONSTRUCT SRL | ~46 |
| 2 | PVC-KG TERAPLAST | TERAPLAST SA | ~30 |
| 3 | Țeavă Fontă (SAINT-GOBAIN) + Gaz TERAPLAST | SAINT-GOBAIN PAM, TERAPLAST SA | ~35 |
| 4 | Vane TIANJIN KEFA | TIANJIN KEFA VALVE CO., BBK VALVE GROUP | ~20 |
| 5 | PEHD Apă VALROM + Drenaj | VALROM INDUSTRIE SRL | ~40 |
| 6 | Gaz Distribuție (TERAPLAST + VALROM) | TERAPLAST SA, VALROM INDUSTRIE SRL | ~35 |
| 7 | Țevi Oțel (producători chinezi) | HEBEI HUAYANG, BESTAR STEEL, SHANDONG LUXING | ~35 |
| 8 | Materiale diverse + Precon + Boma | PRECON SRL, BOMA PREFABRICATE SRL | ~30 |
| 9 | Compensatoare (TIANJIN KEFA + producători chinezi) | TIANJIN KEFA, TIANJIN HUILIFENG | ~38 |

### 2.3 Câmpurile de extracție

Pentru fiecare document se extrag:

| Câmp | Tip | Descriere | Exemplu |
|------|-----|-----------|---------|
| `nume_document` | string, max 50 chars | Titlul/tipul documentului | "Certificat ISO 9001" |
| `numar_pagini` | integer | Numărul de pagini al PDF-ului | 4 |
| `material` | string, max 300 chars, nullable | Produsul/materialul la care se referă documentul | "Țevi PEHD PE100 RC SDR11 DN110-DN630" |
| `data_expirare` | string (DD.MM.YYYY sau durată), nullable | Data expirării documentului | "14.02.2027" sau "2 ani de la recepție" |
| `companie` | string, nullable | Compania principală (certificator pt CE/ISO, companie certificată pt altele) | "TÜV Rheinland Industrie Service GmbH" |
| `producator` | string, nullable | Producătorul materialului | "TERAPLAST SA" |
| `distribuitor` | string, nullable | Distribuitorul materialului | "ZAKPREST CONSTRUCT SRL" |
| `adresa_producator` | string, max 250 chars, nullable | Adresa sediului producătorului | "Sat Sărățel, Comuna Șieu-Măgheruș, Calea Teraplast nr.1, jud. Bistrița-Năsăud" |

Notă: câmpul `material` este null pentru ISO (certifică sisteme de management, nu materiale fizice) și CUI (document de identitate firmă).

---

## 3. PIPELINE-UL TEHNIC (STATUS ACTUAL)

### 3.1 Arhitectura curentă

Script Python monolitic (`clasificare_documente_final.py`, 1700 linii) care face:

```
PDF Input
    │
    ▼
┌─────────────────────┐
│  TEXT EXTRACTION     │  pdfplumber → PyMuPDF → Tesseract OCR
│  (3 fallback-uri)   │  DPI: 200 (clasificare) / 250 (extracție)
└─────────┬───────────┘  Limbi OCR: ron+eng
          │
          ▼
┌─────────────────────┐
│  CLASIFICARE        │  Nivel 1: Filename Regex (25+ patterns) → 71% docs
│  (3 nivele)         │  Nivel 2: Text Rules (scoring markers) → 13% docs
│                     │  Nivel 3: AI via OpenRouter → 12% docs
└─────────┬───────────┘  Text Override: 1% (forțare pe baza textului)
          │              Filename+Text Agree: 3%
          ▼
┌─────────────────────┐
│  EXTRACȚIE DATE      │  AI via OpenRouter (Gemini Flash)
│  (AI per document)   │  Schema specifică per categorie
│                      │  System prompt + category instructions
└─────────┬───────────┘  Temperature: 0.0, Max tokens: 1000
          │
          ▼
┌─────────────────────┐
│  NORMALIZARE        │  Company name normalization
│  POST-EXTRACȚIE     │  Romanian diacritics fix
│                     │  OCR error correction
│                     │  Field validation & truncation
└─────────┬───────────┘  ISO material forced to null
          │
          ▼
┌─────────────────────┐
│  EXPORT             │  Excel (openpyxl) cu 2 sheet-uri:
│                     │  - Raport Documente (18 coloane)
└─────────────────────┘  - Sumar (statistici per categorie)
```

### 3.2 Clasificare — Detalii tehnice

**Nivel 1 — Filename Regex (71% din documente)**

25+ pattern-uri regex ordonate pe prioritate. Exemple:
- `(?i)(aviz\s*(si|și|\+|&)\s*(at|agrement))` → AVIZ_TEHNIC_SI_AGREMENT (0.95)
- `(?i)\bISO\s*\d{4,5}|\bISO\b` → ISO (0.90)
- `(?i)(?:^|\b)\d+\.\s*CC\b` → CERTIFICAT_CALITATE (0.85)
- `(?i)^(teava|garnitura|cot|teu)\s` → FISA_TEHNICA (0.70)

Regulile de mai sus sunt prioritizate: AVIZ_TEHNIC_SI_AGREMENT vine înainte de AVIZ_TEHNIC și AGREMENT individual, CE vine cu atenție la boundary-uri pentru a nu captura "SERVICE", etc.

**Nivel 2 — Text Content Rules (13% din documente)**

Scor pe baza markerilor în text. Exemple:
- CE: `directiva\s+\d{4}/\d+`, `pressure\s+equipment`, `eu\s+certificate\s+of\s+conformity` — scor ≥2 markeri → CE (0.92)
- Declarație Performanță: `declara[tț]i[ea]\s+de\s+performan[tț][aă]`, `regulamentul.*305/2011` — scor ≥2 cu ≥1 în titlu → DP (0.92)
- ISO: pattern `iso\s*(9001|14001|45001|50001)` + context certificare → ISO (0.95)

Text Override: dacă textul conține markeri foarte puternici (ex: "EU CERTIFICATE OF CONFORMITY" + "PED" + "DIRECTIVE"), override-ul forțează categoria chiar dacă filename-ul sugerează altceva.

**Nivel 3 — AI Classification (12% din documente)**

Prompt trimis la OpenRouter (model: Gemini 2.0 Flash):
- System prompt cu cele 14 categorii și descrieri
- User prompt cu filename + primii 2000 de caractere din text
- Returnează JSON cu `category`, `confidence`, `reasoning`
- Temperature 0.0 pentru determinism maxim

**Confidence levels:**
- 0.95: filename regex foarte specific (ISO, CUI, AVIZ_SANITAR)
- 0.90: filename regex standard (CE, AGREMENT, DC)
- 0.85-0.92: text rules cu scor bun
- 0.70-0.85: match parțial sau AI classification
- < 0.70: flag pentru REVIEW manual

### 3.3 Extracție — Detalii tehnice

**Schema per categorie:**

Fiecare din cele 14 categorii are un set specific de câmpuri de extras și instrucțiuni dedicate. Exemple:

- **CE**: distincție clară între `producator` (fabricant: HEBEI HUAYANG) și `companie` (organism certificare: TÜV Rheinland)
- **ISO**: `material` forțat la null (ISO certifică sisteme de management, nu produse fizice); `standard_iso` extras separat
- **CERTIFICAT_CALITATE**: dacă produsul e gol (template), se deduce din standard (EN 12201 → "Țeavă PE pentru apă")
- **CERTIFICAT_GARANTIE**: `data_expirare` extrasă ca durată ("2 ani de la recepție"), nu dată fixă
- **CUI**: `cui_number` extras ca cifre pure

**API Call:**
```
POST https://openrouter.ai/api/v1/chat/completions
Model: google/gemini-2.0-flash-001
Temperature: 0.0
Max tokens: 1000
Messages: [system_prompt (extraction rules), user_prompt (filename + category + text[:5000])]
Output: JSON cu câmpurile specifice categoriei
```

**Post-procesare (normalize_extraction_result):**
1. Map câmpuri raw → câmpuri standard (8 coloane output)
2. Normalizare companii: `normalize_company_name()` — strip SC prefix, normalizare SRL/SA, lookup dicționar
3. Fix diacritice românești: Ţ→Ț, ş→ș, ã→ă
4. Fix erori OCR: lndustrie→Industrie, PEÎD→PEID
5. Truncare: nume_document max 50 chars, material max 300, adresă max 250
6. Validare null-like: "null", "none", "n/a", "-" → None
7. ISO: forțare material = None

### 3.4 Normalizare companii (status actual)

Dicționar actual cu 4 companii românești: TERAPLAST, VALROM, TEHNO WORLD, ZAKPREST CONSTRUCT.

**Problemă:** Auditul a identificat 20+ grupuri de companii cu variante multiple care NU sunt acoperite:
- HEBEI HUAYANG: 7 variante
- AKMERMER: 11 variante
- SAINT-GOBAIN: 8 variante
- TIANJIN KEFA: 6 variante
- BBK VALVE: 4 variante
- TÜV AUSTRIA: 5 variante
- Plus alte 14 grupuri cu 2-4 variante fiecare

---

## 4. REZULTATE AUDIT (309 documente)

### 4.1 Statistici generale

| Metrică | Valoare |
|---------|---------|
| Total documente procesate | 309 |
| Extracții reușite | 303 (98.1%) |
| Fără text (OCR eșuat) | 6 (1.9%) |
| Erori AI | 0 |
| Review OK | 250 (80.9%) |
| NEEDS CHECK | 41 (13.3%) |
| REVIEW | 18 (5.8%) |

### 4.2 Bug-uri critice identificate

1. **#214 CUI fără date** — document scanat, status marcat OK în loc de NO_TEXT
2. **#235 Companie = listă clienți** — "Petrobras Exxon Mobile Pakistan State Oil..." extras ca un singur câmp
3. **#287, #299 Material garbled** — "Doulole flo.ngecl Dlsr10.ntlln9 Jo.lnts" din PDF cu font encoding corupt
4. **#160, #294, #307 Misclasificare** — 8.CC.pdf (Certificat Calitate?) clasificat ca CE prin text_override
5. **#261 Extracție goală** — certificat calitate NIMFA fără nicio dată extrasă

### 4.3 Probleme sistemice

- **20+ grupuri de companii** cu variante nenormalizate
- **5 intrări cu caractere chinezești** în câmpuri (material, producător)
- **17 grupuri de adrese** cu variante inconsistente pentru aceeași locație
- **9 intrări cu material generic** "Produse" (template-uri sau extracție incompletă)
- **4 companii cu CUI în câmpul companie** (contaminare)
- **8 fișiere ISO cu pagini = 0** (bug numărătoare pagini)

---

## 5. ROADMAP DEZVOLTARE

### 5.1 Faza curentă: Clasificare + Extracție (MVP VALIDAT)

Am demonstrat că pipeline-ul funcționează. Următorii pași sunt de calitate, nu de funcționalitate nouă.

### 5.2 Faza 2: Hardening pipeline (URMĂTORUL PAS)

**5.2.1 Knowledge Base complet**

Fișier JSON (`knowledge_base.json`) cu:
```json
{
  "companies": {
    "TERAPLAST_SA": {
      "canonical": "TERAPLAST SA",
      "aliases": ["TERAPLAST", "TERAPIA", "TERAPLAST SRL", "TERAPLAST-SA"],
      "type": "producator",
      "country": "RO",
      "address": "Sat Sărățel, Comuna Șieu-Măgheruș, Calea Teraplast nr.1, jud. Bistrița-Năsăud",
      "cui": "3094980"
    },
    "HEBEI_HUAYANG": {
      "canonical": "HEBEI HUAYANG STEEL PIPE CO., LTD",
      "aliases": ["HEBEI HUA YANG STEEL PIPE", "HEBEI HUAYANG STEELPIPE", "河北华洋钢管有限公司"],
      "type": "producator",
      "country": "CN",
      "address": "Yuzhuangzi Village, Hujiayuan Street, Binhai New Area, Tanggu, Tianjin, China"
    }
    // ... toate cele 20+ companii
  }
}
```

Normalizarea face fuzzy match (Levenshtein distance ≤ 3 sau 90%+ similarity) contra alias-urilor, elimină CUI din nume, strip-ează caractere chinezești când există și text latin.

**5.2.2 Schema Validation**

Validare automată pe output:
- `companie` / `producator` / `distribuitor`: max 80 caractere, fără liste separate de virgulă/spații
- `material`: nu conține doar "Produse", nu e gol pentru categorii care cer material
- `data_expirare`: format DD.MM.YYYY SAU durată recunoscută ("X ani/luni de la Y")
- `adresa_producator`: fără text repetat, fără garbled
- Dacă validarea eșuează → retry cu feedback specific ("compania extrasă are 120 caractere, pare o listă, nu un singur nume")

**5.2.3 Gemini Vision Fallback**

Pentru documentele unde OCR eșuează (NO_TEXT) sau textul e garbled:
- Convertește pagina PDF în imagine
- Trimite imaginea direct la Gemini Flash (multimodal)
- AI-ul "citește" direct din imagine, fără OCR intermediar
- Se aplică pe cele 6 ISO-uri Huayang + orice viitor scan problematic

**5.2.4 Extracție + Validare în doi pași**

Pas 1: extracție normală (ca acum).
Pas 2: un al doilea prompt care primește textul original + rezultatul extracției și verifică:
- "Producătorul X apare cu adevărat în document?"
- "Data de expirare Y e corectă?"
- "Câmpul companie conține o singură entitate?"
Se aplică selectiv (doar pe documente clasificate prin AI sau cu confidence < 0.85).

### 5.3 Faza 3: Interpretare (VIITOR)

Pasul de interpretare care analizează datele extrase la nivel de ansamblu:

- **Relații producător-distribuitor**: cine distribuie ce, cine fabrică ce
- **Completitudine per material**: materialul X are toate documentele necesare?
- **Verificare termene**: ce documente expiră în următoarele 30/60/90 de zile?
- **Conformitate per tip companie**: producătorul non-UE are CE/PED?
- **Alerte**: documente lipsă, expirate, inconsistente

### 5.4 Faza 4: Aplicație (VIITOR)

Back-end (FastAPI/Django) + Front-end (React/Next.js) + Bază de date (PostgreSQL/SQLite):

- Upload documente (drag & drop)
- Dashboard cu tabelul centralizator
- Filtrare, sortare, search
- Vizualizare PDF inline
- Editare manuală câmpuri
- Alerting (expirare, lipsă)
- Export Excel/Word
- Notificări email către furnizori

### 5.5 Faza 5: Automatizare comunicare (VIITOR ÎNDEPĂRTAT)

- Generare automată de email-uri către companii cu documente expirate/lipsă
- Template-uri email per tip de problemă
- Tracking response-uri

---

## 6. SPECIFICAȚII TEHNICE PENTRU DEZVOLTARE

### 6.1 Stack recomandat

| Componentă | Tehnologie | Motivație |
|-----------|-----------|-----------|
| Pipeline procesare | Python 3.10+ | Ecosistem matur pentru PDF, OCR, AI |
| PDF extraction | pdfplumber + PyMuPDF | Complementare: pdfplumber pt text structurat, PyMuPDF pt imagini |
| OCR | Tesseract (local) + Gemini Vision (cloud) | Tesseract gratuit pt text simplu, Vision pt scanuri complexe |
| AI extraction | OpenRouter API → Gemini Flash | Cost mic ($0.001-0.005/doc), viteză bună, acuratețe validată |
| AI validation | OpenRouter API → Gemini Flash | Same model, al doilea pas de verificare |
| Knowledge base | JSON file → migrare la DB | Simplu de editat manual, ușor de migrat |
| Back-end | FastAPI | Async, rapid, typing Python nativ |
| Bază de date | PostgreSQL (prod) / SQLite (dev) | Relational, suport JSON, matur |
| Front-end | React + Next.js | SSR, component-based, ecosistem mare |
| Export | openpyxl (Excel) + python-docx (Word) | Biblioteci mature, output profesional |

### 6.2 Structura modulară recomandată

```
makyol-automation/
├── pipeline/
│   ├── __init__.py
│   ├── text_extraction.py      # pdfplumber + PyMuPDF + OCR + Vision
│   ├── classification.py       # 3-level classification
│   ├── extraction.py           # AI data extraction
│   ├── normalization.py        # Company names, addresses, diacritics
│   ├── validation.py           # Schema validation + AI verification
│   └── knowledge_base.json     # Companies, aliases, addresses
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── routers/
│   │   ├── documents.py        # Upload, classify, extract
│   │   ├── reports.py          # Export Excel/Word
│   │   └── alerts.py           # Interpretation alerts
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic schemas
│   └── services/               # Business logic
├── frontend/                   # React/Next.js
├── tests/
│   ├── test_classification.py  # Regression tests per category
│   ├── test_extraction.py      # Expected outputs per document
│   ├── test_normalization.py   # Company name variants
│   └── fixtures/               # Sample PDFs + expected results
└── docs/
    └── DOCUMENTATIE_SISTEM.md  # Acest fișier
```

### 6.3 Modele AI și costuri

| Model | Cost/1M tokens | Viteză | Acuratețe | Folosit pentru |
|-------|---------------|--------|-----------|----------------|
| Gemini 2.0 Flash | ~$0.075 input, $0.30 output | Foarte rapid | Bună (validat pe 309 docs) | Extracție principală |
| Claude Haiku 4.5 | $0.25 input, $1.25 output | Rapid | Foarte bună | Validare/verificare |
| Claude Sonnet 4 | $3 input, $15 output | Mediu | Excelentă | Clasificare cazuri dificile |
| Gemini Flash Vision | Similar Flash text | Rapid | Bună | OCR fallback pe scanuri |

**Cost estimat per lot de 300 documente:**
- Clasificare: ~$0.30-0.50 (doar 12% ajung la AI)
- Extracție: ~$0.50-1.00 (toate documentele, dar text scurt)
- Validare (opțional): ~$0.20-0.50 (doar pe documente cu confidence scăzut)
- **Total: ~$1-2 per lot de 300 documente**

### 6.4 API OpenRouter

```
Endpoint: https://openrouter.ai/api/v1/chat/completions
Authentication: Bearer token
Modele: google/gemini-2.0-flash-001 (producție), alte modele prin same API
Rate limits: depind de plan
Timeout recomandat: 45 secunde
Retries: 2 (cu backoff)
```

### 6.5 Structura output Excel (actuală)

Sheet "Raport Documente" — 18 coloane:

| Coloană | Tip | Descriere |
|---------|-----|-----------|
| Nr. | int | Index secvențial |
| Fisier | string | Numele fișierului PDF |
| Categorie | string | Una din cele 14 categorii |
| Confidence | float | Scor de încredere (0-1) |
| Metoda | string | filename_regex / text_rules / ai / text_override |
| Nume Document | string | Titlul extras al documentului |
| Numar Pagini | int | Nr. pagini PDF |
| Material | string | Material/produs |
| Data Expirare | string | Data expirării sau durată |
| Companie | string | Companie principală |
| Producator | string | Producătorul materialului |
| Distribuitor | string | Distribuitorul |
| Adresa Producator | string | Adresa producătorului |
| Review | string | OK / REVIEW / NEEDS CHECK |
| Corectie Manuala | string | Câmp gol pentru corecții manuale |
| Status Extractie | string | OK / NO_TEXT / ERROR |
| Reasoning | string | Explicația clasificării |
| Cale Fisier | string | Calea completă la fișierul PDF |

Sheet "Sumar" — statistici agregate pe categorii și metode.

---

## 7. REGULI DE CLASIFICARE DETALIATE

### 7.1 Filename Regex — ordinea priorităților

1. AVIZ_TEHNIC_SI_AGREMENT (combinat trebuie prins ÎNAINTE de individual)
2. AVIZ_SANITAR ("sanitar", "AVS", pattern numere + "AS")
3. CUI
4. ISO (ISO + număr, sau numere standalone 9001/14001/45001/50001)
5. CE (boundary check important — "CE" e scurt și apare în alte cuvinte)
6. DECLARATIE_PERFORMANTA (înainte de DC generic)
7. DECLARATIE_CONFORMITATE
8. CERTIFICAT_GARANTIE
9. CERTIFICAT_CALITATE (inclusiv "CC", "C 3.1", "MTC", "mill test cert")
10. AGREMENT (după combinat)
11. AVIZ_TEHNIC (după sanitar și combinat)
12. AUTORIZATIE_DISTRIBUTIE
13. FISA_TEHNICA (inclusiv "FT", "data sheet", "catalog", nume de produse)

### 7.2 Text Content Rules — markeri cheie

**CE (2+ markeri necesari):**
- `directiva\s+\d{4}/\d+` (ex: "Directiva 2014/68/EU")
- `pressure\s+equipment\s+directive`
- `eu\s+certificate\s+of\s+conformity`
- `annex\s+iii.*module\s+h`
- `ce\s+mark`

**ISO (pattern + context):**
- Pattern: `iso\s*(9001|14001|45001|50001)` în text
- Context: "certificate", "certification", "validity", "management system"
- Dacă în titlu (primele 500 chars) + context → 0.95
- Dacă doar în body + context → 0.78

**Declarație Conformitate (2+ markeri):**
- `declara[tț]i[ea]\s+de\s+conformitate`
- `hg\s*(?:nr\.?)?\s*668` (HG 668/2017)
- `nu\s+pun\s+[îi]n\s+pericol\s+via[tț]a`
- `certificate?\s+of\s+conformity(?!.*pressure)` (exclus PED)

### 7.3 Cazuri speciale de clasificare

- **"EU Certificate of Conformity" + "PED"** = CE, NU Declarație Conformitate
- **"WRAS Approval"** = CERTIFICAT_CALITATE (aprobarea WRAS e un certificat de calitate pentru materiale în contact cu apă)
- **"Aviz Tehnic + Agrement"** = AVIZ_TEHNIC_SI_AGREMENT (categorie combinată separată)
- **Filename "8. CC.pdf"** = ar trebui să fie CERTIFICAT_CALITATE, dar dacă text_override găsește markeri CE puternici, poate fi suprascris (BUG CUNOSCUT — necesită verificare)

---

## 8. REGULI DE EXTRACȚIE DETALIATE

### 8.1 Distincții semantice importante

**CE: Producător vs. Companie**
- `producator` = fabricantul materialului (ex: HEBEI HUAYANG STEEL PIPE CO., LTD)
- `companie` = organismul de certificare care a emis certificatul (ex: TÜV Rheinland)
- GREȘIT: a pune fabricantul în câmpul companie

**ISO: Material = NULL**
- Certificatele ISO certifică sisteme de management (calitate, mediu, securitate), NU materiale fizice
- `material` trebuie forțat la null pentru ISO
- `standard_iso` (ex: "ISO 9001:2015") se pune în `nume_document`

**CERTIFICAT_CALITATE: Deducere material din standard**
- Dacă produsul nu e menționat explicit dar standardul apare:
  - EN 12201 → "Țeavă PE pentru apă (conform EN 12201)"
  - EN 13476 → "Țeavă PVC multistrat (conform EN 13476)"
  - EN 10204 → "Țevi/produse din oțel (conform EN 10204)"

**CERTIFICAT_GARANTIE: Durată, nu dată fixă**
- `data_expirare` = durata garanției: "2 ani de la recepție", "24 luni de la data livrării"
- NU o dată calendaristică (garanția se calculează de la livrare, nu de la emitere)

### 8.2 Normalizare companii — reguli

1. Strip prefix "S.C." / "SC " (arhaic, nu mai e obligatoriu)
2. Normalizare suffix: "S.R.L." / "S.R.L" / "srl" → " SRL"
3. Normalizare suffix: "S.A." / "S.A" / "sa" → " SA"
4. Strip "(CUI: XXXXX)" din câmpul companie
5. Lookup fuzzy în knowledge_base.json
6. Dacă textul conține caractere chinezești + text latin, păstrează doar textul latin
7. Dacă compania are > 80 caractere → flag REVIEW

### 8.3 Fix-uri OCR cunoscute

| OCR greșit | Corect | Context |
|-----------|--------|---------|
| lndustrie | Industrie | "l" confundat cu "I" |
| TERAPIA | TERAPLAST | OCR pe documente TERAPLAST |
| PEÎD | PEID | Diacritice false pe scanuri |
| ser,;ce | Service | Punctuație OCR |
| lron | Iron | "l" → "I" |
| GELIK | CELIK | OCR pe documente turcești |
| TIANJINHUILIFENG... (fără spații) | TIANJIN HUILIFENG... | OCR care colapsează spațiile |
| CO..LTD | CO., LTD | Punct dublu OCR |

---

## 9. COMPANII CUNOSCUTE (pentru Knowledge Base)

### 9.1 Producători români

| Companie | Forma canonică | CUI | Produse | Adresă |
|----------|---------------|-----|---------|--------|
| TERAPLAST | TERAPLAST SA | 3094980 | Țevi PEHD, PVC, fitinguri | Sat Sărățel, Com. Șieu-Măgheruș, jud. Bistrița-Năsăud |
| VALROM | VALROM INDUSTRIE SRL | - | Țevi PE100, PVC, fitinguri | Bd. Gen. Nicolae Dăscălescu nr. 261, Piatra Neamț |
| TEHNO WORLD | TEHNO WORLD SRL | - | Distribuitor țevi PEHD | - |
| PRECON | PRECON SRL | 382733 | Prefabricate beton | Com. Jilava, Șos. Giurgiului nr. 5, jud. Ilfov |
| BOMA | BOMA PREFABRICATE SRL | 80006102 | Prefabricate | Alba Iulia, str. Seini nr. 19E2, jud. Alba |

### 9.2 Producători internaționali

| Companie | Forma canonică | Țară | Produse |
|----------|---------------|------|---------|
| SAINT-GOBAIN PAM | SAINT-GOBAIN PAM CANALISATION | FR | Țevi fontă ductilă |
| SAINT-GOBAIN CPR | SAINT-GOBAIN CONSTRUCTION PRODUCTS ROMANIA SRL | RO (subsd.) | Distribuitie produse SG |
| HEBEI HUAYANG | HEBEI HUAYANG STEEL PIPE CO., LTD | CN | Țevi oțel sudate LSAW |
| TIANJIN KEFA | TIANJIN KEFA VALVE CO., LTD | CN | Vane, compensatoare |
| BBK VALVE | BBK VALVE GROUP CO., LTD | CN | Vane industriale |
| TIANJIN HUILIFENG | TIANJIN HUILIFENG ANTI-CORROSION AND INSULATION STEEL PIPE GROUP CO., LTD | CN | Izolație țevi oțel |
| BESTAR STEEL | BESTAR STEEL CO., LTD | CN | Țevi oțel |
| WEIFANG LUZHENG | WEIFANG LUZHENG INDUSTRY AND TRADE CO., LTD | CN | Țevi oțel |
| SHANDONG LUXING | SHANDONG LUXING STEEL PIPE CO., LTD | CN | Țevi oțel |
| AKMERMER | AKMERMER DEMIR CELIK TIC. VE SAN. LTD. STI. | TR | Oțel, fitinguri |
| KANAT | KANAT BOYACILIK TIC. VE SAN. A.S. | TR | Vopsele, acoperiri |

### 9.3 Distribuitori/Subcontractori

| Companie | Forma canonică | Rol |
|----------|---------------|-----|
| ZAKPREST CONSTRUCT | ZAKPREST CONSTRUCT SRL | Distribuitor + subcontractor principal |
| TITAN STEEL TRADING | TITAN STEEL TRADING SRL | Distribuitor țevi oțel |
| PETROUZINEX | PETROUZINEX SRL | Distribuitor |
| NIMFA COM | NIMFA COM SRL | Distribuitor |
| HALLS TRADING EDIL | HALLS TRADING EDIL SRL | Distribuitor |
| METAL TRADE INTERNATIONAL | METALTRADE INTERNATIONAL SRL | Distribuitor |
| INNOTECH VALVES | INNOTECH VALVES SRL | Distribuitor vane |

### 9.4 Organisme de certificare

| Companie | Forma canonică | Tip certificări |
|----------|---------------|-----------------|
| TÜV RHEINLAND | TÜV Rheinland Industrie Service GmbH | CE/PED |
| TÜV SÜD | TÜV SÜD Industrie Service GmbH | CE/PED |
| TÜV AUSTRIA TURK | TÜV AUSTRIA TURK | ISO, CE |
| LLOYD'S | Lloyd's Register Quality Assurance | ISO |
| LRQA | LRQA Nederland B.V. | ISO |
| EUROCERT | EUROCERT SA | ISO |
| AXA CERT | AXA CERT SRL | ISO |
| IRD CERTIFICARE | IRD CERTIFICARE | ISO |

---

## 10. TESTARE ȘI VALIDARE

### 10.1 Set de test recomandat

Minimum 2 documente per categorie, acoperind:
- Un document cu text nativ (PDF generat digital)
- Un document scanat (imagine)
- Un document în engleză
- Un document cu producător chinezesc (caractere mixte)
- Un document template/gol

### 10.2 Metrici de succes

| Metrică | Target MVP | Target Producție |
|---------|-----------|-----------------|
| Clasificare corectă | 95%+ | 99%+ |
| Extracție fără erori | 90%+ | 97%+ |
| Companii normalizate | 80%+ | 99%+ |
| Documente NO_TEXT | < 5% | < 1% (cu Vision) |
| Timp procesare 300 docs | < 30 min | < 15 min |
| Cost per lot 300 docs | < $5 | < $2 |

### 10.3 Regression testing

La fiecare modificare de pipeline, se rulează pe setul complet de 309 documente și se compară:
- Nr. clasificări corecte vs. run anterior
- Nr. câmpuri extrase corect vs. run anterior
- Nr. companii normalizate vs. run anterior
- Orice regresie (câmp care era corect și acum e greșit) = blocker

---

## 11. LIMITĂRI CUNOSCUTE

1. **Documente scanate cu OCR slab** — Tesseract local are acuratețe variabilă pe scanuri de calitate joasă. Soluție: Gemini Vision fallback.
2. **PDF-uri cu font encoding corupt** — unele PDF-uri (ex: 1.FT.pdf) au mapping-uri de fonturi greșite care produc text garbled. Singura soluție: Vision AI sau înlocuire PDF.
3. **Non-determinism OCR** — același document scanat poate produce texte ușor diferite la rulări diferite. Soluție: caching rezultate, sau Vision AI.
4. **Limbi multiple** — documente în chineză, turcă, franceză. AI-ul (Gemini) se descurcă bine multilingv, dar normalizarea post-extracție trebuie extinsă.
5. **Template-uri goale** — documente MODEL fără date concrete. Sistemul extrage "Produse" generic, ceea ce e corect dar nu util.
6. **Relații implicite** — sistemul nu deduce automat că ZAKPREST e distribuitorul pentru TERAPLAST. Asta necesită pasul de interpretare (Faza 3).
