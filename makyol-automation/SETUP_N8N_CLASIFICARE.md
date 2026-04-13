# Setup Workflow n8n — Clasificare Documente PDF Makyol

## Arhitectura

```
PDF Input
    |
    v
[1. Citeste Folder] --> [2. Clasificare Filename (Regex)]
                              |
                              v
                        [3. Necesita AI?]
                         /            \
                    DA /                \ NU
                      v                  v
              [4a. Prep Text]    [4b. Rezultat Direct]
                    |                    |
                    v                    |
              [5a. AI OpenRouter]        |
                    |                    |
                    v                    |
              [6a. Parse Raspuns]        |
                    \                  /
                     v              v
                   [7. Merge Rezultate]
                          |
                          v
                   [8. Mapeaza Foldere]
                      /          \
                     v            v
            [9. Muta Fisiere]  [10. Raport CSV]
                                    |
                                    v
                             [11. Salveaza]
```

## Pasii de Setup

### 1. Import Workflow
- Deschide n8n
- Click "Import from file"
- Selecteaza `n8n_clasificare_documente.json`

### 2. Configureaza OpenRouter API Key
- Du-te la Settings > Credentials
- Creeaza un nou "Header Auth" credential:
  - Name: `OpenRouter API Key`
  - Header Name: `Authorization`
  - Header Value: `Bearer sk-or-v1-XXXXXXXXX` (cheia ta OpenRouter)
- In nodul "5a. AI Clasificare", selecteaza credential-ul creat

### 3. Configureaza Input/Output Folders
- In nodul "Manual Trigger", seteaza:
  - `input_folder`: calea catre folderul cu PDF-uri
  - `output_folder`: calea unde vrei folderele clasificate

### 4. Nodul de Citire PDF (de adaptat)
Nodul "1. Citeste Folder" trebuie adaptat la setup-ul tau. Optiuni:
- **Local filesystem**: Foloseste "Read/Write Files from Disk" node
- **Google Drive**: Inlocuieste cu "Google Drive" node
- **Webhook**: Adauga un Webhook trigger in loc de Manual Trigger

### 5. Extractie Text PDF (de adaugat)
Intre nodul 3 si 4a, adauga un nod pentru extractia de text:
- **Optiunea A**: "Extract from File" node (n8n built-in)
- **Optiunea B**: HTTP Request catre un serviciu OCR (Google Vision, Azure, Tesseract API)
- **Optiunea C**: Code node cu librarie pdf-parse:
  ```javascript
  const pdf = require('pdf-parse');
  // ... extract text
  ```

## Categorii Suportate (14)

| Cod                      | Folder Destinatie                                    |
|--------------------------|------------------------------------------------------|
| AGREMENT                 | Agrement/                                            |
| AUTORIZATIE_DISTRIBUTIE  | Autorizatii de comercializare sau de distributie/    |
| AVIZ_TEHNIC_SI_AGREMENT  | Aviz Tehnic + Agrement/                              |
| AVIZ_TEHNIC              | Aviz tehnic/                                         |
| AVIZ_SANITAR             | Avize Sanitare/                                      |
| CE                       | CE/                                                  |
| CERTIFICAT_CALITATE      | Certificat Calitate/                                 |
| CERTIFICAT_GARANTIE      | Certificat Garantie/                                 |
| CUI                      | Cui/                                                 |
| DECLARATIE_CONFORMITATE  | Declaratii conformitate/                             |
| DECLARATIE_PERFORMANTA   | Declaratie de Performanta/                           |
| FISA_TEHNICA             | Fisa Tehnica/                                        |
| ISO                      | Iso/                                                 |
| ALTELE                   | Z.Altele/                                            |

## Modele AI Recomandate (OpenRouter)

| Model | Cost | Viteza | Acuratete | Recomandat pentru |
|-------|------|--------|-----------|-------------------|
| `anthropic/claude-sonnet-4` | $3/M tok | Rapid | Excelenta | Productie |
| `anthropic/claude-haiku-4-5` | $0.25/M tok | Foarte rapid | Buna | Volum mare |
| `openai/gpt-4o-mini` | $0.15/M tok | Foarte rapid | Buna | Buget redus |
| `google/gemini-flash-1.5` | $0.075/M tok | Ultra rapid | Acceptabila | Testing |

## Testare

1. Pune 5-10 PDF-uri din categorii diferite in folderul de input
2. Ruleaza workflow-ul manual
3. Verifica raportul CSV generat
4. Verifica daca fisierele au fost mutate corect

## Costul estimat per document

- Nivel 1 (filename): $0 (gratuit, regex local)
- Nivel 3 (AI): ~$0.001-0.005 per document (depinde de model)
- Pentru 300 documente: ~$0.30-1.50 total cu AI
- ~70-75% se rezolva din filename → costul real e si mai mic

## Nota despre OCR

Pentru PDF-uri scanate, ai nevoie de OCR inainte de AI. Optiuni:
1. **Tesseract local** pe VM-ul tau GCP (gratuit dar necesita setup)
2. **Google Cloud Vision API** ($1.50/1000 pagini)
3. **Azure Computer Vision** (similar pricing)
4. **n8n community node** pentru OCR (cauta "tesseract" in n8n nodes)

Recomandare: Google Cloud Vision API — esti deja pe GCP, integrarea e simpla.
