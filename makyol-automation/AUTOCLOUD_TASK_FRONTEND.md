# AutoCloud Task: Makyol Frontend Dashboard (Vite + React)

## Obiectiv

Construiește un **frontend dashboard** complet folosind **Vite + React + TypeScript** pentru sistemul Makyol de automatizare documente tehnice. Frontend-ul se conectează la backend-ul Express existent pe `http://localhost:3000/api`.

## Context Business

Sistemul procesează dosare PDF (certificate ISO, fișe tehnice, declarații de conformitate, avize sanitare, etc.) pentru materiale de construcții pe autostrada Sibiu-Făgăraș. Un operator încarcă PDF-uri, sistemul le clasifică în 14 categorii și extrage date structurate (material, producător, distribuitor, dată expirare, etc.).

## Tech Stack OBLIGATORIU

- **Vite** — build tool (NU Next.js, NU CRA)
- **React 18+** cu TypeScript
- **React Router v6** — routing client-side (SPA)
- **TanStack Query (React Query)** — data fetching, caching, invalidation
- **Tailwind CSS** — styling (utility-first)
- **Recharts** sau **Chart.js** — grafice dashboard
- **Lucide React** — iconițe
- **react-dropzone** — upload PDF
- **date-fns** — date formatting
- Port frontend: `5173` (default Vite)
- Port backend: `3000`

## API Backend Existent

### Endpoints disponibile:

**POST /api/documents** — Upload PDF (multipart/form-data)
```
Request: FormData cu field "file" (PDF)
Response 201: {
  document: {
    id, filename, original_filename, file_path, file_size, mime_type,
    processing_status: "pending"|"processing"|"completed"|"failed",
    categorie, confidence, metoda_clasificare, review_status,
    error_message, uploaded_at, processing_started_at, processing_completed_at
  },
  extraction: {
    id, document_id, extracted_text,
    material, data_expirare, companie, producator, distribuitor, adresa_producator,
    metadata: { certificate_number, issuing_organization, issue_date, expiry_date, ... },
    confidence_score, extraction_status: "pending"|"success"|"partial"|"failed",
    extraction_model
  }
}
```

**GET /api/documents** — List documents
```
Query params: ?limit=N&offset=N&status=pending|processing|completed|failed
Response 200: { documents: [...], count, limit, offset }
```

**GET /api/documents/:id** — Get document + extraction
```
Response 200: { document: {...}, extraction: {...} }
```

### Câmpuri importante din DB (migration 003):

Pe `documents`:
- `categorie` — una din cele 14 categorii (ISO, CE, FISA_TEHNICA, AGREMENT, AVIZ_TEHNIC, AVIZ_SANITAR, DECLARATIE_CONFORMITATE, DECLARATIE_PERFORMANTA, CERTIFICAT_CALITATE, CERTIFICAT_GARANTIE, AUTORIZATIE_DISTRIBUTIE, CUI, AVIZ_TEHNIC_SI_AGREMENT, ALTELE)
- `confidence` — scor clasificare (0.0-1.0)
- `metoda_clasificare` — rule_based | vision_ai | hybrid | manual
- `review_status` — pending | approved | rejected | needs_review

Pe `extraction_results`:
- `material` — text
- `data_expirare` — date
- `companie` — varchar(255)
- `producator` — varchar(255)
- `distribuitor` — varchar(255)
- `adresa_producator` — text
- `extraction_model` — varchar(100)

## Pagini de Implementat

### 1. Dashboard (`/`)

Pagina principală cu overview:

**Summary Cards** (4 carduri top):
- Total documente procesate
- Documente cu erori/failed
- Documente expirate (data_expirare < today)
- Documente care necesită review (review_status = needs_review)

**Grafice:**
- **Pie chart** — distribuție pe categorii (14 categorii)
- **Bar chart** — documente per status (pending/processing/completed/failed)
- **Bar chart** — documente per metodă clasificare (rule_based/vision_ai/hybrid)

**Activitate recentă:**
- Ultimele 10 documente procesate (tabel mic cu: filename, categorie, status, data)

### 2. Documente (`/documents`)

**Tabel principal** cu TOATE documentele, full-featured:

**Coloane:**
| # | Coloană | Sursă |
|---|---------|-------|
| 1 | Fișier | `document.original_filename` |
| 2 | Categorie | `document.categorie` — afișat ca badge colorat |
| 3 | Material | `extraction.material` |
| 4 | Producător | `extraction.producator` |
| 5 | Companie | `extraction.companie` |
| 6 | Distribuitor | `extraction.distribuitor` |
| 7 | Data expirare | `extraction.data_expirare` — roșu dacă expirat, galben dacă < 30 zile |
| 8 | Confidence | `document.confidence` — progress bar colorat |
| 9 | Status | `document.processing_status` — badge colorat |
| 10 | Review | `document.review_status` — badge |
| 11 | Data upload | `document.uploaded_at` |

**Funcționalități tabel:**
- **Filtrare** pe: categorie (dropdown multi-select), status, review_status
- **Sortare** pe orice coloană (click header)
- **Căutare** text (caută în filename, material, producător, companie)
- **Paginare** (20/50/100 per pagină, using API limit/offset)
- **Color coding** pe categorie (fiecare din 14 categorii = culoare unică)
- **Export** — buton export tabel ca CSV

**Badge-uri categorie** cu culori fixe:
```
ISO = blue, CE = red, FISA_TEHNICA = green, AGREMENT = purple,
AVIZ_TEHNIC = orange, AVIZ_SANITAR = teal, DECLARATIE_CONFORMITATE = pink,
DECLARATIE_PERFORMANTA = indigo, CERTIFICAT_CALITATE = amber,
CERTIFICAT_GARANTIE = cyan, AUTORIZATIE_DISTRIBUTIE = lime,
CUI = gray, AVIZ_TEHNIC_SI_AGREMENT = violet, ALTELE = slate
```

### 3. Document Detail (`/documents/:id`)

**Layout split:**
- **Stânga (60%)**: PDF viewer (embed `<iframe>` sau `<object>` cu file_path)
- **Dreapta (40%)**: Date extrase

**Date extrase (card-uri):**
- Nume document
- Categorie (badge)
- Material
- Producător + Adresă
- Distribuitor
- Companie
- Data expirare (cu warning vizual dacă expirat)
- Confidence score (progress bar)
- Metoda clasificare
- Status procesare
- Status review + butoane: Approve / Reject / Needs Review

**Metadata AI** (expandable section):
- Raw metadata JSON pretty-printed
- Extracted text (collapsible, primele 500 chars by default)

### 4. Upload (`/upload`)

**Dropzone** (react-dropzone):
- Drag & drop area mare
- Accept doar `.pdf`
- Upload multiplu (queue)
- Progress bar per fișier
- După upload: redirect la `/documents` sau arată status inline
- Afișare erori per fișier

**Upload flow:**
1. User drop-ează PDF-uri
2. Frontend trimite POST /api/documents pentru fiecare
3. Afișează progress + rezultat (categorie detectată, confidence)
4. Buton "Vezi toate documentele"

### 5. Alerte (`/alerts`)

Pagină cu documente problematice:

**Tabs:**
- **Expirate** — data_expirare < today (sortate: cele mai recent expirate primele)
- **Expiră curând** — data_expirare între today și today+30 zile
- **Failed** — processing_status = failed
- **Low confidence** — confidence < 0.7
- **Needs review** — review_status = needs_review

Fiecare tab = tabel filtrat cu aceleași coloane ca pagina Documents.

## Structura Proiect

```
frontend/
├── index.html
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── tsconfig.json
├── package.json
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── api/
│   │   └── client.ts          # Axios/fetch wrapper, base URL config
│   │   └── documents.ts       # API calls: uploadDocument, listDocuments, getDocument
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx     # Navigare: Dashboard, Documents, Upload, Alerts
│   │   │   ├── Header.tsx
│   │   │   └── Layout.tsx
│   │   ├── documents/
│   │   │   ├── DocumentsTable.tsx
│   │   │   ├── DocumentRow.tsx
│   │   │   ├── DocumentFilters.tsx
│   │   │   ├── DocumentDetail.tsx
│   │   │   ├── CategoryBadge.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── ConfidenceBar.tsx
│   │   ├── upload/
│   │   │   ├── UploadDropzone.tsx
│   │   │   └── UploadProgress.tsx
│   │   ├── dashboard/
│   │   │   ├── SummaryCards.tsx
│   │   │   ├── CategoryChart.tsx
│   │   │   └── RecentActivity.tsx
│   │   └── shared/
│   │       ├── Pagination.tsx
│   │       ├── SearchBar.tsx
│   │       ├── ExpirationWarning.tsx
│   │       └── LoadingSpinner.tsx
│   ├── hooks/
│   │   ├── useDocuments.ts     # TanStack Query hooks
│   │   └── useUpload.ts
│   ├── pages/
│   │   ├── DashboardPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── DocumentDetailPage.tsx
│   │   ├── UploadPage.tsx
│   │   └── AlertsPage.tsx
│   ├── types/
│   │   └── index.ts            # Document, ExtractionResult, Category types
│   ├── utils/
│   │   ├── categories.ts       # Category labels, colors, icons
│   │   ├── dates.ts            # Date formatting, expiration checks
│   │   └── csv.ts              # CSV export utility
│   └── styles/
│       └── globals.css         # Tailwind imports
```

