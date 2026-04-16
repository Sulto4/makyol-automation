# Vision vs Text-based Extraction Diff Report

## Summary

- **pre_total_rows**: 328
- **post_total_rows**: 328
- **pre_distinct_filenames**: 244
- **post_distinct_filenames**: 244
- **common_filenames**: 244
- **only_in_pre_filenames**: 0
- **only_in_post_filenames**: 0
- **identical_paired_rows**: 0
- **diff_kind_counts**:
  - `extraction_only`: 309
  - `both_changed`: 19
- **category_transitions_top**:
  - `∅ → AGREMENT`: 2
  - `ALTELE → FISA_TEHNICA`: 1
  - `∅ → AVIZ_TEHNIC_SI_AGREMENT`: 1
  - `∅ → DECLARATIE_PERFORMANTA`: 1


## Kind: `both_changed` (19 entries)

### `15. DC.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **material**
  - pre:  `produse pentru constructii`
  - post: `Produsele livrate pentru construcții`
- **adresa_producator**
  - pre:  `in Bucuresti str`
  - post: `Str Stinjeneilor, nr 4, Sector 4, Bucuresti`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. ISO 9001.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. ISO 14001.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. Instructiuni montaj.pdf`
- **categorie**
  - pre:  `ALTELE`
  - post: `FISA_TEHNICA`
- **confidence**
  - pre:  `0.30`
  - post: `0.95`
- **metoda_clasificare**
  - pre:  `fallback`
  - post: `ai`
- **companie**
  - pre:  `4 pipes GmbH`
  - post: `4 pipes`
- **material**
  - pre:  `End seals AKT/AWM`
  - post: `End seals AKT/AWM, AKT/AKO, AKT/AKG din cauciuc EPDM, pentru diverse diametre de tevi`
- **adresa_producator**
  - pre:  ``
  - post: `Sigmundstraße 182 • 90431 Nuremberg / Germany`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. ISO 45001.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. AVT.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `AXA CERT SRL`
- **material**
  - pre:  `Tevi din PVC-U pentru instalații de canalizare și drenaj`
  - post: `Țevi din PVC-U pentru instalații de canalizare și drenaj`
- **adresa_producator**
  - pre:  ``
  - post: `Baia, jud. Suceava`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. AVT.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `TERAPLAST SA`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. DC.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **material**
  - pre:  `Țevi Multistrat și Fitinguri din PVC pentru instalații de canalizare și drenare`
  - post: `Tevi Multistrat și Fitinguri din PVC pentru instalații de canalizare și drenare`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Parc Industrial TERAPLAST, Calea Teraplast, Nr.1, Sat: Saratel, Comuna Sieu magherus, 427298, județ Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8. CG.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **companie**
  - pre:  ``
  - post: `TERAPLAST SA`
- **material**
  - pre:  `Tevi si Fitinguri PVC, PP, PE, PEX, microtuburi fibra optica, Camine si accesorii PE, Rezervoare PE, Tuburi PVC si PE protectie cabluri, Microstatii epurare, separatoare grasimi, Granule`
  - post: `Teava PVC si Fitinguri PP pentru transport apa, canalizare si drenaj; Tevi si Fitinguri PP pentru instalatii sanitare; Tevi si Fitinguri PP pentru telecomunicatii; Tevi corugate si fitinguri din PP si PE pentru canalizare si drenaj; Tevi si fitinguri PE pentru transport gaze; Tevi si fitinguri PE`
- **data_expirare**
  - pre:  `2 ani de la receptie`
  - post: ``
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Sat Sărățel, Comuna Sieu-Magherus, ⏎ Calea TeraPlast, nr. 1, Jud. Bistrița-Năsăud, 427301`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `A13__L4_0276_AB_26.02.26_teava PEID si fitinguri_ producatorfurnizor -  Valrom Industrie SRL.pdf`
- **confidence**
  - pre:  `0.90`
  - post: `0.85`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `TECNIC`
- **material**
  - pre:  `teava PEID si fitinguri`
  - post: `Teava PEID si fitinguri`
- **data_expirare**
  - pre:  ``
  - post: `26.02.2026`
- **producator**
  - pre:  ``
  - post: `VALROM INDUSTRIE SRL`
- **adresa_producator**
  - pre:  `nr. MAKYOL-RO-LOT4-UTI016-23.02.2026, va`
  - post: `Str. loan Voda Caragea nr. 1, sector 1, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AT-003-05_1222-2025 compensatori montaj.pdf`
- **categorie**
  - pre:  ``
  - post: `AGREMENT`
- **confidence**
  - pre:  ``
  - post: `0.99`
- **metoda_clasificare**
  - pre:  ``
  - post: `filename+text_agree`
- **companie**
  - pre:  ``
  - post: `AVK INTERNATIONAL A/S`
- **material**
  - pre:  ``
  - post: `Compensatori de montaj AVK fabricați din următoarele elemente: corp oțel S275JR (EN 10025-2:2019) /fontă ductilă EN GJS-400-15, tiranti și piulițe din oțel 8.8 zincat și pasivat, garnituri din EPDM`
- **data_expirare**
  - pre:  ``
  - post: `23.01.2028`
- **adresa_producator**
  - pre:  ``
  - post: `Bizonevej 1, Skovby DK-8464 Galten, Danemarca`
- **extraction_model**
  - pre:  ``
  - post: `vision:gemini-2.0-flash`

### `Agrement tehnic  003 05 1279 2025 Saint Gobain.pdf`
- **categorie**
  - pre:  ``
  - post: `AGREMENT`
- **confidence**
  - pre:  ``
  - post: `0.98`
- **metoda_clasificare**
  - pre:  ``
  - post: `filename+text_agree`
- **companie**
  - pre:  ``
  - post: `SAINT - GOBAIN PAM Canalisation`
- **material**
  - pre:  ``
  - post: `Tuburi și fitinguri din fontă ductilă pentru sisteme de alimentare cu apă, fabricate de SAINT-GOBAIN PAM Canalisation-Franța, cu diametre nominale (DN) cuprinse în domeniul 60 ÷ 2000 mm, conform EN 545:2011, ISO 2531:2009.`
- **data_expirare**
  - pre:  ``
  - post: `24.04.2028`
- **adresa_producator**
  - pre:  ``
  - post: `21, Avenue Camille Cavallier – BP 129, 54705 PONT-A-MOUSSON CEDEX - Franța`
- **extraction_model**
  - pre:  ``
  - post: `vision:gemini-2.0-flash`

### `Agrement tehnic PVC multistrat  021-05-072-2024.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **material**
  - pre:  `ȚEVI MULTISTRAT DIN PVC-U PENTRU INSTALAȚII DE CANALIZARE SI DRENAJ`
  - post: `Tevi multistrat din PVC-U pentru instalații de canalizare și drenaj, diametru 110 ÷ 630 mm`
- **data_expirare**
  - pre:  `31.08.2025`
  - post: `08.04.2027`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 — jud. Suceava — România`
  - post: `Loc. Baia nr. 1616 - jud. Suceava - România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz Tehnic PVC multistrat  021-05-072-2024.pdf`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `AXA CERT SRL`
- **material**
  - pre:  `Tevi din PVC-U pentru instalații de canalizare și drenaj`
  - post: `Țevi din PVC-U pentru instalații de canalizare și drenaj`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Baia, jud. Suceava`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz si AT 017-05-4295-2025.pdf`
- **categorie**
  - pre:  ``
  - post: `AVIZ_TEHNIC_SI_AGREMENT`
- **confidence**
  - pre:  ``
  - post: `0.98`
- **metoda_clasificare**
  - pre:  ``
  - post: `filename+text_agree`
- **companie**
  - pre:  ``
  - post: `VALROM INDUSTRIE SRL`
- **material**
  - pre:  ``
  - post: `Țevi și fitinguri VALROM din PEID pentru instalații de alimentare cu apă rece și canalizare`
- **data_expirare**
  - pre:  ``
  - post: `24.07.2028`
- **adresa_producator**
  - pre:  ``
  - post: `B-dul Preciziei nr. 28, sector 6, București, ROMÂNIA`
- **extraction_model**
  - pre:  ``
  - post: `vision:gemini-2.0-flash`

### `Aviz si AT 017-05-4295-2025.pdf`
- **confidence**
  - pre:  `1.00`
  - post: `0.98`
- **metoda_clasificare**
  - pre:  `human_review`
  - post: `filename+text_agree`
- **review_status**
  - pre:  `REVIEW`
  - post: `OK`
- **companie**
  - pre:  ``
  - post: `VALROM INDUSTRIE SRL`
- **material**
  - pre:  ``
  - post: `Țevi și fitinguri VALROM din PEID pentru instalații de alimentare cu apă rece și canalizare`
- **data_expirare**
  - pre:  ``
  - post: `24.07.2028`
- **adresa_producator**
  - pre:  ``
  - post: `B-dul Preciziei nr. 28, sector 6, București, ROMÂNIA`
- **extraction_model**
  - pre:  ``
  - post: `vision:gemini-2.0-flash`

### `Fise tehnice si declaratii de performanta _Boma.pdf`
- **categorie**
  - pre:  ``
  - post: `DECLARATIE_PERFORMANTA`
- **confidence**
  - pre:  ``
  - post: `0.95`
- **metoda_clasificare**
  - pre:  ``
  - post: `text_rules`
- **companie**
  - pre:  ``
  - post: `BOMA PREFABRICATE`
- **material**
  - pre:  ``
  - post: `Inele de aducere la cota (suprainaltare) 865 / 625 / 50 / 120, 865 / 625 / 100 / 120, 865 / 625 / 150 / 120`
- **adresa_producator**
  - pre:  ``
  - post: `S.C. BOMA PREFABRICATE S.R.L. ⏎ Adresă: Platforma Industrială Florea Grup, Sat Strejnicu, Com. Tîrgșorul Vechi, DN1 A KM62+200, Jud. Prahova`
- **extraction_model**
  - pre:  ``
  - post: `vision:gemini-2.0-flash`

### `Plan de inspectie si testare a acoperirii interne producator Huayang -semnat.pdf`
- **confidence**
  - pre:  `0.85`
  - post: `0.95`
- **companie**
  - pre:  `TIANJINHUILIFENGANTI-CORROSIONANDINSULATIONSTEELPIPEGROUP CO.LTD`
  - post: ``
- **material**
  - pre:  `ȚEAVĂ LSAW`
  - post: `Conducte de otel cu protectie anticoroziva si izolatie termica, diverse dimensiuni si specificatii conform SR EN 10301/2004 & BS EN 10301/2003`
- **data_expirare**
  - pre:  ``
  - post: `11.04.2025`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `adresa Tehnoworld pentru agrementul tehnic al tevii de gaz.pdf`
- **confidence**
  - pre:  `0.85`
  - post: `0.65`
- **data_expirare**
  - pre:  ``
  - post: `26.02.2025`
- **adresa_producator**
  - pre:  `va aducem la cunostinta Tehno World are demarat procesul de re-`
  - post: `TehnoWorld SRL-Loc. Baia, nr. 1616, Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`


## Kind: `extraction_only` (309 entries)

### `01737.1 PE gaz.pdf`
- **companie**
  - pre:  `TERAPLAST SA`
  - post: `ICECON CERT`
- **material**
  - pre:  `TEVI “POLITUB” DIN POLIETILENĂ, PENTRU SISTEME DE ALIMENTARE CU GAZE NATURALE`
  - post: `TEVI "POLITUB" DIN POLIETILENĂ, PENTRU SISTEME DE ALIMENTARE CU GAZE NATURALE, PE 100/PE 100RC, DN (mm) Ø20 ÷ Ø800`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Comuna ȘIEU-MĂGHERUȘ, Sat SĂRĂȚEL, Calea Teraplast nr. 1, jud. BISTRIȚA-NĂSĂUD`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. CUI.pdf`
- **extraction_model**
  - pre:  ``
  - post: `vision:gemini-2.0-flash`

### `1. CUI.pdf`
- **material**
  - pre:  ``
  - post: `Fabricarea placilor, foliilor, tuburilor și profilelor din material plastic`
- **adresa_producator**
  - pre:  ``
  - post: `Sat Sărățel, Comuna Sieu-Magherus, CALEA TERAPLAST, Nr. 1, Județ Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. FT PEHD.pdf`
- **material**
  - pre:  `Tevi din polietilenă de înaltă densitate HDPE PE112, HDPE PE100, PE100RC, HDPE PE80`
  - post: `Teava din polietilena de inalta densitate PE112, PE100, PE100RC, PE80 conform EN 12201-2:2024, ISO 4427:2019, DIN 8074:2011`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Via Valsir 2, Villanuova sul Clisi, Italy`
  - post: `Localitatea Baia, nr. 1616, DN2E km 2, judetul Suceava, ROMÂNIA, 727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. FT Teava PEHD apa.pdf`
