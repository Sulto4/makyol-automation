# Raport Audit Complet — Extracție Date 309 Documente

**Data audit:** 12 Aprilie 2026  
**Model AI:** google/gemini-2.0-flash-001  
**Total documente:** 309 | **Extracții OK:** 303 (98%) | **Fără text (OCR eșuat):** 6 (2%)

---

## 1. BUG-URI CRITICE (date greșite sau lipsă)

### 1.1 — `#214` CUI fără date de extracție
**Fișier:** `1. CUI.pdf` (Pachet 2 PVC-KG TERAPLAST / APROBARE FURNIZOR)  
**Problemă:** Documentul este un scan pur (imagine fără strat OCR). Textul nu a putut fi extras, dar status-ul arată "OK" în loc de "NO_TEXT".  
**Impact:** Rând complet gol în raport — companie, adresă, totul lipsește.  
**Fix:** Trebuie adăugat ca NO_TEXT sau procesat cu OCR dedicat (Tesseract/Google Vision).

### 1.2 — `8. CC.pdf` clasificat ca CE (3 intrări: #160, #294, #307)
**Fișier:** `8. CC.pdf` (apare în 3 pachete: VANE-TIANJIN KEFA, Compensatori-Tianjin, Tianjin Kefa)  
**Problemă:** Documentul este un scan fără text (copie Konica Minolta). Clasificarea `text_override` l-a forțat la CE, dar fișierul se numește "CC" (Certificat de Calitate). Fără text, nu se poate verifica.  
**Impact:** Clasificare potențial greșită la 3 documente.  
**Fix:** Necesită verificare manuală. Dacă este Certificat de Calitate, regula de text_override trebuie ajustată.

### 1.3 — Material garbled OCR (2 intrări: #287, #299)
**Fișier:** `1.FT.pdf` (Compensatori - Tianjin, Tianjin Kefa)  
**Material extras:** `Doulole flo.ngecl Dlsr10.ntlln9 Jo.lnts`  
**Cauza:** PDF-ul are font encoding corupt (nu e problemă de OCR, ci de mapping-ul fontului în PDF). "Double flanged Dismantling Joints" → garbled.  
**Impact:** Material complet ilizibil în raport.  
**Fix:** PDF-ul trebuie înlocuit de la producător sau materialul trebuie setat manual/dedus din numele fișierului ("Fișă Tehnică" → tipul produsului).

### 1.4 — `#261` SAMPLE NIMFA COM SRL — extracție goală
**Fișier:** `SAMPLE NIMFA COM SRL MTC 25-153 Ø609,6 x 8,00 mm.pdf`  
**Categorie:** CERTIFICAT_CALITATE  
**Problemă:** `nume_document` este gol, deși documentul ar trebui să conțină date.  
**Fix:** Verificare manuală a conținutului PDF + debugging extracție.

### 1.5 — Companie = listă de clienți (#235)
**Fișier:** `Lista proiecte producator Huayang - semnat.pdf`  
**Companie extrasă:** `Petrobras Exxon Mobile Pakistan State Oil Co.Ltd.(PSO) Shell MPCL SGCL Dead Sea Works Ltd (DSW) TITAS Gas CNOOC Tecnicas Reunidas`  
**Cauza:** AI-ul a extras o listă de clienți/parteneri ca și cum ar fi un singur nume de companie.  
**Impact:** Date complet greșite.  
**Fix:** Post-processing: dacă câmpul "companie" conține mai mult de ~80 caractere sau mai multe entități juridice separate, flaggează ca "REVIEW".

---

## 2. PROBLEME DE NORMALIZARE NUME COMPANII

Aceasta este cea mai importantă problemă sistemică. Același producător/companie apare sub 5-12 variante diferite în raport.

### 2.1 — HEBEI HUAYANG (7 variante)
| Variantă | Câmp |
|----------|------|
| `HEBEI HUA YANG STEEL PIPE CO., LTD.` | producator |
| `HEBEI HUAYANG STEEL PIPE CO., LTD` | companie/producator |
| `HEBEI HUAYANG STEEL PIPE CO.,LTD` | companie/producator |
| `HEBEI HUAYANG STEELPIPE CO., LTD` | producator |
| `Hebei Huayang Steel Pipe Co., Ltd` | companie/producator |
| `Hebei Huayang Steel Pipe Co.,Ltd` | companie/producator |
| `河北华洋钢管有限公司 HEBEI HUAYANG STEEL PIPE CO.,LTD` | producator |

**Forma canonică recomandată:** `HEBEI HUAYANG STEEL PIPE CO., LTD`