## Configurare Vite

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
      }
    }
  }
})
```

## TypeScript Types

```typescript
// src/types/index.ts

export type Category =
  | 'ISO' | 'CE' | 'FISA_TEHNICA' | 'AGREMENT'
  | 'AVIZ_TEHNIC' | 'AVIZ_SANITAR' | 'DECLARATIE_CONFORMITATE'
  | 'DECLARATIE_PERFORMANTA' | 'CERTIFICAT_CALITATE'
  | 'CERTIFICAT_GARANTIE' | 'AUTORIZATIE_DISTRIBUTIE'
  | 'CUI' | 'AVIZ_TEHNIC_SI_AGREMENT' | 'ALTELE';

export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';
export type ExtractionStatus = 'pending' | 'success' | 'partial' | 'failed';
export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'needs_review';
export type ClassificationMethod = 'rule_based' | 'vision_ai' | 'hybrid' | 'manual';

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  processing_status: ProcessingStatus;
  categorie: Category | null;
  confidence: number | null;
  metoda_clasificare: ClassificationMethod | null;
  review_status: ReviewStatus;
  error_message: string | null;
  uploaded_at: string;
  processing_started_at: string | null;
  processing_completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExtractionResult {
  id: number;
  document_id: number;
  extracted_text: string | null;
  material: string | null;
  data_expirare: string | null; // ISO date or duration string
  companie: string | null;
  producator: string | null;
  distribuitor: string | null;
  adresa_producator: string | null;
  metadata: Record<string, any>;
  confidence_score: number | null;
  extraction_status: ExtractionStatus;
  extraction_model: string | null;
  error_details: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentWithExtraction {
  document: Document;
  extraction: ExtractionResult | null;
}

export interface DocumentListResponse {
  documents: Document[];
  count: number;
  limit: number | null;
  offset: number;
}
```

## Design & UX

- **Layout:** Sidebar fixă stânga (200px) + content area
- **Culori:** Professional, light theme, accent blue (#3B82F6)
- **Font:** System font stack (Inter dacă disponibil)
- **Responsive:** Desktop-first (tool intern), dar tabelul să fie scrollable pe ecrane mici
- **Loading states:** Skeleton loaders pe tabele, spinner pe upload
- **Empty states:** Ilustrații/mesaje pentru "No documents yet", "No alerts"
- **Toasts:** Notificări pentru upload success/error (react-hot-toast sau similar)
- **Limba interfață:** Română (labels, butoane, mesaje)

## Reguli CRITICE

1. **NU instala Next.js** — folosește DOAR Vite + React
2. **NU face SSR** — este o aplicație SPA pură
3. **Proxy API** prin vite.config.ts — NU hardcoda `http://localhost:3000` în componente
4. **TanStack Query** pentru TOATE fetch-urile — NU useEffect + fetch manual
5. **TypeScript strict** — no `any` types, definește toate interfețele
6. **Toate textele UI în română** — "Documente", "Încarcă", "Alerte", "Categorie", etc.
7. **Testează** cu `npm run build` — zero erori TypeScript
8. **CORS:** Backend-ul are CORS configurat pe `CORS_ORIGIN` env var — setează la `http://localhost:5173`

## Livrabile

1. Folder `frontend/` complet funcțional în root-ul repo-ului
2. `npm run dev` pornește aplicația fără erori
3. `npm run build` compilează fără erori
4. Dashboard-ul afișează date reale din API
5. Upload-ul funcționează end-to-end
6. Tabelul cu documente are filtrare, sortare, paginare
7. README.md cu instrucțiuni setup (2-3 comenzi)