- **companie**
  - pre:  ``
  - post: `TERAPLAST SA`
- **material**
  - pre:  `Țevi PE100 pentru APĂ`
  - post: `Tevi PE100 pentru APĂ, SR EN 12201-2`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. FT Teava PVC-KG.pdf`
- **material**
  - pre:  `TEVI DIN PVC-U RIGID MULTISTRAT`
  - post: `TEVI DIN PVC-U RIGID MULTISTRAT PENTRU INSTALATII DE CANALIZARE INGROPATE – CURGERE FARA PRESIUNE ⏎ Standard de produs: SF 36/2017 (cu referinte din SR EN 13476)`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `DN 15A, km 45+500 ⏎ 390026 Bistrita, Bistrita-Nasaud ⏎ Tel. 0263-238202, Fax. 0263-231221`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. FT ro.pdf`
- **material**
  - pre:  `Tevi HDPE PE100, MRS= 10Mpa si PE80, MRS= 8MPa, pentru distributia si transportul gazelor naturale, conform normelor SR EN 1555-2, ISO 4437`
  - post: `Teava din polietilena de inalta densitate destinata retelelor de distributie si transport a gazelor naturale PE80 - PE100`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
  - post: `S.C. TehnoWorld SRL ⏎ Loc. Baia, nr. 1616, DN2E km 2 ⏎ Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. FT.pdf`
- **material**
  - pre:  `Robinet cu sertar cauciucat DIN3352 F4/F5`
  - post: `RESILIENT GATE VALVE DIN3352 F4/F5`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. FT.pdf`
- **material**
  - pre:  `ROBINET CU SERTAR CAUCIUCAT DIN3352 F4/F5`
  - post: `RESILIENT GATE VALVE DIN3352 F4/F5`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1. Fisa tehnica.pdf`
- **companie**
  - pre:  ``
  - post: `4 pipes`
- **producator**
  - pre:  `4 pipes GmbH`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.1 FT engl.pdf`
- **material**
  - pre:  `GAS POLYETHYLENE PIPE PE 100`
  - post: `Teava din polietilena de inalta densitate pentru gaz PE 100, standard EN 1555`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
  - post: `S.C TehnoWorld SRL ⏎ Loc. Baia, nr. 1616, DN2E km 2 ⏎ Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.1 FT.pdf`
- **material**
  - pre:  `ROBINET SERTAR CAUCIUCAT CU TIJA NEASCENDENTA DN40--ON600 DIN 5352`
  - post: `Robinetsertar cauciucat cu tija neascendenta DN40-DN600`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.1 FT.pdf`
- **material**
  - pre:  `ROBINET SERTAR CAUCIUCAT CU TIJA NEASCENDENTA DN40--ON600 DIN 5352`
  - post: `Robinetsertar cauciucat cu tija neascendenta DN40-DN600`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.1 FT.pdf`
- **material**
  - pre:  `Tirant delimitare Otel carbon`
  - post: `Compensator cu tiranti`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.1 FT.pdf`
- **companie**
  - pre:  ``
  - post: `K C PELLIZZARI OIL & GAS`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.FT.pdf`
- **companie**
  - pre:  ``
  - post: `PETROUZINEX`
- **material**
  - pre:  `Doulole flo.ngecl Dlsr10.ntlln9 Jo.lnts`
  - post: `Double flanged Dismantling Joints`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1.FT.pdf`
- **companie**
  - pre:  ``
  - post: `PETROUZINEX`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `10. CUI.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `ZAKPREST CONSTRUCT SRL`
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `București Sectorul 4, Strada STÂNJENEILOR, Nr. 4, CAMERA NR. 1, Bloc 62, Scara 2, Etaj 1, Ap. 61`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `10. ISO14001 & ISO45001 Tianjin.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `A1 Building(Waixu Industry Park) Dongli DistrictWaixu Industry Park Dongli District, Waixu Industry Park, Dongli District, Tianjin City 300400, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `10. ISO14001 & ISO45001 Tianjin.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `A1 Building/Waiwa Industry Park Dongli District/Waiwa Industry Park Dongli District, Waiwa Industry Park, Dongli District, Tianjin City 300400, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `11. ISO 9001 PETROUZINEX.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **data_expirare**
  - pre:  `25.08.2028`
  - post: `26.08.2028`
- **adresa_producator**
  - pre:  `Bd.General Nicolae Dăscălescu, Nr. 261, Loc. Piatra Neamt, Județul Neamt, Romania`
  - post: `Bd.General Nicolae Dascalescu, Nr. 261, Loc. Piatra Neamt, Judetul Neamt, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `11. ISO 9001 PETROUZINEX.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **data_expirare**
  - pre:  `25.08.2028`
  - post: `26.08.2026`
- **adresa_producator**
  - pre:  `Bd.General Nicolae Dăscălescu, Nr. 261, Loc. Piatra Neamt, Județul Neamt, Romania`
  - post: `Bd.General Nicolae Dascalescu, Nr. 261, Loc. Piatra Neamt, Judetul Neamt, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `11. ISO 9001.pdf`
- **data_expirare**
  - pre:  `14.02.2027`
  - post: `22.02.2027`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `11. ISO 9001.pdf`
- **data_expirare**
  - pre:  `14.02.2027`
  - post: `22.02.2027`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `12. ISO 14001 PETROUZINEX.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **adresa_producator**
  - pre:  `Bd.General Nicolae Dăscălescu, Nr. 261, Loc. Piatra Neamt, Județul Neamt, România`
  - post: `Bd. General Nicolae Dascalescu, Nr. 261, Loc. Piatra Neamt, Judetul Neamt, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `12. ISO 14001 PETROUZINEX.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **adresa_producator**
  - pre:  `Bd.General Nicolae Dăscălescu, Nr. 261, Loc. Piatra Neamt, Județul Neamt, România`
  - post: `Bd. General Nicolae Dascalescu, Nr. 261, Loc. Piatra Neamt, Judetul Neamt, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `12. ISO 14001.pdf`
- **data_expirare**
  - pre:  `14.02.2027`
  - post: `22.02.2024`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stănjenellor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `12. ISO 14001.pdf`
- **data_expirare**
  - pre:  `14.02.2027`
  - post: `02.02.2027`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjenellor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `13. ISO 45001 PETROUZINEX.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `QSCert`
- **data_expirare**
  - pre:  `25.08.2028`
  - post: `25.08.2025`
- **adresa_producator**
  - pre:  `SoS eae Reg No. 091/R-129`
  - post: `C. P. Vajanskeho 1, 960 01 Zvolen, Slovak Republic`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `13. ISO 45001 PETROUZINEX.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **data_expirare**
  - pre:  `25.08.2028`
  - post: `25.08.2025`
- **adresa_producator**
  - pre:  `SoS eae Reg No. 091/R-129`
  - post: `Bd.General Nicolae Dascalescu, Nr. 261, Loc. Piatra Neamt, Judetul Neamt, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `13. ISO 45001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `13. ISO 45001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `14. ISO 50001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `14. ISO 50001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Stânjeneilor, nr. 4, camera nr. 1, bl. 62, sc. 2, et. 1, ap. 61, sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `14_FISA TEHNICA PVC  multistrat.pdf`
- **material**
  - pre:  `Tevi realizate din PVC neplastifiat, de culoare brun roscata RAL 8023`
  - post: `Tevi din PVC-U multistrat pentru canalizare si drenaj, conform SR EN 13476-1:2018, SR EN 13476-3+A1:2020, SR EN 1401:2019.`
- **adresa_producator**
  - pre:  `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
  - post: `S.C TehnoWorld SRL Loc. Scheia, DN2E km 2 jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `15. DC.pdf`
- **material**
  - pre:  `produse pentru construcții`
  - post: `Produsele livrate pentru constructii`
- **adresa_producator**
  - pre:  `in Bucuresti str`
  - post: `Str Stinjeneilor, nr 4, Sector 4, Bucuresti`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `1cert_NIMFA_EN_RO.pdf`
- **companie**
  - pre:  `AKMERMER DEMIR CELIK TIC. SAN. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. DC.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Robineti cu sertar cauciucat`
  - post: `Resilient seat gate valves, ductile iron body, F4/F5 PN10/16 DN40 - DN1200, flange and resilient seat`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  `YUZHUANGCUN, HUJIAYUANJIE, TANGGU, TIANJIN, CHINA, 300452`
  - post: `YUZHUANGGCUN, HUJIAYUANJIE, TANGGU, TIANJIN, CHINA, 300452`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. DC.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Dismantling Joint PN10/16 DN40-2000`
  - post: `Compensator de montaj PN10/16 DN40-2000`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. DC.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Dismantling Joint PN10/16 DN40-2000`
  - post: `Compensator de montaj PN10/16 DN40-2000`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `yuzhuang village,hujiayuan street,tanggu,tianjin,china`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. DC.pdf`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C TEHNO WORLD S.R.L., Loc. Baia nr. 1616, jud. Suceava - România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. FT FITINGURI.pdf`