### 2.2 — AKMERMER (11+ variante!)
| Variantă | Problema |
|----------|---------|
| `AKMERMER DEMIR CELIK TIC. SAN. LTD. ȘTI.` | Lipsește "VE" |
| `AKMERMER DEMIR CELIK. TIC. VE SAN. LTD. ȘTI.` | Punct extra după CELIK |
| `AKMERMER DEMIR GELIK TIC. VE SAN. LTD. ȘTI.` | GELIK vs CELIK (OCR) |
| `AKMERMER DEMIR CELIK TIC. VE SA. LTD. ȘTI.` | SA vs SAN |
| `AKMERMER DEMİR ÇELİK TİC. VE SAN. LT D. ȘTİ.` | Spațiu în "LTD" |
| `Akmermer Demir Celik Tc. Ve San. Ltd. Ști.` | Tc vs Tic |
| `AKMERMER DEMİR ÇELİK TİC. VE SAN. LTD. ȘTI.` | Diacritice turcești |

**Forma canonică recomandată:** `AKMERMER DEMIR CELIK TIC. VE SAN. LTD. STI.`

### 2.3 — SAINT-GOBAIN (8 variante)
| Variantă | Problema |
|----------|---------|
| `SAINT GOBAIN PAM CANALISATION` | Fără cratimă |
| `SAINT-GOBAIN PAM CANALISATION` | OK |
| `SAINT — GOBAIN CONSTRUCTION PRODUCTS ROMANIA SRL` | Em-dash |
| `SAINT — GOBAIN CONSTRUCTION PRODUCTS ROMÂNIA SRL` | Em-dash + â |
| `SAINT- GOBAIN CONSTRUCTION PRODUCTS ROMÂNIA SRL` | Cratimă + spațiu |
| `SAINT - GOBAIN PAM CANALISATION` | Spații în jurul cratimei |
| `Saint-Gobain PAM Canalisation` | Title case |

**Forme canonice:** `SAINT-GOBAIN PAM CANALISATION` și `SAINT-GOBAIN CONSTRUCTION PRODUCTS ROMANIA SRL`

### 2.4 — TIANJIN KEFA (6 variante)
| Variantă | Problema |
|----------|---------|
| `Tianjin KEFA Valve Co., Ltd.` | Title case |
| `Tianjin KEFA Valve Co.,Ltd.` | Fără spațiu |
| `TIANJIN KEFA VALVE CO., LTD` | Fără punct final |
| `TIANJIN KEFA VALVE CO.,LTD` | Fără spațiu, fără punct |
| `TIANJIN KEFA VALVE CO..LTD` | Punct dublu (OCR) |

**Forma canonică:** `TIANJIN KEFA VALVE CO., LTD`

### 2.5 — BBK VALVE (4 variante)
`BBK VALVE GROUP CO., LTD` / `BBK VALVE GROUP CO., LTD.` / `BBK VALVE Group Company Limited` + `TIANJIN BBK VALVE MANUFACTURE CO., LTD`  
**Notă:** "BBK VALVE GROUP" și "TIANJIN BBK VALVE MANUFACTURE" par entități diferite.

### 2.6 — TIANJIN HUILIFENG (fără spații — OCR sever)
`TIANJINHUILIFENGANTI-CORROSIONANDINSULATIONSTEELPIPEGROUP CO.LTD`  
vs. forma corectă: `TIANJIN HUILIFENG ANTI-CORROSION AND INSULATION STEEL PIPE GROUP CO.,LTD`

### 2.7 — KANAT (4 variante)
`KANAT` (trunchiat) / `KANAT Boyacilik Tic. ve San. A.S` / `KANAT Boyacilik Tic. ve San. A.S.` / `KANAT PAINTS AND COATINGS` (traducere engleză)

### 2.8 — TÜV AUSTRIA (5 variante)
`TUV AUSTRIA TURK` / `TÜV AUSTRIA TURK` / `TUV Austria Turk` / `TUV Austria Türk` / `TUV AUSTRIA TURK Belgelendirme...`

### 2.9 — BESTAR STEEL (4 variante)
`BESTAR STEEL CO., LTD` / `Bestar Steel Co., Ltd` / `Bestar Steel Co., Ltd.` / `Bestar Steel CO., LTD.`

### 2.10 — WEIFANG LUZHENG (3 variante)
`WEIFANG LUZHENG INDUSTRY AND TRADE CO.,LTD.` / `WEIFANG LUZHENG INDUSTRY AND TRADE CO., LTD.` / `Weifang Luzheng Industry and Trade Co ltd`

