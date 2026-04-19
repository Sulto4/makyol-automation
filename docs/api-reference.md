---
title: API Reference (backend + pipeline)
scope: api-reference
stability: living
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./auth-and-access.md
  - ./configuration.md
code_refs:
  - src/routes/auth.ts
  - src/routes/documents.ts
  - src/routes/auditLogs.ts
  - src/routes/settings.ts
  - src/routes/adminUsers.ts
  - pipeline/api.py
---

# API Reference

Toate rutele HTTP expuse de backend (`:3000`, prefix `/api`) și pipeline (`:8001`). În producție frontendul accesează backend-ul same-origin prin nginx (`/api/*` → `http://backend:3000`). Pipeline-ul NU e expus extern — doar backend-ul îl apelează pe rețeaua Docker.

## Coloane

- **Auth:** `public` (fără), `JWT` (Bearer user), `Admin` (JWT + `is_admin`), `Internal` (JWT user sau `INTERNAL_API_TOKEN`).
- **Handler:** `path:line` fișier controller.
- **Scope:** `owner` = filtrat pe `owner_user_id`; admin vede tot.

**Nota asupra `AUTH_DISABLED`:** dacă `AUTH_DISABLED=true` în env, toate rutele marcate `JWT`/`Admin` sunt tratate ca și cum caller-ul e admin (pentru dev local). **Nu** folosi în prod.

---

## Backend — Health

| Method | Path | Auth | Handler | Note |
|--------|------|------|---------|------|
| GET | `/health` | public | `src/index.ts:92` | `{status, timestamp, environment}`; NU e rate-limited |

---

## Backend — Auth (public + /me)

Rate-limited `5/min/IP` pe `/login` și `/register` (vezi `src/middleware/rateLimiter.ts:8`).

| Method | Path | Auth | Handler | Note |
|--------|------|------|---------|------|
| POST | `/api/auth/register` | public | `src/controllers/authController.ts → register` | Blocat cu 403 dacă `REGISTER_ENABLED=false`. Primul user înregistrat devine automat admin |
| POST | `/api/auth/login` | public | `src/controllers/authController.ts → login` | `{email, password}` → `{user, token}` |
| GET | `/api/auth/me` | JWT | `src/controllers/authController.ts → me` | Profil user curent |

---

## Backend — Admin users (/api/auth/admin/users)

Router-ul atașează intern `requireAuth + requireAdmin` (`src/routes/adminUsers.ts:13`).

| Method | Path | Auth | Handler | Note |
|--------|------|------|---------|------|
| GET | `/api/auth/admin/users` | Admin | `authController.ts → adminListUsers` | Listează toți utilizatorii |
| POST | `/api/auth/admin/users` | Admin | `authController.ts → adminCreateUser` | `{email, password, isAdmin?}`; parola returnată în toast UI |
| PATCH | `/api/auth/admin/users/:id/active` | Admin | `authController.ts → adminSetUserActive` | Activare/dezactivare user; împiedică self-deactivation |
| PATCH | `/api/auth/admin/users/:id/password` | Admin | `authController.ts → adminResetPassword` | Reset parolă fără email (one-shot) |

---

## Backend — Documents (/api/documents)

Toate necesită `JWT`; filtrare `owner` pentru utilizator non-admin; fișierele upload trec prin multer (`MAX_FILE_SIZE=10MB` single / `50MB` per-file pentru folder-upload).

