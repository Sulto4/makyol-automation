---
title: Development (dev loop local + how-to)
scope: development
stability: living
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./backend.md
  - ./pipeline.md
  - ./frontend.md
  - ./database.md
  - ./runbook.md
code_refs:
  - package.json
  - docker-compose.yml
  - jest.config.js
  - migrations
---

# Development

Cum rulezi sistemul local, cum adaugi lucruri, cum testezi. Pentru proceduri ops (seed admin, rotate key) vezi [runbook.md](./runbook.md).

## Prerechizite

- **Docker Desktop** (Windows) sau Docker + docker-compose (Linux/Mac) — ≥ 20.10
- **Git** + `git config core.longpaths true` pe Windows (PDF-urile din `Pachete Makyol/` au filenames lungi)
- Editor (VS Code recomandat, cu extensii ESLint + Prettier + Tailwind)
- (Opțional) `node >= 18` + `python >= 3.11` dacă vrei să rulezi fără Docker

## Quickstart

```bash
git clone <repo-url>
cd makyol-automation

# Config
cp .env.example .env
# Editează .env — minim JWT_SECRET + OPENROUTER_API_KEY + INTERNAL_API_TOKEN
openssl rand -hex 32   # pentru fiecare dintre cele 3 secrete

# Pornire stack complet
docker compose up -d --build

# Verifică
docker compose ps
curl -s http://localhost/health
curl -s http://localhost:8001/api/pipeline/health
```