### 2.11 — Alte probleme minore
- `AXA CERT SRL` vs `AXA-CERT SRL`
- `NIMFA - COM SRL` vs `NIMFA COM SRL`
- `METAL TRADE INTERNATIONAL SRL` vs `METALTRADE INTERNATIONAL SRL`
- `PETROUZINEX SRL` vs `PIROUZINEX` (OCR probabil)
- `BOMA PREFABRICATE SRL` vs `BOMA PREFABRICATE SRL (CUI: 80006102)` — CUI inclus
- `TERAPLAST SA` vs `TERAPLAST SA (CUI: 3094980)` — CUI inclus
- `PRECON SRL` vs `PRECON SRL (CUI: 382733)` — CUI inclus
- `ZAKPREST CONSTRUCT SRL` vs `ZAKPREST CONSTRUCT SRL (CUI: 34646295)` — CUI inclus
- `NATURAL` (bare name, fără formă juridică) — verificat: corect, compania chiar se numește NATURAL

---

## 3. CARACTERE CHINEZEȘTI ÎN CÂMPURI

### 3.1 — Material cu caractere chinezești
- `#113, #240`: `直缝埋弧焊钢管 LONGITUDINALSUBMERGED ARCWELDING PIPE`
- `#115, #242`: `SAWL Pipe Longitudinal Submerged Arc Welding Pipe 直缝埋弧焊管`
- `#125`: `External 3LPE 钢管`

### 3.2 — Producător complet în chineză
- `#125`: `湖南佰仕达钢管有限公司` (Hunan Baishida Steel Pipe Co., Ltd)
- `#240`: `河北华洋钢管有限公司 HEBEI HUAYANG STEEL PIPE CO.,LTD` (+ versiune engleză)

**Impact:** Inconsistență în raport. Unele documente chinezești au doar caractere chineze, altele au și traducerea engleză.  
**Fix:** Post-processing: dacă materialul/producătorul conține caractere chinezești dar și text latin, păstrează doar partea latină. Dacă e complet chinezesc, flaggează pentru traducere manuală.

---

## 4. PROBLEME DE NORMALIZARE ADRESE

Am identificat **17 grupuri** de adrese care se referă la aceeași locație dar au variante diferite.

Exemple cheie:

**ZAKPREST (5 variante):**
- `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, Bucuresti`
- `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- `Str Stinjeneilor, nr 4, Sector 4, Bucuresti`
- `București Sectorul 4, Strada STANJENEILOR, Nr. 4, CAMERA NR. 1, Bloc 62, Scara 2, Etaj 1, Ap. 61`

**TERAPLAST / Piatra Neamț (3 grupuri, 7 variante):**
- `Bd.General Nicolae Dăscălescu, Nr. 261, Loc. Piatra Neamt, Județul Neamt, România` (x15)
- `Bd. General Nicolae Dăscălescu nr.261 610201 Piatra-Neamt, Jud. Neamt` (x1)
- `Piatra-Neamt, Str.Bulevardul General Nicolae Dascalescu , Nr.261, Judetul Neamt` (x2)

**Adresă garbled (Wuxia Industry Park):**
- `A1 BuildingWuxia Industry Park Dongli DistrictWuxia Industry Park Dongli District, Wuxia Industry Park, Dongli District, Tianjin City 300454, China`
- Text repetat și lipsa spațiilor — OCR defectuos sau PDF cu font encoding prost.

**Recomandare:** Normalizarea adreselor este un task complex. Se poate implementa:
1. Normalizare per-companie: fiecare companie are O singură adresă canonică în KNOWN_COMPANIES
2. Sau: normalizare minimă (diacritice, majuscule, punctuație) fără a forța o formă unică

---

## 5. INCONSISTENȚE DE FORMAT

### 5.1 — `numar_pagini = 0` pentru 8 fișiere ISO (Zakprest)
Fișierele ISO #1-#4 și #43-#46 au `numar_pagini = 0`. Aceste documente au text extratibil, deci pagina ar trebui să fie >= 1.  
**Cauza probabilă:** Bug în extragerea numărului de pagini (pdfplumber returnează 0 pentru anumite PDF-uri ISO?).

### 5.2 — `nume_document` trunchiat
- `#133`: `FIȘĂ TEHNICĂ – ȚEVI SUDATE LONGITUDINAL (LSAW) CU` — trunchiat la 50 caractere, pierde informație.
- `#114, #241`: `MANUFACTURE PROCEDURE FOR INERNAL COATINGS （MPS）` — notă: "INERNAL" nu "INTERNAL" (OCR error în PDF)

### 5.3 — Date de expirare ca durată (5 intrări)
- `24 luni de la data livrării` (x1)
- `Pe durata contractului` (x2)
- `2 ani de la receptie` (x2)

Acestea sunt corecte conceptual (certificate de garanție), dar inconsistente ca format cu celelalte date (DD.MM.YYYY).