| Method | Path | Auth | Scope | Handler | Note |
|--------|------|------|-------|---------|------|
| POST | `/api/documents` | JWT | owner | `documentController.ts → uploadDocument` | multipart `file` sau `{file_path}`; procesează sincron via pipeline; 201 la succes, 422 la pipeline fail |
| GET | `/api/documents` | JWT | owner | `documentController.ts → listDocuments` | `?limit&offset&status`; status ∈ `pending/processing/completed/failed` |
| GET | `/api/documents/stats` | JWT | owner | `documentController.ts → getStats` | Counts pe status, success rate, usage per-model |
| GET | `/api/documents/:id` | JWT | owner | `documentController.ts → getDocumentById` | Document + extraction result |
| POST | `/api/documents/:id/reprocess` | JWT | owner | `documentController.ts → reprocessDocument` | Re-rulează pipeline pe un doc existent |
| PATCH | `/api/documents/:id/review` | JWT | owner | `documentController.ts → reviewDocument` | `{action: 'approve'/'reject', rejection_reason, corrected_category, wrong_fields, comment}` |
| POST | `/api/documents/reprocess-all` | JWT | owner | `documentController.ts → reprocessAll` | Batch reprocess; concurență din `batch_concurrency` (`[1..10]`) |
| DELETE | `/api/documents` | Admin (în fapt, intern) | all | `documentController.ts → clearAllDocuments` | Șterge tot (purge) |
| POST | `/api/documents/upload-folder` | JWT | owner | `documentController.ts → uploadFolder` (via `folderUpload` multer middleware) | Multi-file, 50MB/fișier; păstrează structura folder prin `relative_path` |
| POST | `/api/documents/export-archive` | JWT | owner | `documentController.ts → exportArchive` | Streaming ZIP + Excel (hyperlinks, color-coding pe expirare) |

---

## Backend — Audit Logs (/api/audit-logs)