- **material**
  - pre:  `FITINGURI SEGMENTATE ⏎ POLIETILENA DE INALTA DENSITATE - PEHD`
  - post: `Fitinguri segmentate polietilena de inalta densitate (PEHD), diverse dimensiuni, conform EN 12201-3`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
  - post: `S.C TehnoWorld SRL ⏎ Loc. Dumbrava Rosie DN2E km 2 ⏎ Jud. Suceava, RO 727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. ISO 9001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2, 727030 Baia, jud. Suceava, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. ISO 9001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. ISO 9001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2, 727030 Baia, jud. Suceava, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. Licenta.pdf`
- **companie**
  - pre:  `TERAPLAST SA`
  - post: `AEROQ SA`
- **material**
  - pre:  `TUBURI SI ACCESORII DIN BETON: SIMPLU, BETON SLAB ARMAT, BETON ARMAT - TUBURI. 500, 600, 1000, 1250, 1500, 2000; REDUCTIE TRONCO 42) 1000; 800mm; 800/ 800mm si gura de scurgere DN 500 mm`
  - post: `Tuburi si accesorii din beton simplu, beton slab armat, beton armat-tuburi Ø 500, Ø 600, Ø 800, Ø 1000, Ø 1250, Ø 1500, Ø 2000, reductie tronconica Ø 1000/Ø 800mm; Ø 800/ Ø 600mm si gura de scurgere DN 500 mm, camine de vizitare si camine de racord din beton simplu, beton slab armat, beton armat.`
- **producator**
  - pre:  ``
  - post: `PRECON SRL`
- **adresa_producator**
  - pre:  ``
  - post: `Soseaua Giurgiului, nr.5, Jilava, Jud. Ilfov`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2. Test Report.pdf`
- **companie**
  - pre:  `4pipesGmbH`
  - post: `4 pipes GmbH`
- **material**
  - pre:  `Casing end seal type AKTI AWM IAST`
  - post: `4 pipes Casing end seal type AKT / AWM / AST, EPDM, black`
- **producator**
  - pre:  `4pipesGmbH`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Sigmundstrasse 182, 90431 Nuremberg`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2024-04-25-P1R0519_Valrom_A_2024_ro-_extsigned.pdf`
- **material**
  - pre:  `Țevi de presiune din polietilenă pentru apă potabilă – PE 80, PE 100, PE 100-RC`
  - post: `Țevi de presiune din polietilenă pentru apă potabilă - PE 80, PE 100, PE 100-RC, dimensiunea la 63 mm`
- **data_expirare**
  - pre:  ``
  - post: `25.04.2024`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Bdul. Preciziei, nr 28, sector 6 062204 Bucuresti ROMÂNIA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `24469 MTC-LSAW.pdf`
- **companie**
  - pre:  ``
  - post: `Shinestar Holdings Group`
- **material**
  - pre:  `LSAW STEEL PIPE API 5L PSL2`
  - post: `LSAW STEEL PIPE`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Add: No.9 Xiangfu Road, Changsha, Hunan, China ⏎ E-mail: service@bestarpipe.com ⏎ Tel: 86-731-86786506 P.O.: 410116`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `265-910-001_avk905_rom__586086 (1).pdf`
- **companie**
  - pre:  ``
  - post: `AVK GROUP A/S`
- **material**
  - pre:  `Compensator de montaj cu flanșă centrală, PN10/16 265/910-001`
  - post: `Compensator de montaj cu flanșă centrală, PN10/16, fontă ductilă, acoperire GSK, tiranti din oțel inoxidabil A2, DN40-1200`
- **producator**
  - pre:  `AVK`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `2cert_NIMFA_EN_RO.pdf`
- **companie**
  - pre:  `AKMERMER DEMIR CELIK TIC. SAN. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. CC 8 SABLON CC TEAVA GAZ PE100_draft.pdf`
- **material**
  - pre:  `Teava PE100 (conform SR EN 1555-1-2)`
  - post: `Produs conform SR EN 1555-1-2`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc: Jud: RO87BACX0000003023781012`
  - post: `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. DOP.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Robinet cu sertar cauciucat EPDM, F4/FS, PNl0/16 DN40-DN1200 corp din fonta ductila`
  - post: `Resilient seat gate valve, F4/F5, PN10/16 DN40-DN1200 made ductile iron`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  `yuzhuang village,hujiayuan street, tanggu,t ianjin,china`
  - post: `yuzhuang village,hujiayuan street,tanggu,tianjin,china`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. DOP.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  `yuzhuang village, hujiayuan street,tanggu,tianjin,china`
  - post: `yuzhuang village,hujiayuan street,tanggu,tianjin,china`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. DOP.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  `yuzhuang village, hujiayuan street,tanggu,tianjin,china`
  - post: `yuzhuang village,hujiayuan street,tanggu,tianjin,china`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. Declaratie de conformitate.pdf`
- **material**
  - pre:  `TUBURI ȘI ACCESORII DIN BETON SIMPLU 0500 ; 8600 ; 0800 ; O 1000 ; O 1250; 91500 ; REDUCTIE TRONCONICĂ @ 1000/ 0800 ; GURĂ SCURGERE DN 500mm ⏎ CAMINE DE VIZITARE ȘI CÂMINE DE RACORD SAU INSPECTIE DIN BETON SIMPLU`
  - post: `Tuburi si accesorii din beton simplu Ø500-Ø1500, reductie tronconica Ø1000/Ø800, gura scurgere DN 500mm, camine de vizitare si camine de racord sau inspectie din beton simplu conform SR EN 1916:2003, SR EN 1916/AC:2008, SR EN 1917:2003, SR EN 1917/AC:2008`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Sos. Giurgiului nr. 5, Județul Ilfov „cod postal 077120,`
  - post: `Șos. Giurgiului nr. 5, Județul Ilfov, cod poștal 077120, Jilava`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. ISO 14001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. ISO 14001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3. ISO 14001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2, 727030 Baia, jud. Suceava, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3LPE TDS.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `BESTAR STEEL CO.,LTD`
- **material**
  - pre:  `External 3LPE`
  - post: `5C STEEL, STEEL GRADE API 5L PSL2 L245N/L360N, external 3LPE, coating type 3LPE External Coating, ISO 21809-1 Polyethylene coatings on steel pipes and fittings`
- **producator**
  - pre:  `湖南佰仕达钢管有限公司`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `3cert_NIMFA_EN_RO.pdf`
- **companie**
  - pre:  `AKMERMER DEMIR CELIK TIC. SAN. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. AVT.pdf`
- **material**
  - pre:  `Țevi și fitinguri din Peid pentru alimentare cu gaze naturale combustibile`
  - post: `Tevi și fitinguri din Peid pentru alimentare cu gaze naturale combustibile`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Baia, jud. Suceava`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. Certificat de garantie.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PRECON SRL`
- **material**
  - pre:  `produsele`
  - post: ``
- **data_expirare**
  - pre:  `24 luni, de la data livrării`
  - post: ``
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Comuna Jilava, Sos. Giurgiului nr. 5, Județul Ilfov, cod poștal 077120`
  - post: `Comuna Jilava, Șos. Giurgiului nr. 5, Județul Ilfov, cod poștal 077120`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. DC.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **adresa_producator**
  - pre:  `Piatra-Neamt,Str.BulevardulGeneral Nicolae Dascalescu 261 Judetul:Neamt`
  - post: `Piatra-Neamt, Str. Bulevardul General Nicolae Dascalescu 261, Judetul: Neamt`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. DC.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **material**
  - pre:  `produsele de mai jos`
  - post: ``
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Piatra-Neamt,Str.BulevardulGeneral Nicolae Dascalescu 261 Judetul:Neamt`
  - post: `Piatra-Neamt, Str. Bulevardul General Nicolae Dascalescu 261, Judetul: Neamt`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. DC.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **material**
  - pre:  `produsele de mai jos`
  - post: ``
- **adresa_producator**
  - pre:  `Piatra-Neamt,Str.BulevardulGeneral Nicolae Dascalescu 261 Judetul:Neamt`
  - post: `Piatra-Neamt, Str. Bulevardul General Nicolae Dascalescu 261, Judetul: Neamt`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. DC.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **material**
  - pre:  `produsele de mai jos`
  - post: ``
- **adresa_producator**
  - pre:  `Piatra-Neamt,Str.BulevardulGeneral Nicolae Dascalescu 261 Judetul:Neamt`
  - post: `Piatra-Neamt, Str. Bulevardul General Nicolae Dascalescu 261, Judetul: Neamt`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. I.SO_4pipes_GB_9001.pdf`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. ISO 45001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2, 727030 Baia, jud. Suceava, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. ISO 45001.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `4. ISO 45001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. AGT.pdf`
- **material**
  - pre:  `Tevi și fitinguri din PEID pentru alimentare cu gaze naturale combustibile`
  - post: `Țevi și fitinguri din PEID pentru alimentare cu gaze naturale combustibile, tip PE 80, PE 100, SDR 11, cu diametre nominale cuprinse în domeniul 32 ÷ 800 mm, conform SR EN 1555-1/2:2021.`
- **data_expirare**
  - pre:  `27.02.2026`
  - post: ``
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr, 1616DN 2 E- jud. Suceava - Romănia`
  - post: `Loc. Baia nr. 1616DN 2 E- Jud. Suceava - România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. AVT.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `AXA-CERT SRL`
- **material**
  - pre:  `Țevi și fitinguri din PEID pentru instalatii de apa`
  - post: `Țevi și fitinguri din PEID pentru instalații de apă`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. C 3.1.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Robinet cu sertar cauciucat PN16 DN80`
  - post: `Robinet PN16 DN80 F4`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `YUZHUANGZHICUN,HUAIYUANLI,TANGGU,TIANJIN,CHINA,300452`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. C 3.1.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Compensator cu tirant PN10 DN450`
  - post: `bolt 2045-9`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `NO.128, WEISAN ROAD,DONGLI DISTRICT,TIANJIN,CHINA,300302`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. C 3.1.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `Compensator cu tirant PN10 DN450`
  - post: `bolt 2048-9, surub 2048-9`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `115 WEISAN ROAD, DONGLIJING, TIANJIN, CHINA,300302`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5. Instructiuni de manipulare si montaj.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PRECON`
- **material**
  - pre:  `TUBURI DIN BETON SI CAMINE DE VIZITARE`
  - post: `Tuburi din beton și cămine de vizitare`
- **adresa_producator**
  - pre:  `calea ferată sau alte mijloace adecvate. Aşezarea se face pe reazeme speciale din lemn, asigurate`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `5.ISO_4pipes_GB_14001.pdf`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AGT.pdf`
- **material**
  - pre:  `Țevi si fitinguri din PEID pentru instalații de apa`
  - post: `Țevi și fitinguri din PEID pentru instalații de apă`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AGT.pdf`
- **material**
  - pre:  `ȚEVI MULTISTRAT DIN PVC-U PENTRU INSTALAȚII DE CANALIZARE ȘI DRENAJ`
  - post: `Tevi multistrat din PVC-U pentru instalații de canalizare și drenaj. Diametru nominal teava: 110 ÷ 630 mm. Clasa de rigiditate inelara: SN2 (SDR 51) - rigiditate inelara 2 kN/m²; SN4 (SDR 41) - rigiditate inelara 4 kN/m²; SN8 (SDR 34) - rigiditate inelara 8 kN/m².`
- **data_expirare**
  - pre:  `31.08.2025`
  - post: `08.04.2027`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 — jud. Suceava — România`
  - post: `Loc. Baia nr. 1616 - jud. Suceava - România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AGT.pdf`