### 5.4 — Material = "Produse" (generic, 9 intrări)
Documentele MODEL (#93, #109, #122, #236, #284) și 4.DC.pdf (#148, #156, #290, #303) au material = "Produse" — fie sunt template-uri fără produse specifice, fie extracția nu a reușit.

---

## 6. DOCUMENTE NO_TEXT (6 intrări)

| Nr | Fișier | Categorie |
|----|--------|-----------|
| #103 | ISO 14001 Huayang - semnat.pdf | ISO |
| #105 | ISO 45001 Huayang - semnat.pdf | ISO |
| #106 | ISO 9001 Huayang - semnat.pdf | ISO |
| #230 | ISO 14001 Huayang - semnat.pdf | ISO |
| #232 | ISO 45001 Huayang - semnat.pdf | ISO |
| #233 | ISO 9001 Huayang - semnat.pdf | ISO |

Toate sunt certificate ISO Huayang scanate (imagini pure). Apar în duplicate (Pachet 5 și Pachet 8).  
**Fix posibil:** OCR cu Tesseract (dacă calitatea scanării permite) sau Google Cloud Vision API.

---

## 7. REVIEW STATUS

| Status | Nr. | Procent |
|--------|-----|---------|
| OK | 250 | 80.9% |
| NEEDS CHECK | 41 | 13.3% |
| REVIEW | 18 | 5.8% |

**41 de documente NEEDS CHECK** sunt în majoritate clasificate prin AI (metoda "ai"), ceea ce e corect — orice document clasificat prin AI ar trebui verificat cu prioritate mai mare.

---

## 8. SUMAR PROBLEME ȘI PRIORITĂȚI

### Prioritate CRITICĂ (date greșite)
1. **Bug #214** — CUI fără date, status OK în loc de NO_TEXT
2. **Bug #235** — Lista de clienți extrasă ca nume companie
3. **Bug #287, #299** — Material garbled din PDF cu font encoding corupt
4. **Bug #160, #294, #307** — 8.CC.pdf posibil misclasificat (CE vs CC)
5. **Bug #261** — Extracție goală pentru certificat calitate NIMFA

### Prioritate MARE (inconsistență date)
6. **Normalizare companii** — 20+ grupuri de companii cu variante multiple (cel mai grav: AKMERMER cu 11 variante, HEBEI cu 7)
7. **CUI inclus în nume companie** — 4 companii au "(CUI: XXXXX)" în câmpul companie
8. **Caractere chinezești** — 5 intrări cu mix chineză/engleză sau doar chineză
9. **TIANJINHUILIFENG fără spații** — OCR sever, 4 intrări

### Prioritate MEDIE (calitate date)
10. **Normalizare adrese** — 17 grupuri cu variante (cel mai grav: ZAKPREST cu 5 variante)
11. **Material generic "Produse"** — 9 intrări (template-uri sau extracție incompletă)
12. **numar_pagini = 0** — 8 fișiere ISO cu pagini = 0
13. **Adresă garbled Wuxia** — text repetat și lipsă spații

### Prioritate SCĂZUTĂ (cosmetice)
14. **Date ca durată** — 5 intrări cu format diferit (corect, dar inconsistent)
15. **nume_document trunchiat** — 2 intrări la limita de 50 caractere
16. **Case inconsistency** — Title Case vs UPPERCASE la companii (ex: TUV Austria vs TÜV AUSTRIA)

---

## 9. RECOMANDĂRI DE FIX

### Fix 1: Normalizare avansată companii
Extinde `normalize_company_name()` cu:
- Mapping complet pentru toate companiile din dataset (HEBEI, AKMERMER, SAINT-GOBAIN, etc.)
- Regex pentru eliminare CUI: `re.sub(r'\s*\(CUI:\s*\d+\)', '', name)`
- Normalizare case: upper case canonical
- Normalizare punctuație: `CO.,LTD` → `CO., LTD`; `SAINT — GOBAIN` → `SAINT-GOBAIN`
- Strip caractere chinezești când există și text latin

### Fix 2: Normalizare adrese
- Dicționar de adrese canonice per companie
- Sau normalizare minimă: diacritice consistente, punctuație standard

### Fix 3: Detectare NO_TEXT
- Verifică lungimea textului extras. Dacă < 20 caractere după cleanup, marchează NO_TEXT
- #214 ar trebui să fie NO_TEXT, nu OK

### Fix 4: Validare câmpuri
- Dacă `companie` > 80 caractere, flaggează REVIEW
- Dacă `material` conține doar "Produse", flaggează REVIEW
- Dacă `adresa` conține text repetat, cleanup automat

### Fix 5: Fallback din filename
- Pentru PDF-uri cu font encoding corupt (1.FT.pdf), extrage informații din numele fișierului și director ca fallback
