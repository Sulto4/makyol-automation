---
title: Arhitectura sistemului
scope: architecture
stability: stable
last_verified: 2026-04-19
related:
  - ./api-reference.md
  - ./auth-and-access.md
  - ./extraction-logic.md
  - ./deployment.md
code_refs:
  - docker-compose.yml
  - src/index.ts
  - pipeline/__init__.py
  - pipeline/api.py
  - frontend/nginx/default.conf
---

# Arhitectura sistemului

Makyol Automation e un stack de 4 servicii Docker orchestrat prin `docker-compose.yml`. Documentul descrie shape-ul stabil: servicii, fluxul unei cereri, trust boundaries, modelul de izolare per-utilizator. Pentru detalii per-serviciu vezi `backend.md` / `pipeline.md` / `frontend.md`.

## Servicii

| Nume | Imagine | Port host | Port intern | Rol | Restart policy |
|------|---------|-----------|-------------|-----|----------------|
| `postgres` | `postgres:15-alpine` | 5432 | 5432 | Date persistente + audit log immutable + `settings` key-value | `unless-stopped` |
| `backend` | Custom (`./Dockerfile`, node:18-alpine) | — (doar `expose`) | 3000 | API Express, JWT auth, orchestrare, export Excel | `unless-stopped` |
| `pipeline` | Custom (`./pipeline/Dockerfile`, python:3.11-slim) | 8001 | 8001 | FastAPI worker: clasificare + Vision AI + extracție | `unless-stopped` |
| `frontend` | Custom (`./frontend/Dockerfile`, nginx:alpine + bundle Vite) | `${FRONTEND_PORT:-80}` | 80 | UI React servit de nginx + reverse-proxy `/api` și `/uploads` către backend | `unless-stopped` |

Definit în `docker-compose.yml`. Rețea: bridge default; rezoluție servicii prin DNS intern (`postgres`, `backend`, `pipeline`).

**Volume persistente:**
- `postgres_data` (named volume) — date PostgreSQL
- `./uploads` → `/app/uploads` (backend + pipeline) — PDF-urile încărcate
- `./logs/backend`, `./logs/pipeline` — loguri cu rotație 50MB × 5 fișiere
- `./migrations` → `/docker-entrypoint-initdb.d` (postgres) — aplicare automată la boot

## Request path (producție)

```
Browser
 ├─► TLS termination + DDoS shield @ Cloudflare edge
 │    └─► Tunel cloudflared (outbound din Windows PC)
 │         └─► nginx (container frontend, :80)
 │              ├─► GET /              → static Vite bundle
 │              ├─► /api/*             → http://backend:3000  (proxy, timeout 600s)
 │              ├─► /uploads/*         → http://backend:3000
 │              └─► /health            → http://backend:3000/health
 │
 └─► (dev local fără tunel) → http://localhost:${FRONTEND_PORT:-80}
```

Detalii tunel + auto-start în [deployment.md](./deployment.md).

**De ce timeout 600s pe `/api/*`:** Vision AI poate dura 5-10 minute per document scanat (multi-pagini + OpenRouter). Vezi `frontend/nginx/default.conf`.

## Request path (intern, după intrarea în backend)

```
POST /api/documents (multipart file)
  │
  ├─► src/index.ts:74-86   request logger
  ├─► src/index.ts:106     apiLimiter (2000/min/IP)
  ├─► src/index.ts:124     authGuard (Bearer JWT sau INTERNAL_API_TOKEN)
  ├─► src/routes/documents.ts:28  multer upload (MAX_FILE_SIZE=10MB)
  └─► src/controllers/documentController.ts → uploadDocument
       │
       ├─► Salvează fișier în ./uploads
       ├─► Document.create(...) → INSERT documents (status='pending')
       ├─► pipelineClient.processPdf(path)
       │    └─► POST http://pipeline:8001/api/pipeline/process
       │         └─► pipeline/__init__.py::process_document
       │              ├─► extract_text_from_pdf (pdfplumber → PyMuPDF → Tesseract)
       │              ├─► classify_document (filename → text → AI)
       │              ├─► extract_with_vision (300 DPI → Gemini 2.5 Flash)
       │              ├─► normalize_extraction_result (+ KB fuzzy match)
       │              ├─► validate_extraction (review_status)
       │              └─► returnează {classification, confidence, extraction, ...}
       │
       ├─► ExtractionResult.create(...) + Document.updateStatus('completed')
       ├─► AuditLog.create (immutable)
       └─► 201 Created
```