- **material**
  - pre:  `ȚEVI MULTISTRAT SI FITINGURI DIN PVC PENTRU INSTALAȚII DE CANALIZARE ȘI ⏎ DRENARE`
  - post: `Țevi multistrat și fitinguri din PVC pentru instalații de canalizare și drenare`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Sat Saratel, com. Șieu-Măgheruș, Calea Teraplast nr. 1 județ Bistrița-Năsăud`
  - post: `Sat Sărățel, com. Sieu-Măgheruș, Calea Teraplast nr. 1 judet Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AS.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **material**
  - pre:  `Robineti cu sertar, reținere, aerisire/dezaerisire, închidere, clapă fluture și bilă`
  - post: `Robineți cu sertar, reținere, aerisire/dezaerisire, închidere, clapă fluture și bilă`
- **producator**
  - pre:  `Tianjin KEFA Valve Co.,Ltd.`
  - post: `Tianjin KEFA Valve Co.,Ltd`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AS.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **material**
  - pre:  `Robineti cu sertar, reținere, aerisire/dezaerisire, închidere, clapă fluture și bilă`
  - post: `Robineți cu sertar, reținere, aerisire/dezaerisire, închidere, clapă fluture și bilă`
- **producator**
  - pre:  `Tianjin KEFA Valve Co.,Ltd.`
  - post: `Tianjin KEFA Valve Co.,Ltd`
- **adresa_producator**
  - pre:  `Yuzhuangzi Village, Hujiayuan Street, Binhai New Area, Tanggu, Tianjin`
  - post: `Yuzhuangzi Village, Hujiayuan Street, Binhai New Area, Tanggu, Tianjin, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AUTORIZATIE.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `robineti si fitinguri`
  - post: `valves and fittings`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AUTORIZATIE.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **adresa_producator**
  - pre:  `yuzhuang village,hujiayuan street,tanggu,tianjin,China`
  - post: `yuzhuang village,hujiayuan street,tanggu,tianjin,china`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. AVS.pdf`
- **material**
  - pre:  `Țevi și fitinguri VALROM din PE 100 BorSafe HE3490-LS, de culoare neagră cu dungi de reper albastre`
  - post: `Țevi și fitinguri VALROM din PE 100 BorSafe HE3490-LS, de culoare neagră cu dungi de reper albastre, țevi cu DN 20-1200 mm`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `București, Sector 6, B-dul Preciziei Nr.28`
  - post: `București, Sector 6, B-dul Preciziei Nr.28, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `6. ISO 9001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2, 727030 Baia, jud. Suceava, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. AS.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `INSTITUTUL NAȚIONAL DE SĂNĂTATE PUBLICĂ`
- **material**
  - pre:  `Compensator de montaj cu tiranti PN10-PN16, DN50-DN1400`
  - post: `Compensator de montaj cu tiranți PN10-PN16, DN50-DN1400`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. AS.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROZINEX SRL`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. AUTORIZATIE.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **material**
  - pre:  `robineti si fitinguri`
  - post: `valves and fittings`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `yuzhuang village,hujiayuan street,tanggu,tianjin,China`
  - post: `yuzhuang village,hujiayuan street,tanggu,tianjin,china`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. AVS RC.pdf`
- **material**
  - pre:  `Țevi și fitinguri VALROM din PE 100RC BorSafe HE3490-LS-H, de culoare neagră cu dungi de reper albastre`
  - post: `Țevi și fitinguri VALROM din PE 100RC BorSafe HE3490-LS-H, de culoare neagră cu dungi de reper albastre, țevi cu DN 20 - 1200 mm`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. AVS.pdf`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. AVS.pdf`
- **material**
  - pre:  `Țevi din PEID pentru instalații de apa`
  - post: `Tevi din PEID pentru instalații de apă`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `sat Sărățel, comuna Șieu-Măgheruș, DN 15 A, km. 45+500, Cod 427301, jud. Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `7. ISO 14001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2, 727030 Baia, jud. Suceava, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8. CC.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `LRQA`
- **material**
  - pre:  `Robineti cu clapa fluture, Robineti de retinere, Robineti cu sertar, Robineti cu bila si Filtre`
  - post: `Butterfly valves DN50 to DN1600, Check Valves DN50 to DN900, Gate valves DN50 to DN600, Ball valves DN50 to DN600, Y Type Strainers DN50 to DN300, Directive 2014/68/EU`
- **data_expirare**
  - pre:  ``
  - post: `04.08.2026`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **adresa_producator**
  - pre:  `sediu social:`
  - post: `Yuzhuangzi Village, Huijiayuan Street, Binhai New Area, Tanggu, Tianjin, People's Republic of China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8. CC.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `LRQA`
- **data_expirare**
  - pre:  ``
  - post: `04.08.2026`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **adresa_producator**
  - pre:  `sediu social:`
  - post: `Yuzhuangzi Village, Huajiayuan Street, Binhai New Area, Tanggu, Tianjin, People's Republic of China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8. CC.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `LRQA`
- **material**
  - pre:  `Butterfly valves, Check Valves, Gate Valves, Ball Valve and Strainers`
  - post: `Butterfly valves DN50 to DN1600, Check Valves DN50 to DN900, Gate valves DN50 to DN600, Ball valves DN50 to DN600, Y Type Strainers DN50 to DN300`
- **data_expirare**
  - pre:  ``
  - post: `04.08.2026`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **adresa_producator**
  - pre:  `sediu social:`
  - post: `Yuzhuangzi Village, Huijiayuan Street, Binhai New Area, Tanggu, Tianjin, People’s Republic of China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8. DC.pdf`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C TEHNO WORLD S.R.L., Loc. Baia nr. 1616, jud. Suceava - România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8. ISO 45001.pdf`
- **adresa_producator**
  - pre:  `Baia nr.1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
  - post: `Baia nr. 1616, DN 2 E- km 2 727030 Baia, jud. Suceava România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `8.1 AVT.pdf`
- **companie**
  - pre:  ``
  - post: `TERAPLAST SA`
- **material**
  - pre:  `Țevi din PEID pentru instalații de apă`
  - post: `Tevi din PEID pentru instalații de apă`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Sat Sărățel, Comuna Sieu-Măgheruș, Calea Teraplast nr.1, județul Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `9. AGT.pdf`
- **material**
  - pre:  `Tevi din PEID pentru instalatii de apa`
  - post: `TEVI DIN PEID PENTRU INSTALATII DE APA ⏎ HDPE PIPES FOR WATER INSTALLATIONS`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `9. CC.pdf`
- **material**
  - pre:  `Teava PE pentru apa (conform EN 12201)`
  - post: `PE100, executat dupa EN I 12201-2`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc : Jud: RO87BACX0000003023781012`
  - post: `Loc. Baia, nr. 1616, DN2E km 2, Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `9. CG.pdf`
- **companie**
  - pre:  ``
  - post: `TERAPLAST SA`
- **material**
  - pre:  `Tevi si Fitinguri PVC, PP, PE, PEX, Tuburi PVC si PE protectie cabluri, Camine si accesorii din PE, Rezervoare pentru lichide din PE, Microstatii epurare si separatoare grasimi, Granule`
  - post: `Tevi si Fitinguri PP pentru transport apa, canalizare si drenaj; Tevi si Fitinguri PP pentru telecomunicatii, fibra optica; Tevi corugate si fitinguri din PP si PE pentru canalizare si drenaj; Tevi si Fitinguri PP cu insertie metalica pentru instalatii sanitare, termice, hidraulice, tehnologice,`
- **data_expirare**
  - pre:  `2 ani de la receptie`
  - post: ``
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Sat Sărățel, Comuna Sieu-Magherus, Calea TeraPlast, nr. 1, Jud. Bistrița-Năsăud, 427301`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `9. ISO 9001 Tianjin.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **data_expirare**
  - pre:  `22.08.2026`
  - post: `23.08.2026`
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `A1 BuildingWuxia Industry Park Dongli DistrictWuxia Industry Park Dongli District, Tianjin City 300454, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `9. ISO 9001Tianjin.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `Tianjin KEFA Valve Co., Ltd.`
- **data_expirare**
  - pre:  `22.08.2026`
  - post: `23.08.2026`
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `A1 BuildingWuxia Industry Park Dongli DistrictWuxia Industry Park Dongli District, Tianjin City 300454, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AGT.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PROEX TOP SRL`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AT 021-05-257-2025 TERAPLAST - Tevi din PEID pt. gaz.pdf`
- **material**
  - pre:  `TEVI DIN PEID PENTRU SISTEME DE ALIMENTARE CU GAZE NATURALE`
  - post: `TEVI DIN PEID PENTRU SISTEME DE ALIMENTARE CU GAZE NATURALE / SISTEMES DE CANALIZATIONS IN HDPE POUR LA DISTRIBUTION DE COMBUSTIBILES GAZEUX`
- **data_expirare**
  - pre:  `04.06.2028`
  - post: ``
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Sat Sărățel, Com. Sieu-Măgheruș, Calea Teraplast nr. 1 judet Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AVT.pdf`
- **companie**
  - pre:  `TERAPLAST SA`
  - post: `ICECON SA`
- **adresa_producator**
  - pre:  `Urlichstrasse 25, 72116 Mâssingen Germania`
  - post: `Urlichstrasse 25, 72116 Mössingen Germania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AWWA C210.pdf`
- **companie**
  - pre:  `AKMERMER DEMİR ÇELİK TİC. VE SAN. LTD. ȘTI.`
  - post: ``
- **material**
  - pre:  `STEEL PIPES`
  - post: `Steel pipes, Length 6 to 12 m, Outside Diameter 219 mm to 1.625 mm, Wall Thickness 4 mm to 16 mm, AWWA C210-15`
- **data_expirare**
  - pre:  ``
  - post: `16.11.2026`
- **producator**
  - pre:  `AKMERMER DEMİR ÇELİK TİC. VE SAN. LTD. ȘTI.`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `MALIKÖY BAȘKENT OSB. MAH.RECEP TAYYİP ERDOĞAN BULV. NO:13 MALIKÖY/ANKARA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AWWA C210_NIMFA_EN_RO_260223_125244.pdf`
- **companie**
  - pre:  `TUV AUSTRIA TURK`
  - post: `AKMERMER DEMIR CELIK TIC.`
- **material**
  - pre:  `ȚEVI DE OȚEL`
  - post: `ȚEVI DE OȚEL, lungime 6-12m, diametru exterior 219mm-1625mm, grosime perete 4mm-16mm, standard AWWA C210-15`
- **producator**
  - pre:  `AKMERMER DEMIR CELIK TIC. VE SAN. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Agrement tehnic_Armaturi de inchidere_003-0151013-2023 expira la 27.02.2026_AVK.pdf`
- **companie**
  - pre:  `Reprezentanta AVK International A/S`
  - post: `AVK INTERNATIONAL A/S`
- **producator**
  - pre:  `AVK INTERNATIONAL A/S`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Bizonevej 1, Skovby DK – 8464 Galten Danemarca`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Agrement+ Aviz Tehnic Vane Stavilar Petrouzinex - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PETROUZINEX SRL`
- **material**
  - pre:  `VANE STAVILAR`
  - post: `Vane stăvilar fabricate din PETROUZINEX S.R.L. Piatra-Neamț`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Bd. General Nicolae Dăscălescu nr.261, 610201 Piatra-Neamț, Jud. Neamț`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Authorization Leter.pdf`
- **companie**
  - pre:  ``
  - post: `BESTAR STEEL CO.,LTD.`
- **material**
  - pre:  `steel pipes and related products (Seamless, ERW, LSAW/SAWL, SSAW, line pipe and relevant accessories)`
  - post: `Steel pipes and related products (Seamless, ERW, LSAW/SAWL, SSAW, line pipe and relevant accessories)`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Autorizatie Metal Trade-HALLS.pdf`