Read-only. Audit logs sunt **immutable** — fără update/delete route-s. Vezi [architecture.md#audit-log-immutable](./architecture.md#audit-log-immutable).

| Method | Path | Auth | Handler | Note |
|--------|------|------|---------|------|
| GET | `/api/audit-logs/export` | JWT | `auditLogController.ts → exportAuditLogs` | `?format=csv/json` + filtre `user_id`, `action_type`, `entity_type`, `entity_id`, `start_date`, `end_date` |
| GET | `/api/audit-logs` | JWT | `auditLogController.ts → listAuditLogs` | Aceleași filtre; `limit` default 50 max 1000, `offset` default 0 |
| GET | `/api/audit-logs/:id` | JWT | `auditLogController.ts → getAuditLogById` | Un singur log |

**Action types logate** (`src/models/AuditLog.ts`): `DOCUMENT_UPLOAD`, `DOCUMENT_STATUS_CHANGE`, `DOCUMENT_DELETE`, `DOCUMENT_REVIEW`, `COMPLIANCE_CHECK_EXECUTION`, `REPORT_GENERATION`, `USER_LOGIN`, `CONFIG_CHANGE`.

---

## Backend — Settings (/api/settings)

Fiecare mutare (PUT/DELETE) declanșează fire-and-forget `POST http://pipeline:8001/api/pipeline/reload-settings` cu timeout 5s. Vezi [configuration.md#hot-reload](./configuration.md#hot-reload).

| Method | Path | Auth | Handler | Note |
|--------|------|------|---------|------|
| POST | `/api/settings/initialize` | JWT | `settingsController.ts → initializeDefaults` | Populează default-urile lipsă din DB |
| GET | `/api/settings` | Internal | `settingsController.ts → getAllSettings` | Merge DB + `DEFAULT_SETTINGS`; apelat de pipeline cu `INTERNAL_API_TOKEN` |
| GET | `/api/settings/:key` | Internal | `settingsController.ts → getSetting` | Single key; returnează default dacă lipsește |
| PUT | `/api/settings/:key` | JWT | `settingsController.ts → updateSetting` | UPSERT + validare + audit log + trigger reload |
| DELETE | `/api/settings/:key` | JWT | `settingsController.ts → deleteSetting` | Șterge cheia + audit log + trigger reload |

Chei cunoscute: `openrouter_api_key`, `ai_model`, `ai_temperature`, `tesseract_path`, `vision_max_pages`, `batch_concurrency`. Vezi [configuration.md#chei-cunoscute](./configuration.md#chei-cunoscute).

---

## Pipeline — /api/pipeline/*

Expus la `:8001` pe rețeaua Docker. NU are autentificare internă — acces controlat prin rețea.

| Method | Path | Auth | Handler | Note |
|--------|------|------|---------|------|
| GET | `/api/pipeline/health` | none | `pipeline/api.py:112` | `{status: "ok", service: "python-pipeline"}` |
| POST | `/api/pipeline/process` | none | `pipeline/api.py:145` | multipart `file` (PDF); rulează `process_document()`; returnează `{filename, classification, confidence, method, extraction, review_status, review_reasons, used_vision, page_count, total_duration_ms, error}`. `extraction` include: `material`, `data_expirare`, `companie`, `producator`, `distribuitor`, `adresa_producator`, `adresa_distribuitor`, `extraction_model` (toate `string \| null`). `review_reasons` conține obiecte `{reason, field, message}` — vezi [`extraction-logic.md`](./extraction-logic.md) pentru lista de reasons (ex. `suspicious_past_expiry`, `distribuitor_not_romanian`). |
| POST | `/api/pipeline/batch` | none | `pipeline/api.py:185` | `{folder_path}`; scanează folder + procesează fiecare PDF; returnează `{total, results: [...]}` |
| GET | `/api/pipeline/stats` | none | `pipeline/api.py:135` | Stats in-memory de la ultimul startup: `{total_processed, successful, failed, avg_duration_ms, classification_methods, categories, ai_calls, ai_failures}` |
| POST | `/api/pipeline/reload-settings` | none | `pipeline/api.py:118` | Re-citește settings din backend (cu `INTERNAL_API_TOKEN`); returnează `{status, changed: [...], current: {...}}` |

**Timeout-uri backend→pipeline** (vezi `src/services/pipelineClient.ts`):
- Normal: 300,000ms (5 min)
- File >1MB (probabil Vision fallback): 600,000ms (10 min)
- Health check: 5s

---

## Erori standard

Toate rutele backend răspund cu:

```json
{
  "error": {
    "name": "ErrorType",       // "ValidationError", "AuthError", "NotFoundError", etc.
    "message": "Mesaj în română",
    "code": "ERROR_CODE"         // "MISSING_TOKEN", "INVALID_TOKEN", "RATE_LIMIT", etc.
  }
}
```

Status codes folosite:
- `400` — request invalid (validare Zod, parametru lipsă)
- `401` — auth lipsă/invalidă
- `403` — permisiuni (admin, register dezactivat, owner mismatch)
- `404` — resursă negăsită
- `409` — conflict (ex: user deja există)
- `422` — procesare eșuată (pipeline returnează eroare)
- `500` — eroare internă

## Rate limiting

| Scope | Limit | Key | Cod |
|-------|-------|-----|-----|
| `/api/auth/login`, `/api/auth/register` | 5/min | IP | `authLimiter` — `src/middleware/rateLimiter.ts:8` |
| `/api/*` | 2000/min | IP | `apiLimiter` — `src/middleware/rateLimiter.ts:34` |

IP-ul real e extras din `X-Forwarded-For` cu `app.set('trust proxy', 1)` (nginx + Cloudflare = 2 hop-uri, dar trust 1 pentru că Cloudflare pune IP-ul real, nginx îl forwardează). Vezi `src/index.ts:67`.

> **De ce 2000/min global:** AlertsPage face fetch de detalii în paralel pentru fiecare document; la 300+ docs vechiul cap 100/min trunchia burst-ul. 2000 e rezonabil fiind ajutat și de JWT + Cloudflare.

## Verify freshness

```bash
# 5 router factories există
ls src/routes/*.ts | wc -l
# trebuie 5: adminUsers, auditLogs, auth, documents, settings

# Pipeline are 5 endpoints
grep -E "^@app\.(get|post)" pipeline/api.py
# trebuie 5 match-uri

# Rata limit 2000/min e în vigoare
grep -A5 "apiLimiter" src/middleware/rateLimiter.ts | grep "limit:"

# Rutele documents sunt toate cele 10
grep -E "router\.(get|post|patch|delete)" src/routes/documents.ts | wc -l
# trebuie 10
```