## Trust boundaries

| Graniță | Mecanism | De unde știi că ai trecut-o |
|---------|----------|------------------------------|
| Internet → Cloudflare | TLS + reguli de acces | Cert valid + header `CF-Connecting-IP` |
| Cloudflare → nginx | Tunel `cloudflared` outbound | IP-ul real din `X-Forwarded-For` |
| nginx → backend | Network bridge intern | `app.set('trust proxy', 1)` în `src/index.ts:67` |
| Extern → rute `/api/*` | JWT (rate-limited 2000/min) | `req.user.id` populat (sau `AUTH_DISABLED=true`) |
| Pipeline → backend | Bearer cu `INTERNAL_API_TOKEN` | `req.user.email === 'internal@pipeline'` (vezi `src/middleware/authMiddleware.ts:52`) |
| Public → `/register` | Flag `REGISTER_ENABLED` | 403 dacă flag-ul e `false` |

> **De ce `INTERNAL_API_TOKEN` și nu un JWT pentru pipeline:** pipeline-ul e un worker pur, fără user. Un JWT ar însemna generarea unui pseudo-user la boot + rotație. Un secret partajat (≥16 chars) între backend și pipeline acoperă nevoia fără state adițional. Vezi [adr/0005-internal-api-token.md](./adr/0005-internal-api-token.md) (Valul 3).

**Pipeline NU autentifică apelurile venite la `:8001`.** Toate apelurile vin de la backend pe rețeaua internă Docker. Dacă ar fi expus extern, ar trebui același `INTERNAL_API_TOKEN`-check.

## Data flow pentru procesare document

```
┌──────────┐  upload  ┌──────────┐  POST /api/pipeline/process  ┌──────────┐
│ Browser  │─────────►│ backend  │─────────────────────────────►│ pipeline │
└──────────┘          └────┬─────┘                              └────┬─────┘
                           │                                          │
                           │  INSERT documents (status='pending')     │
                           ▼                                          │
                      ┌─────────┐                                     │
                      │ postgres│                                     │
                      └────┬────┘                                     │
                           │                                          │
                           │  UPDATE status='processing'              │
                           ▼                                          │
                      ┌─────────┐◄────────────── rezultate ───────────┘
                      │         │
                      │ postgres│  INSERT extraction_results
                      │         │  UPDATE documents status='completed'
                      │         │  INSERT audit_logs
                      └─────────┘
```

## Modelul de izolare per-utilizator (OwnerFilter)

**Enforcat la nivelul modelului, nu al middleware-ului.**

Tabelele `documents` și `extraction_results` au coloana `owner_user_id` (UUID, FK la `users.id`). Toate SELECT/UPDATE/DELETE din `src/models/Document.ts` și `src/models/ExtractionResult.ts` aplică `WHERE owner_user_id = ?` când primesc un owner filter.

**Reguli:**
- Utilizator regulat: vede doar documentele proprii. Controllerul pasează `req.user.id` ca owner filter.
- Admin (`is_admin=true`): vede tot. Controllerul pasează `null` ca owner filter.
- Pipeline (cu `INTERNAL_API_TOKEN`): utilizator sintetic `internal@pipeline` cu `is_admin=true` → acces complet.

> **De ce la nivelul modelului:** dacă cineva adaugă o rută nouă și uită să paseze middleware-ul de filtrare, breach-ul e silent. Forțând ownerul să fie argument al query-ului, un uitat devine eroare de compilare TypeScript. Vezi [adr/0003-...](./adr/) (Valul 3).

Migrațiile relevante: `011_add_owner_to_documents.sql`, `012_add_owner_to_extraction_results.sql`, `014_backfill_existing_documents.sql`.