- **companie**
  - pre:  ``
  - post: `METALTRADE INTERNATIONAL SRL`
- **material**
  - pre:  `Teava din otel sudata elicoidal 1016x10.3 ⏎ Teava din otel sudata elicoidal 406.4x8`
  - post: `Teava din otel sudata elicoidal 1016x10.3, Teava din otel sudata elicoidal 406.4x8`
- **producator**
  - pre:  `REHAU POLYMER SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Galati, str. Calea Prutului, nr. 230, Jud. Galati`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Autorizatie de distributie - furnizor Petrouzinex - producator Saint Gobain - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `SAINT-GOBAIN`
- **material**
  - pre:  `țevi și fitinguri, vane, capace și grătare stradale din fontă ductilă`
  - post: `Țevi și fitinguri, vane, capace și grătare stradale din fontă ductilă`
- **producator**
  - pre:  `SAINT-GOBAIN PAM Canalisation`
  - post: ``
- **adresa_producator**
  - pre:  `21, avenue Camille Cavallier - BP 129, PONT-A-MOUSSON, Franța`
  - post: `21, avenue Camille Cavallier - BP 129, 54705 PONT-A-MOUSSON Cedex, FRANCE`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `AvT 003-05_1013-2023 ARMATURI INCHIDERE APA - prelungire.pdf`
- **companie**
  - pre:  ``
  - post: `AVK INTERNATIONAL A/S`
- **producator**
  - pre:  `AVK INTERNATIONAL A/S`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz Teh. 021-05-257-2025 TERAPLAST - Tevi din PEID pt. gaz.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `TERAPLAST SA`
- **material**
  - pre:  `Tevi din PEID pentru sisteme de alimentare cu gaze naturale`
  - post: `Țevi din PEID pentru sisteme de alimentare cu gaze naturale`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Sat Sărățel, Comuna Sieu-Măgheruș, Calea Teraplast nr.1, județ Bistrița-Năsăud`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz agrement 4309 DC Tevi si fit PVC-U multistrat VALPlast_21nov2027.pdf`
- **material**
  - pre:  `ȚEVI ȘI FITINGURI DIN PVC-U MULTISTRAT PENTRU INSTALAȚII SI RETELE EXTERIOARE DE CANALIZARE`
  - post: `Țevi și fitinguri din PVC-U multistrat pentru instalații și rețele exterioare de canalizare și drenare produse/e de VALROM INDUSTRIE S.R.L.`
- **data_expirare**
  - pre:  ``
  - post: `21.11.2027`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `B-dul Preciziei, Nr. 28, Sector 6, Bucuresti, Romania`
  - post: `Bd. Preciziei nr. 28, sector 6, Bucuresti, ROMANIA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz sanitar fitinguri si armaturi.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **material**
  - pre:  `Fitinguri din fontă ductilă, cu flanșe și/sau mufe gama: NATURAL DN 60-1200 mm, ISOPAM DN 100-300 mm, KLIKSO DN 63-225 mm, KAMELEO DN 80-150 mm, BLUTOP DN 75-160 mm, vane de sectionare (vane cu sertar, vane fluture), de bransament, de protecție a rețelei (de aerisire, reglare, siguranță), piese de`
  - post: `Fitinguri din fontă ductilă, cu flanșe și/sau mufe gama: NATURAL DN 60-1200 mm, ISOPAM DN 100-300 mm, KLIKSO DN 63-225 mm, KAMELEO DN 80-150 mm, BLUTOP DN 75-160 mm, vane de secționare (vane cu sertar, vane fluture), de branșament, de protecție a rețelei (de aerisire, reglare, siguranță), piese de`
- **adresa_producator**
  - pre:  `21 Camille Cavallier, 54705, Pont-ă-Mousson, Franța`
  - post: `21 Camille Cavallier, 54705, Pont-à-Mousson, Franța`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz sanitar teava fonta.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **material**
  - pre:  `Tuburi cu mufă din fontă ductilă gama: NATURAL DN 60-1000 mm, CLASIC DN 700-2000 mm, HYDROCLASS DN 100-1600 mm, STANDARD TTPE DN 80-700mm, STANDARD TT PUX DN 100-600 mm, STANDARD TT ZMU DN 100-700 mm, cu protectie interioara din mortar de ciment tip CEM III/B32,5 N-LH`
  - post: `Tuburi cu mufă din fontă ductilă gama: NATURAL DN 60-1000 mm, CLASIC DN 700-2000 mm, HYDROCLASS DN 100-1600 mm, STANDARD TTPE DN 80-700mm, STANDARD TT PUX DN 100-600 mm, STANDARD TT ZMU DN 100-700 mm, cu protecție interioară din mortar de ciment tip CEM III/B32,5 N-LH`
- **producator**
  - pre:  `SAINT - GOBAIN PAM CANALISATION`
  - post: `SAINT – GOBAIN PAM CANALISATION`
- **adresa_producator**
  - pre:  `21 Camille Cavallier, 54705, Pont-ă-Mousson, Franța`
  - post: `21 Camille Cavallier, 54705, Pont-à-Mousson, Franța`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz si agrement nr 4076_DC_Tevi si fit PEHD gaze Valrom.pdf`
- **material**
  - pre:  `TEVI SI FITINGURI PEHD <GasKIT>`
  - post: `TEVI SI FITTINGURI DIN PEID PENTRU SISTEME DE ALIMENTARE CU GAZE NATURALE; Tevi GasPRO cu strat protector sunt tevi din PE100RC, SDR 11, diam.ext. 25 ÷ 600mm, iar la exterior au un strat exfoliat din material termoplastic de culoare galbena`
- **data_expirare**
  - pre:  ``
  - post: `27.06.2027`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `B-dul Preciziei, Nr. 28, Sector 6, Bucuresti, Romania`
  - post: `Blv. Preciziei nr. 28, sector 6, București, ROMÂNIA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz si agrement nr 4076_Tevi si fit PEHD gaze Valrom_DC.pdf`
- **material**
  - pre:  `TEVI SI FITINGURI DIN PEID PENTRU ALIMENTARE CU GAZE NATURALE`
  - post: `Țevi și fitinguri din PEID pentru sisteme de alimentare cu gaze naturale, diverse dimensiuni, SDR 11 PE80, SDR11 PE100, SDR11 PE 100RC`
- **data_expirare**
  - pre:  `20.05.2025`
  - post: `27.06.2027`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `B-dul Preciziei, Nr. 28, Sector 6, Bucuresti, Romania`
  - post: `B-dul Preciziei, nr. 28, Sector 6, Bucuresti, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz tehnic Saint Gobain 003 05 1279 2025.pdf`
- **companie**
  - pre:  `CONSILIUL TEHNIC PERMANENT PENTRU CONSTRUCȚII`
  - post: `PROCEMA CERCETARE SRL`
- **adresa_producator**
  - pre:  `54705 PONT-A-MOUSSON CEDEX, Franta`
  - post: `54705 PONT-A-MOUSSON CEDEX, Franța`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz tehnic si Agrement tehnic _Boma.pdf`
- **material**
  - pre:  `PROCEDEU DE REALIZARE AL ELEMENTELOR PREFABRICATE DIN BETON VIBRO-PRESAT`
  - post: `Elementelor prefabricate din beton vibro-presat`
- **producator**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Localitatea Strejnicu, DN 1A, km 62+200, judetul Prahova`
  - post: `Localitatea Strejnicu, DN 1A, km 62+200, județul Prahova`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz tehnic_Armaturi de inchidere apa_27.02.2025_AVK.pdf`
- **material**
  - pre:  `ARMĂTURI DE INCHIDERE PENTRU INSTALAȚII DE APĂ`
  - post: `Armături de închidere pentru instalații de apă, produse de AVK INTERNATIONAL A/S`
- **producator**
  - pre:  `AVK INTERNATIONAL A/S, Danemarca`
  - post: `AVK INTERNATIONAL A/S`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Aviz-agrement-tehnic-4014-DC-Tevi si fit PEHD Water VLR.pdf`
- **material**
  - pre:  `CONDUCTE SI FITINGURI DIN PEID <WaterKIT>`
  - post: `Conducte și fitinguri din PEID pentru instalații de apă`
- **data_expirare**
  - pre:  ``
  - post: `25.10.2025`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `B-dul Preciziei, Nr. 28, Sector 6, Bucuresti, Romania`
  - post: `Bd. Preciziei, nr. 28, sector 6, Bucuresti, ROMANIA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CC 15_ sablon CC teava PVC multistrat EN 13476-2_draft_lungime utila.pdf`
- **material**
  - pre:  `Teava PVC multistrat cu mufa si garnitura`
  - post: `Teava PVC multistrat cu mufa si garnitura, SR EN 13476-2, SR EN 1401-1`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc Jud: RO87BACX0000003023781012`
  - post: `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CC 8 SABLON CC TEAVA GAZ PE100_draft.pdf`
- **material**
  - pre:  `Teava PE (conform EN 1555-1-2)`
  - post: `Produs conform SR EN 1555-1-2`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc: Jud: RO87BACX0000003023781012`
  - post: `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CC- Akmermer.pdf`
- **material**
  - pre:  `STEEL PIPES`
  - post: `Steel pipes, Length 6-12m, Outside diameter 219mm-1.625mm, Wall thickness 4-16mm, AWWA C210-15 Liquid-Epoxy Coatings and Linings`
- **data_expirare**
  - pre:  ``
  - post: `16.11.2026`
- **producator**
  - pre:  `AKMERMER DEMİR ÇELİK TİC. VE SAN. LTD. ȘTI.`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `MALIKÖY BAȘKENT OSB. MAH.RECEP TAYYİP ERDOĞAN BULV. NO:13 MALIKÖY/ANKARA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CC-01740.1 PE typ 2.pdf`
- **companie**
  - pre:  `TERAPLAST SA`
  - post: `ICECON CERT`
