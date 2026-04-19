---
title: Backend (Node/Express/TypeScript)
scope: backend
stability: living
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./api-reference.md
  - ./database.md
  - ./auth-and-access.md
  - ./configuration.md
code_refs:
  - src/index.ts
  - src/controllers
  - src/services
  - src/models
  - src/middleware
  - Dockerfile
---

# Backend

Serviciul Node/TypeScript/Express care expune API-ul HTTP (`:3000`, prefix `/api`), autentifică utilizatorii, persistă date în Postgres și orchestrează pipeline-ul Python. Acest doc descrie shape-ul codului (ce fișier face ce). Pentru comportament cross-service vezi [architecture.md](./architecture.md). Pentru rute vezi [api-reference.md](./api-reference.md).

## Rol

- Terminator JWT + OwnerFilter per utilizator
- Orchestrează upload → pipeline → persistență
- Audit logging immutable
- Export Excel + ZIP arhive
- Interfață CRUD pentru `settings` + admin users

Nu face: OCR, Vision AI, clasificare — acelea sunt în `pipeline/`.

## Entry point & bootstrap

| Pas | Locație | Ce face |
|-----|---------|---------|
| Creează pool Postgres | `src/index.ts:143-155` (`createDatabasePool`) | Config din `src/config/database.ts` + handlers pentru pool events |
| Creează Express app | `src/index.ts:61-138` (`createApp`) | Atașează middleware + routes |
| Test conexiune DB | `src/index.ts:169-176` | `pool.connect()` early-fail la erori |
| Rulează migrații | `src/index.ts:22-54` (`runMigrations`) | Sort alfabetic în `migrations/`, idempotent (înghite "already exists") |
| Listen | `src/index.ts:182` | Default `appConfig.port = 3000` |
| Graceful shutdown | `src/index.ts:191-205` | `SIGTERM`/`SIGINT` → `pool.end()` + `process.exit(0)` |

## Directory layout

| Folder | Rol | Fișiere |
|--------|-----|---------|
| `src/config/` | Config app + DB + locale | `app.ts`, `database.ts`, `romanian-locale.ts` |
| `src/controllers/` | Request handlers HTTP | `authController.ts`, `documentController.ts`, `settingsController.ts`, `auditLogController.ts` |
| `src/routes/` | Router factory functions | `auth.ts`, `adminUsers.ts`, `documents.ts`, `settings.ts`, `auditLogs.ts` |
| `src/services/` | Business logic | `authService.ts`, `pipelineClient.ts`, `settingsService.ts`, `auditService.ts`, `archiveService.ts`, `dateParser.ts`, `metadataParser.ts`, `pdfExtractor.ts` |
| `src/models/` | DB models (query layer) | `User.ts`, `Document.ts`, `ExtractionResult.ts`, `AuditLog.ts`, `settings.ts` |
| `src/middleware/` | Express middleware | `authMiddleware.ts`, `rateLimiter.ts`, `errorHandler.ts`, `auditMiddleware.ts`, `upload.ts` |
| `src/utils/` | Helpers | `logger.ts` (Winston), `errors.ts`, `patterns.ts`, `concurrency.ts` |
| `src/types/` | TS type stubs | `pdf-parse.d.ts` etc. |

> **Atenție — fișiere legacy:** `src/` conține și fișiere Python MVP care **NU** sunt folosite de backend-ul curent: `config.py`, `document_classifier.py`, `main.py`, `metadata_extractor.py`, `models.py`, `pdf_extractor.py`, `word_generator.py`, `__init__.py`, plus folderele `routers/`, `schemas/`, `templates/`. Sunt reminiscențe din versiunea Python monolitică pre-split. La un refactor viitor pot fi mutate în `archive/`.

## Middleware stack

Ordinea contează — `src/index.ts:61-138`:

```
1. express.json() + express.urlencoded()                   [body parsing]
2. request logger                                           [src/index.ts:74-86]
3. /uploads static                                          [src/index.ts:89]
4. GET /health                                              [src/index.ts:92-98]  (NU e rate-limited)
5. authLimiter pe /api/auth/login, /api/auth/register      [5/min/IP]
6. apiLimiter pe /api                                       [2000/min/IP]
7. /api/auth                                                [createAuthRoutes, public + /me protejat intern]
8. authGuard pentru rutele protejate (sau no-op dacă AUTH_DISABLED)
9. /api/documents, /api/audit-logs, /api/settings           [cu authGuard]
10. /api/auth/admin/users                                    [requireAuth + requireAdmin intern]
11. notFoundHandler                                          [404]
12. errorHandler                                             [500 + logging]
```

**Proxy trust:** `app.set('trust proxy', 1)` la `src/index.ts:67` — deduce IP-ul real din `X-Forwarded-For` (nginx + Cloudflare). Vezi [auth-and-access.md](./auth-and-access.md#rate-limiting).

## Controllers

| Fișier | Responsabilitate | Dependențe principale |
|--------|------------------|----------------------|
| `authController.ts` | register, login, me, admin create/list/activate/reset-password | `AuthService` |
| `documentController.ts` | upload (single + folder), list, stats, get, reprocess, review, reprocess-all, export-archive, clear-all | `DocumentModel`, `ExtractionResultModel`, `pipelineClient`, `auditService`, `archiveService`, `settings.batch_concurrency` |
| `settingsController.ts` | initialize, getAll, getOne, upsert, delete + fire-and-forget `notifyPipelineReload` | `SettingsService` |
| `auditLogController.ts` | list cu filtre (date, user, action_type, entity_type, entity_id), export CSV/JSON | `AuditLogModel` |

Fiecare controller e instanțiat în router factory cu `pool` injectat.

## Services

| Fișier | Rol | Note |
|--------|-----|------|
| `authService.ts` | Bcrypt + JWT sign/verify, admin user management | JWT_SECRET min 16 chars, expires default 7d; first user auto-admin |
| `pipelineClient.ts` | HTTP client către pipeline | Timeout-uri: 300s normal, 600s pentru file >1MB (scan cu Vision), 5s health check; erori custom: `PipelineConnectionError`, `PipelineTimeoutError`, `PipelineProcessingError` |
| `settingsService.ts` | Validare + upsert + audit log + `DEFAULT_SETTINGS` + `VALIDATION_RULES` | Model options pentru `ai_model` listate în cod (9 modele Vision-capable) |
| `auditService.ts` | Wrapper peste `AuditLogModel.create` cu helpers per action type | Eșec audit = log warn, NU aruncă (audit drop silent — compromis acceptat pentru a nu bloca rutele business) |
| `archiveService.ts` | Construiește ZIP + Excel pentru export | Excel: hyperlinks + color-coding pe expiry; folosește `exceljs` |
| `dateParser.ts`, `metadataParser.ts`, `pdfExtractor.ts` | Legacy MVP | Încă rulat de unele teste; în afara hot path-ului curent |

## Models (query layer)

Toate primesc `pool: Pool` în constructor. Filtrare `OwnerFilter: string | null`:

| Fișier | Tabel | OwnerFilter | Metode cheie |
|--------|-------|-------------|--------------|
| `User.ts` | `users` | n/a | `create`, `findByEmail`, `findById`, `countAll`, `touchLastLogin`, `listAll`, `setActive`, `updatePassword` |
| `Document.ts` | `documents` | da | `create`, `findById(id, owner)`, `findAll(limit, offset, status, owner)`, `updateStatus`, `updateClassification`, `delete`, `deleteAll` |
| `ExtractionResult.ts` | `extraction_results` | da | `create`, `update` (pe câmpuri, nu pe rând), `findByDocumentId` |
| `AuditLog.ts` | `audit_logs` | n/a | DOAR `create` (immutable — vezi [architecture.md#audit-log-immutable](./architecture.md#audit-log-immutable)) |
| `settings.ts` | `settings` | n/a | `upsert`, `findByKey`, `findAll`, `update`, `delete`, `getValue<T>` |

**OwnerFilter semantică:** string UUID → `WHERE owner_user_id = $N` adăugat la query; `null` → fără filtrare (admin/intern).

## Middleware detail

| Fișier | Rol |
|--------|-----|
| `authMiddleware.ts` | `createAuthMiddleware(authService)` — Bearer JWT OR `INTERNAL_API_TOKEN`; `requireAdmin` — check `req.user.is_admin` (post-auth) |
| `rateLimiter.ts` | `authLimiter` (5/min login+register) și `apiLimiter` (2000/min /api) |
| `errorHandler.ts` | `errorHandler` (ultimul în stack, log + răspuns structurat) și `notFoundHandler` |
| `auditMiddleware.ts` | Helpers pentru audit log atașat la request (folosit de unele rute) |
| `upload.ts` | Multer: `upload.single('file')` (10MB) + `folderUpload` (50MB/fișier) |

## Build & run

### Scripts npm (`package.json`)

| Script | Cod | Scop |
|--------|-----|------|
| `dev` | `nodemon --exec ts-node src/index.ts` | Dev server cu hot-reload |
| `build` | `tsc` | Compilează `src/` → `dist/` (ES2022, CommonJS, strict) |
| `start` | `node dist/index.js` | Production entry point |
| `migrate` | `ts-node scripts/migrate.ts` | Manual migration (backup — startup-ul rulează oricum) |
| `test`, `test:watch`, `test:integration`, `test:e2e`, `test:coverage` | Jest | Vezi `jest.config.js` |
| `lint`, `lint:fix`, `format`, `format:check` | ESLint + Prettier | Code quality |

### Dockerfile (root `./Dockerfile`)

Multi-stage:
1. **Builder** — `node:18-alpine`, copiază `package*.json` + `tsconfig.json` + `src/`, rulează `npm install` + `npm run build`
2. **Production** — `node:18-alpine` + `dumb-init` (signal handling), user non-root `nodejs:1001`, copiază `dist/` + prod deps + `migrations/`, `EXPOSE 3000`, healthcheck `GET /health`

`CMD ["npm", "start"]` în `docker-compose.yml:62`.

## TypeScript config

`tsconfig.json`: target ES2022, module CommonJS, strict, sourcemap + declarations, `rootDir: src/`, `outDir: dist/`, exclude `node_modules/dist/tests`.

## Legacy MVP artifacts în src/

Fișierele Python din `src/` (`config.py`, `main.py`, etc.) nu sunt importate de codul TS. Folderele `src/routers/`, `src/schemas/`, `src/templates/` sunt de asemenea legacy. La un refactor viitor pot fi mutate în `archive/`. Momentan nu fac rău — nu sunt în tsconfig, Dockerfile-ul copiază doar TS.

## Verify freshness

```bash
# Entry point bootstrap există la liniile indicate
grep -n "function runMigrations\|function createApp\|function startServer" src/index.ts
# trebuie 3 match-uri la L22, L61, L160

# Toate cele 5 routers
ls src/routes/*.ts | wc -l    # 5

# Toate cele 4 controllers
ls src/controllers/*.ts | wc -l    # 4

# 5 modele TS (Python .pyc sunt în __pycache__, ignorate)
ls src/models/*.ts | wc -l    # 5

# 5 middleware-uri
ls src/middleware/*.ts | wc -l    # 5

# authMiddleware înghite JWT sau INTERNAL_API_TOKEN
grep -n "INTERNAL_API_TOKEN" src/middleware/authMiddleware.ts
# trebuie L52-61

# pipelineClient cu timeout-uri configurabile
grep -n "300000\|600000" src/services/pipelineClient.ts
```