La primul boot, migrațiile rulează automat (volumul `postgres_data` e nou). Pentru seed primul admin: vezi [runbook.md#seed-admin](./runbook.md#seed-admin).

## Dev loop per serviciu

### Backend (TypeScript)

**Hot-reload cu Docker:** `src/` e bind-mounted (nu e — vezi compose) sau cu ts-node local:

```bash
# Opțiune A: Docker cu rebuild la modificare (lent)
docker compose up -d --build backend

# Opțiune B: local, fără Docker pentru backend
# În .env setează DB_HOST=localhost, PIPELINE_URL=http://localhost:8001
npm install
npm run dev
# ts-node + nodemon — hot-reload pe save
```

Log-uri: `docker compose logs -f backend` sau stdout-ul direct din `npm run dev`.

### Pipeline (Python)

```bash
# Local (recomandat pentru iterație rapidă)
pip install -r requirements.txt
# Set BACKEND_API_URL + INTERNAL_API_TOKEN în env
uvicorn pipeline.api:app --reload --port 8001

# Sau Docker
docker compose up -d --build pipeline
docker compose logs -f pipeline
```

### Frontend (Vite)

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173 (proxy /api → http://127.0.0.1:3000)
```

În dev, backend trebuie să ruleze pe `localhost:3000` (Docker sau local).

## Testing

### Backend (Jest)

```bash
npm test                       # tot
npm run test:watch             # watch mode
npm run test:integration       # integration/*
npm run test:e2e               # e2e/*
npm run test:coverage          # HTML + LCOV
```

Config: `jest.config.js`. Root-uri: `src/` + `tests/`. Pattern: `**/?(*.)+(spec|test).ts`.

### Pipeline (pytest)

```bash
cd pipeline  # sau root, dacă path e configurat
python -m pytest tests/ -v
```

### Frontend

Momentan nu există teste frontend dedicate. Verificarea se face prin UI la build:

```bash
cd frontend && npm run build
# Verifică că `dist/` se construiește fără erori TypeScript
```

## Lint + format

```bash
npm run lint              # ESLint pe src/**/*.ts
npm run lint:fix          # auto-fix
npm run format            # Prettier
npm run format:check
```

Frontend: `cd frontend && npm run lint`.

## How-to: adaugi o rută nouă în backend

Presupunem: `POST /api/documents/:id/export-pdf` care returnează un PDF compilat.

1. **Controller method** — `src/controllers/documentController.ts`:
   ```typescript
   async exportDocumentPdf(req: Request, res: Response, next: NextFunction) {
     try {
       const id = parseInt(req.params.id);
       const owner = ownerOf(req);
       const doc = await this.documentModel.findById(id, owner);
       if (!doc) return res.status(404).json(...);
       // ... build PDF ...
       res.setHeader('Content-Type', 'application/pdf');
       res.send(buffer);
     } catch (err) { next(err); }
   }
   ```

2. **Route** — `src/routes/documents.ts`:
   ```typescript
   router.get('/:id/export-pdf', (req, res, next) =>
     controller.exportDocumentPdf(req, res, next));
   ```

3. **Audit log** (dacă acțiunea e relevantă pentru trail):
   ```typescript
   await auditService.logDocumentAction(ActionType.REPORT_GENERATION, ...);
   ```

4. **Doc update:**
   - Adaugă rândul în tabelul din [api-reference.md](./api-reference.md#backend---documents-apidocuments)
   - `last_verified: <data curentă>` în frontmatter-ul `api-reference.md`

5. **Frontend** (dacă e apelată din UI):
   - `frontend/src/api/documents.ts` — adaugă funcția de apel
   - Invalidation React Query dacă modifică state

6. **Test:**
   - `tests/e2e/documents/exportPdf.test.ts` — scenariu happy path + 404

## How-to: adaugi o migrație

Presupunem: adăugat o coloană `tags VARCHAR[]` la `documents`.

1. **Creează fișier** — `migrations/016_add_tags_to_documents.sql`:
   ```sql
   -- Migration: 016_add_tags_to_documents
   -- Description: Add tags array to documents for user-facing labels
   -- Date: 2026-04-19

   ALTER TABLE documents ADD COLUMN IF NOT EXISTS tags VARCHAR[];
   CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING GIN (tags);
   COMMENT ON COLUMN documents.tags IS 'User-facing labels / categories';
   ```

2. **Prefix:** continuă numerotarea (ultimul a fost 015). **NU refolosi 016 dacă altcineva a făcut-o între timp** — verifică `ls migrations/`.

3. **Idempotență:** folosește `IF NOT EXISTS` / `IF EXISTS` și tratează "already exists" — migrațiile rulează la fiecare startup, trebuie să fie safe.

4. **Model update** — `src/models/Document.ts`:
   - Adaugă `tags?: string[]` la interfață
   - Actualizează `create()` și `findById()` dacă relevant

5. **Doc update:**
   - [database.md#documents](./database.md#documents-migration-001--cols-adăugate-ulterior) — rândul nou în tabel
   - [database.md#migration-ledger](./database.md#migration-ledger) — rândul 016 nou
   - `last_verified` actualizat

6. **Test migrație:**
   ```bash
   # Drop + recreate DB local ca să verifici că migrațiile sunt idempotente în ordine
   docker compose down -v   # DESTRUCTIV — doar în dev
   docker compose up -d --build
   ```

## How-to: adaugi o categorie nouă de document

Presupunem: `BULETIN_INCERCARI` (buletin de încercări).

1. **Update cod pipeline:**
   - `pipeline/classification.py` L30 (`VALID_CATEGORIES`) — adaugă la listă
   - `pipeline/classification.py` — adaugă:
     - Regex filename în `classify_by_filename` (ex: `\bbuletin.*incerc` match → `("BULETIN_INCERCARI", 0.92, "filename_regex")`)
     - Text rule în `classify_by_text` (ex: `"buletin de incercari"` în primii 500 chars)
   - `pipeline/extraction.py:34` (`EXTRACTION_SCHEMA`) — adaugă intrarea:
     ```python
     "BULETIN_INCERCARI": {
       "fields": ["material", "producator", "data_incercari", ...],
       "instructions": "Extract: material tested, manufacturer, test date, ..."
     }
     ```
   - Decide dacă are `data_expirare` → actualizează `CATEGORIES_WITH_DATA_EXPIRARE` (`extraction.py:202`)

2. **Update DB constraints** (dacă e necesar) — NU există CHECK constraint pentru `categorie` pe documents tabel, deci nu e nevoie de migrație.

3. **Test:**
   - Rulează pipeline local pe un PDF mostră
   - Verifică că clasificarea alege noua categorie

4. **Doc update:**
   - [extraction-logic.md#cele-14-categorii](./extraction-logic.md#cele-14-categorii) — devine 15 categorii
   - [pipeline.md#classification-cascade](./pipeline.md#classification-cascade) dacă e cascade nou
   - `last_verified` actualizat

5. **UI update** (dacă categoria apare în filtere):
   - `frontend/src/types/` — adaugă la `DocumentCategory` enum

## How-to: schimbi modelul AI default

Vezi [runbook.md#schimbă-modelul-ai-folosit](./runbook.md). TL;DR: UI Settings → model → Save. Pipeline reîncarcă automat.

Dacă vrei să adaugi un model nou în lista `VALIDATION_RULES.ai_model.options`:
- `src/services/settingsService.ts:40-50` — adaugă în array
- Asigură-te că e Vision-capable (altfel extraction falls back la regex)

## Common gotchas

- **Migrații care se aplică de mai multe ori.** Usage `IF NOT EXISTS` peste tot; altfel al doilea startup pică.
- **Schimbare enum CHECK.** Postgres nu permite `ALTER CHECK` in-place. Patern: `ALTER TABLE ... DROP CONSTRAINT ...; ALTER TABLE ... ADD CONSTRAINT ... CHECK (...);` — vezi migration `006_update_metoda_clasificare_constraint.sql` ca exemplu.
- **Pipeline cache la import.** Modulele Python citesc settings la `import time`. Dacă adaugi un setting nou pe hot-reload, verifică că e citit din `settings.<attr>` runtime, nu din `AI_MODEL` capturat la import. Vezi `pipeline/config.py:178-190`.
- **Docker build cache.** La schimbări de `package.json`, adesea ai nevoie de `docker compose build --no-cache backend` să pună dependențele noi.
- **Windows long paths.** Dacă `git worktree add` pică pe Windows cu "path too long", asigură-te că ai `git config core.longpaths true` (global și local).

## Structură fișiere noi

| Tip | Unde |
|-----|------|
| Rută backend nouă | `src/routes/*.ts` + `src/controllers/*.ts` |
| Modul pipeline nou | `pipeline/*.py` (evită să injectezi în `__init__.py`) |
| Pagină frontend nouă | `frontend/src/pages/*.tsx` + rută în `App.tsx` |
| Componentă frontend reutilizabilă | `frontend/src/components/<domeniu>/` |
| Migrație SQL | `migrations/NNN_descriptive_name.sql` |
| Test unit | Lângă sursă sau în `tests/<categorie>/` |
| Doc nou | `docs/` conform regulilor din [CONTRIBUTING-DOCS.md](./CONTRIBUTING-DOCS.md) |

## Verify freshness

```bash
# npm scripts există
grep -E '"(dev|build|test|lint):?[^"]*":' package.json | wc -l
# ≥ 8 scripts

# Migrațiile urmează convenția NNN_descriptive
ls migrations/*.sql | head -20

# Pipeline are requirements.txt
test -f requirements.txt || test -f pipeline/requirements.txt && echo OK

# Frontend are propriul package.json
test -f frontend/package.json && echo OK

# jest config există
test -f jest.config.js && echo OK
```