- **material**
  - pre:  `ȚEVI “POLITUB” MULTISTRAT DIN POLIETILENA (strat interior/exterior PE 100RC si strat exterior/interior PE 100)`
  - post: `TEVI "POLITUB" MULTISTRAT DIN POLIETILENĂ (strat interior/exterior PE 100RC și strat exterior/interior PE 100), PENTRU ALIMENTARE CU APĂ POTABILĂ`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Comuna ȘIEU-MĂGHERUȘ, Sat SĂRĂȚEL, Calea Teraplast nr. 1, jud. BISTRIȚA-NĂSĂUD`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CE BBK  Valve Group - traducere .pdf`
- **companie**
  - pre:  `EUROCERT SA`
  - post: `BBK VALVE GROUP CO., LTD`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CE-BBK Valve Group .pdf`
- **companie**
  - pre:  `EUROCERT SA`
  - post: `EURO CERT`
- **material**
  - pre:  `Industrial Valves, Y Strainer, Dismanlting Joint`
  - post: `Industrial Valves, Y Strainer, Dismantling Joint`
- **data_expirare**
  - pre:  `14.09.2026`
  - post: `15.09.2023`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `BIB VALVE GROUP CO., LTD.`
- **adresa_producator**
  - pre:  `603, No.99 YuShan Road, SuZhou, China`
  - post: `603, No.99 Yuzhao Road, SuZhou, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CERT BOMA SISTEM RC 2025.pdf`
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Str. Iederii, Nr. 2, Alba Iulia, Jud. Alba`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CERTIFICAT CONFORMITATE.pdf`
- **material**
  - pre:  `PSI EndiT KT Casing End Seal`
  - post: `PSI EndiT KT Casing End Seal, EPDM, Stainless steel`
- **data_expirare**
  - pre:  ``
  - post: `11.09.2025`
- **producator**
  - pre:  `PSI Products GmbH`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Ulrichstrasse 25 72116 Mossingen Germany`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CERTIFICAT DE CONFORMITATE tuburi,camine circulare si rectangulare 2028.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `AEROQ SA`
- **material**
  - pre:  `TUBURI Si ACCESORI DIN BETON SIMPLU, BETON SLAB ARMAT, BETON ARMAT- TUBURI 2 500, @ 600, @ 800, 3 1000, @ 1250, B 1500, a 2000, REDUCTIE TRONCONICA 8 1000/ @ 800mm: @ 800/ @ 600mm si gura de scurgere DN 500 mm ⏎ CAMINE DE VIZITARE SI CAMINE DE RACORD DIN BETON SIMPLU, BETON SLAB ARMAT, BETON ARMAT`
  - post: `TUBURI SI ACCESORII DIN BETON SIMPLU, BETON SLAB ARMAT - TUBURI Ø 500, Ø 600, Ø 800, Ø 1000, Ø 1250, Ø 1500, Ø 2000; REDUCTIE TRONCONICA Ø 1000/ Ø 800mm; Ø 800/ Ø 600mm si gura de scurgere DN 500 mm; CAMINE DE VIZITARE SI CAMINE DE RACORD DIN BETON SIMPLU, BETON SLAB ARMAT (CIRCULARE SAU`
- **data_expirare**
  - pre:  ``
  - post: `28.09.2025`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Soseaua Giurgiului, nr.5, Jilava, Jud. Ilfov`
  - post: `Strada Feleacu, nr. 14 B, Sector 1, Bucuresti, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CERTIFICATE IRD BOMA DE SISTEM VIZA 2025.pdf`
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Str. Iederii, Nr. 2, Alba Iulia, Jud. Alba`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CERTIFICATE IRD Bomade PRODUS  viza 2025.pdf`
- **material**
  - pre:  `PRODUSE PREFABRICATE DIN BETON. CAMINE DE VANE ⏎ BAZINE CILINDRICE PENTW STATII DE POMPARE`
  - post: `PRODUSE PREFABRICATE DIN BETON, CAMINE DE VANE (CONFORM PROIECT UNIC PRODUS) ⏎ BAZINE CILINDRICE PENTRU STATII DE POMPARE (CONFORM PROIECT UNIC PRODUS)`
- **data_expirare**
  - pre:  ``
  - post: `13.09.2027`
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Alba Iulia, str. Iederii, Nr. 2, Jud. Alba`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `CPR- eng- Akmermer.pdf`
- **material**
  - pre:  `Components for Aluminium and Steel structures`
  - post: `Load bearing steel components up to EXC 3 acc. EN 1090-2, EN1090-1:2009+A1:2011`
- **producator**
  - pre:  `AKMERMER DEMİR ÇELİK TİC. VE SAN. LT D. ȘTİ.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Catalog teava fara sudura producator LUZHENG - semnat.pdf`
- **companie**
  - pre:  ``
  - post: `SHANDONG LUXING STEEL PIPE CO., LTD`
- **material**
  - pre:  `Țeavă magistrală PSL1&PSL2 ⏎ Țeavă magistrală pentru servicii cu sulf ⏎ Țevi de foraj (tubing) ⏎ ȚEVI DIN OȚEL NEGRU FĂRĂ SUDURĂ ⏎ ȚEVI FĂRĂ SUDURĂ DIN OȚEL CARBON ⏎ ȚEVI FĂRĂ SUDURĂ DIN OȚEL CARBON ⏎ ȚEVI FĂRĂ SUDURĂ DIN OȚEL CARBON MEDIU ⏎ ȚEVI FĂRĂ SUDURĂ DIN OȚEL ALIAT FERITIC ȘI AUSTENITIC ⏎ ȚEVI DIN OȚEL`
  - post: `Teava de otel`
- **producator**
  - pre:  `Shandong Luxing Steel Pipe Co., Ltd.`
  - post: ``
- **adresa_producator**
  - pre:  `959 Luxing Road, Qingzhou City, Shandong`
  - post: `Add: Luxing Road, Qingdao City, Shandong Province, P.R. China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Catalog teava fara sudura producator LUZHENG - semnat.pdf`
- **companie**
  - pre:  ``
  - post: `Shandong Luxing Steel Pipe Co., Ltd`
- **material**
  - pre:  `Țevi din oțel fără sudură`
  - post: `Hot-rolled seamless steel pipe`
- **producator**
  - pre:  `Shandong Luxing Steel Pipe Co., Ltd.`
  - post: ``
- **adresa_producator**
  - pre:  `959 Luxing Road, Qingzhou City, 262517 Shandong`
  - post: `Add: Luxing Road, Qingdao City, Shandong Province, P.R.China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat 01381.1 - tevi PE gaz tip 1,2,3.pdf`
- **material**
  - pre:  `Țevi “POLITUB” din polietilenă, pentru sisteme de alimentare cu gaze naturale`
  - post: `Țevi "POLITUB" din polietilenă, pentru sisteme de alimentare cu gaze naturale, PE 100, PE 100RC, DN Ø20 - Ø800, SDR 11, 17`
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast nr. 1, jud. BISTRIȚA-NĂSĂUD`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat API 5L producator Huayang - semnat.pdf`
- **companie**
  - pre:  `HEBEI HUA YANG STEEL PIPE CO., LTD.`
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD.`
- **material**
  - pre:  `țeavă pentru transport (Line Pipe)`
  - post: `Line Pipe Plain End, Steel Pipe`
- **data_expirare**
  - pre:  ``
  - post: `24.07.2027`
- **adresa_producator**
  - pre:  ``
  - post: `Hope New District ⏎ Mengcun County ⏎ Cangzhou, Hebei ⏎ People's Republic of China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat API 5L producator Huayang - semnat.pdf`
- **companie**
  - pre:  `HEBEI HUA YANG STEEL PIPE CO., LTD.`
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD.`
- **material**
  - pre:  `țeavă pentru transport (Line Pipe)`
  - post: `Line Pipe Plain End, Type of Pipe: HFW / Delivery Condition: R / Max. Grade: X65, X70; SAW / Delivery Condition: M / Max. Grade: X60, X52`
- **data_expirare**
  - pre:  ``
  - post: `24.07.2027`
- **adresa_producator**
  - pre:  ``
  - post: `Hope New District ⏎ Mengcun County ⏎ Cangzhou, Hebei ⏎ People's Republic of China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat CE PED 2014-68-EU teava fara sudura producator LUZHENG - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **material**
  - pre:  `țevile fără sudură din oțeluri feritice`
  - post: `Seamless pipes in ferritic steels`
- **producator**
  - pre:  `WEIFANG LUZHENG INDUSTRY AND TRADE CO., LTD.`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `No. 13-14, C District, Zhongrui Iron and steel Logistic Park, Qingzhou City Weifang City, Shandong Province, 262500 P. R. China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat CE PED 2014-68-EU teava fara sudura producator LUZHENG - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **material**
  - pre:  `țevile fără sudură din oțeluri feritice`
  - post: `Seamless pipes in ferritic steels`
- **producator**
  - pre:  `WEIFANG LUZHENG INDUSTRY AND TRADE CO., LTD.`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `No. 13-14, C District, Zhongrui Iron and steel Logistic Park, Qingzhou City Weifang City, Shandong Province, 262500 P. R. China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat CE PED producator Huayang - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `Hebei Huayang Steel Pipe Co., Ltd`
- **material**
  - pre:  `țevi sudate din oțel P235TR1 ,P265TR1 ,P235TR2, P265TR2 EN10217-1:2019, teava sudata P235GH,P265GH EN10217-2:2019, teava sudata P235GH,P265GH EN10217-5:2019, teava sudata P215NL,P265NL EN10217-6:2019`
  - post: `welded steel tubes`
- **data_expirare**
  - pre:  `10.08.2026`
  - post: `08.10.2026`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `Hope New Area, Mengcun Hui Autonomous County, Cangzhou City, Hebei, P.R. China, 061400`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat CE PED producator Huayang - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `Hebei Huayang Steel Pipe Co., Ltd`
- **material**
  - pre:  `țevi sudate din oțel`
  - post: `Welded steel tubes`
- **data_expirare**
  - pre:  `10.08.2026`
  - post: `08.10.2026`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `Hope New Area, Mengcun Hui Autonomous County, Cangzhou City, Hebei, P.R. China, 061400`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 14001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11-2027`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 14001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11-2027`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 14001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `20.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 45001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 45001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 45001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 9001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 9001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 9001 SRAC 2025_2026.pdf`
- **data_expirare**
  - pre:  `24.11.2028`
  - post: `11.11.2026`
- **adresa_producator**
  - pre:  `B-dul. Preciziei, nr. 28, sector 6, Bucuresti`
  - post: `B-dul. Preciziei, nr. 28, sector 6, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat ISO 9001_valabil 2029 SEMNAT.pdf`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de excludere de la marcajul CE Compensatori de montaj producator Tianjin KEFA Valve Co.Ltd.pdf`
- **companie**
  - pre:  ``
  - post: `TIANJIN KEFA VALVE CO.,LTD`
- **producator**
  - pre:  `TIANJIN KEFA VALVE CO.,LTD`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de testare 3.1 MTC 508x8 HUAYANG (MODEL) - semnat.pdf`