## Audit log immutable

`AuditLog` (tabel `audit_logs`) are **doar** metoda `create()` în `src/models/AuditLog.ts`. Nu există update/delete prin API sau cod aplicație. Acțiuni logate: `DOCUMENT_UPLOAD`, `DOCUMENT_STATUS_CHANGE`, `DOCUMENT_DELETE`, `DOCUMENT_REVIEW`, `COMPLIANCE_CHECK_EXECUTION`, `REPORT_GENERATION`, `USER_LOGIN`, `CONFIG_CHANGE`.

> **De ce strict immutable:** audit-ul are valoare doar dacă e neintervenit. O metodă de update ar face log-ul modificabil accidental. Eșecurile de write audit sunt **înghițite** (risc: log drop silent dacă DB-ul pică în timpul scrierii) — alternativa, 500-uri pe rutele de business, e mai proastă.

Vezi [adr/0004-audit-logs-immutable.md](./adr/) (Valul 3).

## Settings hot-reload

```
UI Settings (frontend)
  │  PUT /api/settings/:key
  ▼
backend (src/controllers/settingsController.ts)
  ├─► UPSERT settings (key, value)
  └─► fire-and-forget: POST http://pipeline:8001/api/pipeline/reload-settings
                       (timeout 5s, erori înghițite)
                        │
                        ▼
                   pipeline/config.py::reload_settings()
                        │
                        └─► GET http://backend:3000/api/settings
                            (header: Authorization: Bearer INTERNAL_API_TOKEN)
                             │
                             ▼
                        actualizează singleton `settings` in-process
```

> **De ce fire-and-forget:** dacă pipeline-ul e jos temporar, un save de setting din UI n-ar trebui să eșueze. La next request, pipeline-ul reîncarcă oricum la startup. Vezi [configuration.md#hot-reload](./configuration.md#hot-reload).

## Chei settings care se hot-reloadează

Doar aceste chei sunt re-citite de pipeline fără restart:
- `ai_model` (default: `google/gemini-2.5-flash`)
- `ai_temperature` (default: `0.0`)
- `openrouter_api_key` (valoarea DB e autoritativă; `.env` e doar fallback)
- `vision_max_pages` (default: `3`)
- `tesseract_path` (Windows-only; Linux folosește `/usr/bin/tesseract`)

Alte setări backend (`batch_concurrency` clamped `[1..10]`) sunt re-citite la fiecare request din DB — nu necesită reload.

## Stack frontend (Zustand + React Query)

- **Zustand** (`frontend/src/store/*.ts`) — state persistent în `localStorage`:
  - `authStore` (`makyol-auth`): token JWT + user
  - `settingsStore` (`makyol-settings`): overlay local peste DB settings
  - `filterStore` (`makyol-filters`): filtre tabel documente
  - `themeStore` (`makyol-theme`): light/dark/system
- **React Query** — fetch cu auto-polling pentru documente în `processing` (5s) și pagini cu multe detail-fetch-uri (Alerts, Export).

Detalii în [frontend.md](./frontend.md) (Valul 2).

## Verify freshness

```bash
# Flag-ul "Vision unconditional" trebuie să fie True
grep -n '_USE_VISION_FOR_ALL' pipeline/__init__.py
# trebuie L29 = True

# Backend trust proxy e setat
grep -n "trust proxy" src/index.ts
# trebuie L67: app.set('trust proxy', 1)

# Rate limiter apiLimiter are limita 2000
grep -n "limit:" src/middleware/rateLimiter.ts
# trebuie să vezi 2000 la apiLimiter

# INTERNAL_API_TOKEN check cu min 16 chars
grep -n "INTERNAL_API_TOKEN" src/middleware/authMiddleware.ts
# trebuie L52-61 cu .length >= 16

# Cele 4 servicii în compose
grep -E "^  (postgres|backend|pipeline|frontend):" docker-compose.yml
# trebuie 4 match-uri

# Timeout-urile 600s în nginx pentru Vision
grep -n "600" frontend/nginx/default.conf
```