- **companie**
  - pre:  ``
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD`
- **material**
  - pre:  `Teava de oțel LSAW`
  - post: `Teava de otel LSAW EN10204-3.1`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `ADD:MENGcun COUNTY,CANGZHOU CITY,HEBEI,CHINA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de testare 3.1 MTC 508x8 HUAYANG (MODEL) - semnat.pdf`
- **companie**
  - pre:  ``
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD`
- **material**
  - pre:  `Teava de oțel LSAW`
  - post: `Teava de otel LSAW EN10204-3.1`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `ADD:MENGCUN COUNTY,CANGZHOU CITY HEBEI,CHINA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de testare 3.1 MTC 711x8 HUAYANG (MODEL) - semnat.pdf`
- **companie**
  - pre:  ``
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD`
- **material**
  - pre:  `Teava de oțel LSAW`
  - post: `LSaw Steel Pipe`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `ADD:MENGcun COUNTY CANGZHOU CITY HEBEI, CHINA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de testare 3.1 MTC 711x8 HUAYANG (MODEL) - semnat.pdf`
- **companie**
  - pre:  ``
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD`
- **material**
  - pre:  `Teava de otel LSAW`
  - post: `LSAW STEEL PIPE`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `ADD: MENGcun COUNTY CANGZHOU CITY HEBEI, CHINA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de testare 3.1 MTC 813x8 HUAYANG (MODEL) - semnat.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD`
- **material**
  - pre:  `Teavă de oțel LSAW ISO 3183 PSL2`
  - post: `LSAW STEEL PIPE`
- **data_expirare**
  - pre:  ``
  - post: `20.12.2023`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `ADD:MENGUN COUNTY CANGZHOU CITY HEBEI, CHINA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat de testare 3.1 MTC 813x8 HUAYANG (MODEL) - semnat.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `HEBEI HUAYANG STEEL PIPE CO., LTD`
- **data_expirare**
  - pre:  ``
  - post: `20.12.2023`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `ADD: MENG CUN COUNTY CANGZHOU CITY HEBEI, CHINA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat_14001_ro.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat_45001_ro.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificat_9001_ro.pdf`
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Calea Teraplast, Nr. 1, Sat Saratel, Comuna Sieu-Magherus, 427301, Jud. Bistrita-Nasaud, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificate SIM 2028.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `PRECON SRL`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificate de conformitate2025_2028.pdf`
- **material**
  - pre:  `Tevi din PVC-U VALPLast by VALROM pentru evacuare, canalizare și drenaj, fară presiune, subterane cu suprafata interioară și exterioară netedă si pentru sistem, tip A, DN110 mm + 630 mm, SN2 + SN16. Marca VALPlast ⏎ Tevi din polietilenă monostrat, dublustrat și triplustrat coextrudate și cu strat`
  - post: `Tevi din PVC-U VALPLAST BY VALROM pentru evacuare, canalizare si drenaj, fără presiune, subterane sau supraterane interioară și exterioară netedă și pentru sistem, tip A, DN 110 mm - 630 mm, SN4, SN16. Marca VALPLAST.`
- **data_expirare**
  - pre:  ``
  - post: `28.08.2028`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `bd. Preciziei, nr. 9, sector 6, Bucuresti, România`
  - post: `bd. Preciziei, nr. 28, sector 6, București, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Certificate de conformitate2025_2028.pdf`
- **material**
  - pre:  `Tevi din PVC-U VALPlast by VALROM pentru evacuare, canalizare și drenaj, fără presiune, subterane cu suprafata interioară și exterioară netedă si pentru sistem, tip A, DN110 mun + 630 mm, SN2 + SN16. Marca VALPlast ⏎ Tevi din polietilenă monostrat, dublustrat și triplustrat coextrudate și cu strat`
  - post: `Tevi din PVC-U VALPLAST by VALROM pentru evacuare, canalizare si drenaj, stații presiune, subterane sau supraterane interioară și exterioară netedă și pentru sistem, tip A, DN 110 mm - 630 mm, SN4, SN16. Marca VALPLAST.`
- **data_expirare**
  - pre:  ``
  - post: `28.08.2028`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `bd. Preciziei, nr. 9, sector 6, Bucuresti, România`
  - post: `bd. Preciziei, nr. 28, sector 6, București, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Cot 45 cu mufe Standard_PECB.pdf`
- **companie**
  - pre:  ``
  - post: `SAINT-GOBAIN`
- **adresa_producator**
  - pre:  ``
  - post: `SAINT-GOBAIN PAM CANALISATION 4 Quai de Coubervoie - BP 40 54705 PONT-A-MOUSSON Cedex FRANCE`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Cuplaje_coliere_compensatori_fittinguri_AVK_aviz_sanitar.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `VESTRA INDUSTRY SRL`
- **material**
  - pre:  `Cuplaje, adaptoare cu flanșă, coliere de reparație, compensatori de montaj AVK seriile: 05, 10, 100, 258, 259, 260, 265, 601, 602, 603, 621, 623, 631, 632, 633, 634, 635, 745, 749, 727, 730, 873, 800X; Fitinguri AVK seriile: 712, LOX Supa Lock și Filtru Y AVK seria: 910`
  - post: `Cuplaje, adaptoare cu flanșă, coliere de reparație, compensatori de montaj AVK seriile: 05, 10, 100, 258, 259, 260, 265, 601, 602, 603, 621, 623, 631, 632, 633, 634, 635, 745, 748, 727, 730, 873, 800X DN40 - DN2200, PN10, PN16, PN25; Fitinguri AVK seriile: 712, 10X Supa Lock, DN20 – DN600, PN10,`
- **producator**
  - pre:  `AVK TNTERNATTONAL A/S`
  - post: `AVK INTERNATIONAL A/S`
- **adresa_producator**
  - pre:  `Str. Uzinei nr. 1, Valcea`
  - post: `Str. Mihai Eminescu nr. 85, sat Cătămărești Deal, comuna Mihai Eminescu, Județul Botoșani, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC 10  PVC  DE250 SN8_draft.pdf`
- **material**
  - pre:  `TEVI MULTISTRAT DIN PVC-U PENTRU INSTALATII DE CANALIZARE SI DRENAJ DE 250 SN8`
  - post: `Tevi multistrat din PVC-U pentru instalatii de canalizare si drenaj`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C. TEHNO WORLD S.R.L., Loc. Baia nr. 161E - Jud. Suceava - România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC 21 PVC  DE160 SN8_draft.pdf`
- **material**
  - pre:  `TEVI MULTISTRAT DIN PVC-U PENTRU INSTALATII DE CANALIZARE SI DRENAJ DE160 SN8`
  - post: `Tevi multistrat din PVC-U pentru instalatii de canalizare si drenaj TEVI MULTISTRAT DIN PVC-U DN160 SN8`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C TEHNO WORLD S.R.L., Loc. Balți nr. 1616 – jud. Suceava – România, Tel: 0743 289 657, e-mail: office@tehnoworld.ro, www.tehnoworld.ro`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC 24 PVC  DE200 SN8_draft.pdf`
- **material**
  - pre:  `TEVI MULTISTRAT DIN PVC-U PENTRU INSTALATII DE CANALIZARE SI DRENAJ DE 200 SN8`
  - post: `Tevi multistrat din PVC-U pentru instalatii de canalizare si drenaj`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C. TEHNO WORLD S.R.L., Loc. Balca nr. 1616 – jud. Suceava – România, Tel. 0743 269 867, e-mail: office@tehnoworld.ro, www.tehnoworld.ro`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC 29 PVC  DE315 SN8_draft.pdf`
- **material**
  - pre:  `TEVI MULTISTRAT DIN PVC-U PENTRU INSTALATII DE CANALIZARE SI DRENAJ DE 315 SN8`
  - post: `TEVI MULTISTRAT DIN PVC-U PENTRU INSTALATII DE CANALIZARE SI DRENAJ 315 SN8`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C. TEHNO WORLD S.R.L., Loc. Balți nr. 1616 – jud. Suceava – România, Tel. 0743 269 827, e-mail: office@tehnoworld.ro, www.tehnoworld.ro`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC 32 PVC  DE400 SN8_draft.pdf`
- **material**
  - pre:  `TEVI MULTISTRAT DIN PVC-U PENTRU INSTALATII DE CANALIZARE SI DRENAJ DE 400 SN8`
  - post: `Tevi multistrat din PVC-U pentru instalatii de canalizare si drenaj de 400 SN8`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C. TEHNO WORLD S.R.L., Loc. Balți nr. 1616 – jud. Suceava – România, Tel. 0743 359 857, e-mail: office@tehnoworld.ro, www.tehnoworld.ro`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC 36 Teava gaz PEHD_draft.pdf`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia nr. 1616 – jud. Suceava – România`
  - post: `S.C. TEHNO WORLD S.R.L., Loc. Baia nr. 1616, jud. Suceava - Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DC-Placa+capac.pdf`
- **companie**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: `BOMA PREFABRICATE`
- **material**
  - pre:  `ELEMENTE PENTRU CAMINE DIN BETON, placi de acoperire din beton armat: rama rectangulara cu capac de fonta inglobat total`
  - post: `Elemente pentru camine din beton, placi de acoperire din beton armat: rama rectangulara cu capac de fonta`
- **data_expirare**
  - pre:  `12.06.2020`
  - post: ``
- **producator**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Platforma Industrială Florea Grup, Sat Strejnicu, Com. Tîrgșorul Vechi, DNI A KM62+200, Jud. Prahova`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DOC TUB PROTECTIE.pdf`
- **companie**
  - pre:  `REHAU POLYMER SRL`
  - post: `METALTRADE INTERNATIONAL SRL`
- **data_expirare**
  - pre:  `05.06.2025`
  - post: `05.06.2026`
- **adresa_producator**
  - pre:  `Calea Prutului nr. 230, Galați, Jud. Galați, Romania`
  - post: `Galati, strada Portului, nr. 56, biroul 17, et.1, judetul Galati ⏎ Galati, strada Bazinul Nou, nr. 20, Zona Libera, hala industriala/depozit vamal, judetul Galati ⏎ Galati, Calea Prutului, nr. 230 Prelungire Magazia 3, judetul Galati ⏎ Galati, teren`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DOC001.pdf`
- **material**
  - pre:  `Produse diverse (autorizatie generala)`
  - post: `Materiale pentru piața instalațiilor și construcțiilor`
- **data_expirare**
  - pre:  `Pe durata contractului`
  - post: ``
- **producator**
  - pre:  `TERAPLAST SA`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `sat. Sărățel, com. Șieu-Măgheruș, Calea Teraplast, nr. 1, jud. Bistrița-Năsăud, România`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DOP gas pipe   eng.pdf`
- **producator**
  - pre:  `TEHNO WORLD SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Loc. Baia, nr. 1616, DN 2E km 2 - Suceava – ROMANIA`
  - post: `Loc. Baia, nr. 1616, DN2E km 2 Jud. Suceava, RO-727020`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DP - Inel D1000x1000.pdf`
- **companie**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: `BOMA PREFABRICATE`
- **material**
  - pre:  `ELEMENTE PENTRU CĂMINE DIN BETON SIMPLU, inel pentru cămin, Diametru interior / Ȋnălțime / Grosime 1000 / 1000 / 120`
  - post: `Elemente pentru cămine din beton simplu, inel pentru cămin, dimensiuni 1000/1000/120, SR EN 1917:2003`
- **data_expirare**
  - pre:  `12.06.2020`
  - post: ``
- **producator**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Platforma Industrială Florea Grup, Sat Strejnicu, Com. Tîrgșorul Vechi, DNI A KM62+200, Jud. Prahova`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DP-Inel D1000x250.pdf`
- **companie**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: `BOMA PREFABRICATE`
- **material**
  - pre:  `ELEMENTE PENTRU CĂMINE DIN BETON SIMPLU, inel pentru cămin D1000x250`
  - post: `Elemente pentru cămine din beton simplu, inel pentru cămin, dimensiuni 1000/250/120 mm, SR EN 1917:2003; SR EN 1917:2003/AC:2008`
- **data_expirare**
  - pre:  `12.06.2020`
  - post: ``
- **producator**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Platforma Industrială Florea Grup, Sat Strejnicu, Com. Tîrgșorul Vechi, DN1 A KM62+200, Jud. Prahova`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DP-Inel D1000x500.pdf`
- **companie**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: `BOMA PREFABRICATE`
- **material**
  - pre:  `Elemente pentru cămine din beton simplu, inel pentru cămin D1000x500`
  - post: `Elemente pentru cămine din beton simplu, inel pentru cămin, dimensiuni 1000/500/120`
- **data_expirare**
  - pre:  `12.06.2020`
  - post: ``
- **producator**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Platforma Industrială Florea Grup, Sat Strejnicu, Com. Tîrgșorul Vechi, DN1 A KM62+200, Jud. Prahova`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `DP-Inel D1000x750.pdf`
- **companie**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: `BOMA PREFABRICATE`
- **material**
  - pre:  `Inel pentru cămin D1000x750`
  - post: `Elemente pentru cămine din beton simplu, inel pentru cămin, dimensiuni 1000/750/120 mm, SR EN 1917:2003; SR EN 1917:2003/AC:2008`
- **data_expirare**
  - pre:  `12.06.2020`
  - post: ``
- **producator**
  - pre:  `BOMA PREFABRICATE SRL`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Platforma Industrială Florea Grup, Sat Strejnicu, Com. Tîrgșorul Vechi, DNI A KM62+200, Jud. Prahova`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Data sheet WaterKIT PE100CERT pipes_vers vers 2.3 02.02.2026.pdf`
- **companie**
  - pre:  ``
  - post: `VALROM INDUSTRIE SRL`
- **material**
  - pre:  `PE100 CERT VALWater PIPES for DRINKING WATER`
  - post: `Conducte PE100 CERT din polietilena de inalta densitate pentru apa potabila`
- **data_expirare**
  - pre:  ``
  - post: `28.02.2025`
- **producator**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Valrom Industrie SRL J1996004810406 ROB529679 2A Preciziei Blvd. 6° District 062206 Bucuresti, Romania`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Declaratie grosime si rugozitate izolatie interioara producator Huayang (MODEL) - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `HEBEI HUAYANG STEEL PIPE CO.,LTD`
- **material**
  - pre:  `Țevi izolate`
  - post: `Tevi izolate, grosime minima a stratului interior de izolatie de 100 microni si o rugozitate maxima de 10 microni`
- **data_expirare**
  - pre:  ``
  - post: `08.04.2025`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `Add:Mengcun Cangzhou, Hebei Province, China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Declaratie grosime si rugozitate izolatie interioara producator Huayang (MODEL) - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `HEBEI HUAYANG STEEL PIPE CO.,LTD`
- **material**
  - pre:  `Tevi izolate`
  - post: `Tevi izolate, grosime minima a stratului interior de izolatie de 100 microni si o rugozitate maxima de 10 microni`
- **data_expirare**
  - pre:  ``
  - post: `08.04.2025`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `Add:Mengcun Cangzhou City Hebei Province China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Declaratie uzilizare gaz natural cu continut de hidrogen producator Huayang (MODEL) - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `HEBEI HUAYANG STEEL PIPE CO.,LTD`
- **material**
  - pre:  `Țevi pentru gaz natural cu conținut de hidrogen de 20%`
  - post: `Țevi oferite pentru licitația "Mihai Bravu", CN1078286, Section 1, adecvate pentru utilizare în mediu de gaz natural cu un conținut de hidrogen de 20%.`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `Add:Mencun Cangzhou City Hebei Province China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Declaratie uzilizare gaz natural cu continut de hidrogen producator Huayang (MODEL) - semnat.pdf`
- **companie**
  - pre:  `VALROM INDUSTRIE SRL`
  - post: `HEBEI HUAYANG STEEL PIPE CO.,LTD`
- **material**
  - pre:  `Țevi pentru gaz natural cu conținut de hidrogen de 20%`
  - post: `tevi oferite pentru licitatia "Mihai Bravu", CN1078286, Sectiunea 1, adecvate pentru utilizare in mediu de gaz natural cu un continut de hidrogen de 20%.`
- **data_expirare**
  - pre:  ``
  - post: `08.04.2025`
- **producator**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **adresa_producator**
  - pre:  `Yongjia County, Wenzhou City, Zhejiang Province, China`
  - post: `Add:Mengcun Cangzhou City Hebei Province China`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `Documente FAM.pdf`
- **material**
  - pre:  `Robinete și vanele cu sertar pentru instalatii de apă`
  - post: ``
- **producator**
  - pre:  `HENKEL AG`
  - post: ``
- **adresa_producator**
  - pre:  `Str. Industriei nr. 3, Bistrita, Bistrita-Nasaud`
  - post: `Str. Luica, Nr. 15, Cam. 1, Bl. 4, Sc. 2, Et. 6, Ap. 105, Sector 4, București`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EN 10217-1.pdf`
- **material**
  - pre:  `STEEL PIPES`
  - post: `STEEL PIPES, Lungime: 6 to 12 m, Diametru exterior: 219 mm to 1.625 mm, Grosime perete: 4 mm to 16 mm, EN 10217-1:2019`
- **data_expirare**
  - pre:  ``
  - post: `21.11.2026`
- **producator**
  - pre:  `AKMERMER DEMIR GELIK TIC. VE SAN. LTD. ȘTI.`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `MALIKÖY BAȘKENT OSB. MAH.RECEP TAYYİP ERDOĞAN BULV. NO:13 MALIKÖY/ANKARA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EN 10217-1_RO_260219_153142.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: `AKMERMER DEMIR CELIK TIC.`
- **material**
  - pre:  `ȚEVI DE OȚEL`
  - post: `Țevi de oțel, Lungime: 6 până la 12 m, Diametru exterior: 219 mm până la 1.625 mm, Grosimea peretelui: 4 mm până la 16 mm, EN 10217-1:2019`
- **producator**
  - pre:  `AKMERMER DEMIR CELIK TIC. VE SA. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EN 10289.pdf`
- **companie**
  - pre:  `TUV AUSTRIA TURK`
  - post: ``
- **material**
  - pre:  `Spiral Welded Steel Pipes`
  - post: `Spiral Welded Steel Pipes, Length: 6 m to 12 m, Outside diameter: 219,1 - 1625 mm, Wall Thickness: 4 mm to 20 mm, EN 10289:2002`
- **data_expirare**
  - pre:  ``
  - post: `12.01.2028`
- **producator**
  - pre:  `AKMERMER DEMIR CELIK TIC. VE SAN. LTD. STI.`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Malıköy Bașkent OSB. Mah. Recep Tayyip Erdoğan Bulv. No:13 Malıköy/Ankara/Türkiye`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EN 10289_RO.pdf`
- **companie**
  - pre:  `ZHEJIANG HUAYANG PIPELINE INDUSTRY CO LTD`
  - post: ``
- **material**
  - pre:  `Țevi din oțel sudate spiralat`
  - post: `Țevi din oțel sudate spiralat, lungime 6-12 m, diametru exterior 219,1-1625 mm, grosime perete 4-20 mm, EN 10289:2002`
- **producator**
  - pre:  `AKMERMER DEMIR CELIK TIC. VE SA. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EN 1090-1_NIMFA_EN_RO_260223_125207.pdf`
- **companie**
  - pre:  `AKMERMER DEMIR CELIK. TIC. VE SAN. LTD. ȘTI.`
  - post: ``
- **material**
  - pre:  `Componente pentru structuri din aluminiu și oțel`
  - post: `Componente din oțel portante până la EXC 3 conf. EN 1090-2, conform EN1090-1:2009+A1:2011`
- **producator**
  - pre:  `AKMERMER DEMIR CELIK. TIC. VE SAN. LTD. ȘTI.`
  - post: ``
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EPOXY 18521 KANEPOX LINING FREE Rev No 11-ENG.pdf`
- **companie**
  - pre:  ``
  - post: `KANAT`
- **material**
  - pre:  `18521 KANEPOX LINING FREE`
  - post: `18521 KANEPOX LINING FREE, vopsea epoxi-poliamina bicomponenta`
- **producator**
  - pre:  `KANAT`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Kemalpașa O.S.B. Mah. İzmir Ankara Yolu No:321 Kemalpașa - İzmir/TURKEY Phone: 0 232 878 95 00 Fax: 0 232 878 95 95 info@kanatboya.com.tr www.kanatboya.com.tr`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EPOXY 18521 KANEPOX LINING FREE_RO.pdf`
- **companie**
  - pre:  ``
  - post: `KANAT`
- **material**
  - pre:  `18521 KANEPOX LINING FREE`
  - post: `18521 KANEPOX LINING FREE, produs de acoperire pe bază de poliamină epoxidică, alcalinitate în două componente`
- **producator**
  - pre:  `KANAT Project Group`
  - post: ``
- **adresa_producator**
  - pre:  ``
  - post: `Kemalpașa O.S.B. Mah. Izmir Ankara Yolu No. 321 Kemalpașa - Izmir/TURCIA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`

### `EPOXY 1852113010L KANAT KANEPOX_RO.pdf`
- **companie**
  - pre:  `TERAPLAST SA`
  - post: `KANAT PAINTS&COATINGS`
- **material**
  - pre:  `KANEPOX LINING FREE C 3010 O.KIRMIZI`
  - post: `KANEPOL LINING FREE C 3010 O.KIRMIZI`
- **producator**
  - pre:  `KANAT Boyacilik Tic. ve San. A.S.`
  - post: ``
- **adresa_producator**
  - pre:  `Kemalpașa O.S.B. Mah. Izmir Ankara Yolu No. 321 KEMALPAȘA 35730 IZMIR – TURCIA`
  - post: `Kemalpasa O.S.B. Mah. Izmir Ankara Yolu No. 321 KEMALPAȘA 35170 İZMIR - TURCIA`
- **extraction_model**
  - pre:  `google/gemini-2.0-flash-001`
  - post: `vision:gemini-2.0-flash`
