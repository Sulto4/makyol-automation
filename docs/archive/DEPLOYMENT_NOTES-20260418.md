> **Snapshot arhivat.** Acest document comprehensiv al hardening-ului din 2026-04-18 a fost split în docs noi:
> - Topologie producție + Cloudflare Tunnel + hardening checklist → [../deployment.md](../deployment.md)
> - Bug chain (§5) transformat în simptom/cauză/fix durabil → [../troubleshooting.md](../troubleshooting.md)
> - Proceduri runbook (§6) → [../runbook.md](../runbook.md)
> - Env vars + settings autoritative → [../configuration.md](../configuration.md)
>
> Păstrat aici pentru istoric (rollout-ul închis-beta la 2026-04-18).

---

# Deployment Notes — Closed Beta (makyol.voostvision.ro)

_Last updated: 2026-04-18_

Comprehensive log of the closed-beta deployment: architecture, credentials locations, bug chain encountered during rollout, fixes applied, and runbook for common ops tasks.

---

## 1. Live URL & Stack

**Production URL:** <https://makyol.voostvision.ro>

**Request path (public → origin):**

```
Browser
 └─> Cloudflare edge (TLS termination, DDoS shield)
      └─> cloudflared tunnel (outbound from Windows PC)
           └─> nginx (Docker, port 80)
                ├─> /            → static Vite bundle from /usr/share/nginx/html
                ├─> /api/        → http://backend:3000  (proxy, 600s timeouts)
                ├─> /uploads/    → http://backend:3000  (proxy)
                └─> /health      → http://backend:3000/health
```

**Docker services** (all `restart: unless-stopped`):

| Service    | Image                          | Exposed to host | Role                                      |
|------------|--------------------------------|-----------------|-------------------------------------------|
| frontend   | `makyol-automation-frontend`   | `80:80`         | nginx:alpine + Vite static bundle         |
| backend    | `makyol-automation-backend`    | (internal only) | Node/Express — auth, routes, audit        |
| pipeline   | `makyol-automation-pipeline`   | `8001:8001`     | Python/FastAPI — classification, Vision AI|
| postgres   | `postgres:15-alpine`           | `5432:5432`     | Data store                                |

Backend dropped its host-level port after the hardening pass — only nginx publishes to the host. Postgres and pipeline ports are exposed for local debugging; neither is routed through the Cloudflare Tunnel.

---

## 2. Credentials & Key Files

**Do not commit any of these paths to git; `.env*` and `.cloudflared/` are ignored at repo level.**

| What                            | Where                                                                                |
|---------------------------------|--------------------------------------------------------------------------------------|
| Runtime env (prod secrets)      | `./.env` (gitignored)                                                                |
| Template for ops                | `./.env.example`                                                                     |
| Cloudflare tunnel credentials   | `C:\Users\meler\.cloudflared\cert.pem` and `<tunnel-id>.json`                        |
| Cloudflare tunnel config        | `C:\Users\meler\.cloudflared\config.yml`                                             |
| cloudflared binary              | `C:\Users\meler\bin\cloudflared.exe` (standalone, no MSI)                            |
| Auto-start at logon             | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Cloudflared_Makyol.vbs`     |
| Pre-hardening .env backup       | `./.env.backup.20260418-173905`                                                      |

**Runtime env vars worth knowing (see `.env.example` for the full list):**

- `JWT_SECRET` — required in prod, no fallback. Rotate via `openssl rand -hex 32`.
- `OPENROUTER_API_KEY` — required. The value in `.env` is a **fallback**; the authoritative value lives in the `settings` table in Postgres (managed through the Settings UI).
- `REGISTER_ENABLED=false` — public `POST /api/auth/register` returns 403. Flip to `true` only to seed the first admin, then flip back.
- `AUTH_DISABLED=false` — do NOT set to true in production.
- `INTERNAL_API_TOKEN` — shared secret for pipeline ↔ backend calls. ≥16 chars. Without this, settings hot-reload from pipeline breaks with 401 (see bug chain §5).
- `CORS_ORIGIN` — CSV list; include `https://makyol.voostvision.ro` for production.
- `VITE_REGISTER_ENABLED=false` — build arg baked into the frontend bundle; hides `/register` route and "create account" link.

---

## 3. Auth Model

- Single gate: JWT login at `/api/auth/login`. No Cloudflare Access overlay.
- First admin seeded via an inline `docker compose exec backend node -e "..."` one-liner (bcrypt + `pg`) against the `users` table (the TypeScript `scripts/create-admin.ts` script isn't shipped in the prod image).
- Admins create testers from **Sidebar → Utilizatori** (`/admin/users`). Generated passwords appear once in a copyable toast — there's no email delivery.
- `ProtectedRoute.adminOnly` bounces non-admins from admin-only routes.
- Rate limiters (Express):
  - `authLimiter`: 5/min/IP on `/api/auth/login` + `/api/auth/register` (brute-force guard).
  - `apiLimiter`: **2000/min/IP** on `/api` (deliberately generous — AlertsPage fires one detail fetch per document in parallel, and at 300+ docs a 100/min cap left the UI full of blank rows).
- `app.set('trust proxy', 1)` so both limiters key on the real client IP behind nginx + Cloudflare.

---

## 4. Extraction Stack

**Per-document flow inside the pipeline (`pipeline/__init__.py:process_document`)**

1. PDF rendered → text via `pymupdf`/`pdfplumber` (fallback chain).
2. Classification cascade (filename → regex text → AI → ALTELE).
3. **Every document** runs through Vision AI (flag `_USE_VISION_FOR_ALL = True`). Text-only extraction is kept as regex fallback when Vision returns None.
4. AI call: `POST https://openrouter.ai/api/v1/chat/completions` with `model = settings.ai_model` (currently `google/gemini-2.5-flash`).
5. Result normalized (category-specific rules: ISO material stripped, CUI merged, company alias matching, address KB reconcile).
6. Validation + review flag (OK / NEEDS_REVIEW).
7. `extraction_model` column in DB records the actual model used — prefix `vision:` for Vision-path, otherwise the raw model id.

Settings the Vision path reads live: `ai_model`, `ai_temperature`, `openrouter_api_key`, `vision_max_pages`, `tesseract_cmd`. All live in the `settings` Postgres table and are hot-reloaded by the backend hitting `POST /api/pipeline/reload-settings` after any UI save.

---

## 5. Bug Chain Encountered During Rollout (2026-04-18)

### 5.1 "Most documents show empty fields in the table"
**Symptom:** First 20–60 rows on Documents / Alerts pages looked fine; everything after was blank.
**Cause:** `AlertsPage` fires `useDocumentDetails(allIds)` for every document in parallel to compute expiration tabs. The post-hardening `apiLimiter` at 100 req/min/IP truncated that burst at ~100 requests — the remaining ~200 got `429 Too Many Requests` and their `extraction` fell back to null in the React Query cache.
**Fix:** Raised `apiLimiter.limit` from 100 to **2000 per minute** in `src/middleware/rateLimiter.ts`. Behind Cloudflare + JWT auth, the extra limiter is a secondary safety net and doesn't need to cap legitimate burst fetches.

### 5.2 "Reprocess All dropped material/producator to ~4 rows"
**Symptom:** After the first reprocess post-deploy, the DB had `with_material = 4`, `with_producator = 4` (baseline was 220 / 191). Pipeline fell back to `extraction_model = regex_fallback` for nearly every document.
**Cause:** The OpenRouter key baked into the pre-hardening `.env` had been rotated away by the owner; OpenRouter responded with `401 {"error":"User not found"}` to every chat/completions call. The pipeline swallowed the 401, fell through to regex extraction, and overwrote the previously-good DB rows.
**Fix:** Replaced the dead key in `.env` with the active one, restarted pipeline, re-ran reprocess. Probed `/auth/key`, `/credits`, and `/chat/completions` (two models) to confirm the dead key was truly invalid, not a transient blip.

### 5.3 "Settings change in UI doesn't propagate to the pipeline"
**Symptom:** User changed AI model in Settings UI → re-ran extraction on one doc → UI still showed `vision:gemini-2.0-flash`.
**Cause:** The post-hardening backend puts `authGuard` in front of `/api/settings`. Pipeline's `pipeline/config.py :: fetch_settings_from_api()` made unauthenticated `GET /api/settings` calls at startup and on every `reload_settings()` invocation → all returned 401 → pipeline silently stayed on its env-var fallbacks.
**Fix:**
1. New env var `INTERNAL_API_TOKEN` (≥16 chars) — a shared secret between backend and pipeline.
2. `src/middleware/authMiddleware.ts` accepts `Authorization: Bearer <INTERNAL_API_TOKEN>` as an alternate auth, synthesizing an "internal@pipeline" service user with `is_admin: true`.
3. `pipeline/config.py` now attaches the header via a small `_auth_headers()` helper; `docker-compose.yml` ships the same token to both services.

### 5.4 "extraction_model column always shows gemini-2.0-flash"
**Symptom:** Every Vision-path row displayed `vision:gemini-2.0-flash` regardless of which model actually served the request (logs clearly showed `google/gemini-2.5-flash`).
**Cause:** `pipeline/__init__.py:239` hardcoded `"gemini-2.0-flash"` as the fallback label when vision_fallback didn't propagate its own model name.
**Fix:** Replaced the frozen string with `settings.ai_model.replace("google/", "")` so the label tracks hot-reloaded settings. `pipeline/config.settings` is now imported at the top of `pipeline/__init__.py`.

### 5.5 "Frontend container is unhealthy"
**Symptom:** `docker ps` showed `pdfextractor-frontend` as `unhealthy` with `wget: Connection refused`.
**Cause:** nginx:alpine ships busybox wget; its default resolution order inside the Compose network tripped "Connection refused" against `localhost` even though nginx was listening on `0.0.0.0:80`.
**Fix:** `apk add --no-cache curl` in the frontend Dockerfile; healthcheck now `curl -fsS http://127.0.0.1/`.

---

## 6. Runbook

### 6.1 Rebuild + restart after code change

```bash
docker compose up -d --build
```

Use `--build <service>` to target just one (e.g., `backend`). Compose respects `depends_on` healthchecks — backend waits for Postgres, frontend waits for backend.

### 6.2 Seed / reset the admin account

```bash
docker compose exec -e ADMIN_EMAIL=you@example.com -e ADMIN_PASSWORD=choose-a-strong-one backend \
  node -e "
const bcrypt = require('bcryptjs');
const { Pool } = require('pg');
(async () => {
  const pool = new Pool({
    host: process.env.DB_HOST, port: +process.env.DB_PORT,
    user: process.env.DB_USER, password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
  });
  const e = process.env.ADMIN_EMAIL.trim().toLowerCase();
  const existing = await pool.query('SELECT id FROM users WHERE email = \$1', [e]);
  if (existing.rows.length) { console.log('exists'); await pool.end(); return; }
  const hash = await bcrypt.hash(process.env.ADMIN_PASSWORD, 10);
  const res = await pool.query(
    'INSERT INTO users (email, password_hash, is_admin) VALUES (\$1, \$2, true) RETURNING id, email',
    [e, hash]);
  console.log('created', res.rows[0]); await pool.end();
})();
"
```

### 6.3 Kick reprocess-all from the CLI

```bash
ADMIN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<admin-email>","password":"<password>"}' \
  | grep -oE '"token":"[^"]+"' | cut -d'"' -f4)
curl -s -X POST http://localhost/api/documents/reprocess-all \
  -H "Authorization: Bearer $ADMIN"
```

To interrupt a long-running reprocess-all (it's an in-memory async job on the backend):

```bash
docker compose restart backend
```

### 6.4 Rotate the OpenRouter key

The authoritative value lives in Postgres, not `.env`:

```bash
NEW_KEY='sk-or-v1-...'
docker exec -i pdfextractor-postgres psql -U postgres -d pdfextractor -v new_key="$NEW_KEY" <<'SQL'
UPDATE settings SET value = to_jsonb(:'new_key'::text), updated_at = NOW() WHERE key = 'openrouter_api_key';
SQL
curl -s -X POST http://localhost:8001/api/pipeline/reload-settings
```

Also update `./.env:OPENROUTER_API_KEY` to keep it aligned as the fallback.

### 6.5 Stop / start the Cloudflare tunnel

```bash
# Stop (public URL goes 502 until restarted)
taskkill /PID <cloudflared-pid> /F

# Start manually
wscript.exe "C:\Users\meler\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Cloudflared_Makyol.vbs"

# Disable auto-start entirely: delete the VBS above.
```

Tunnel state and edge connections are visible on the Cloudflare Zero Trust dashboard under **Networks → Tunnels → makyol-beta**.

### 6.6 Database fill-rate sanity check

```bash
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor -c "
SELECT
  COUNT(*) FILTER (WHERE material IS NOT NULL AND material <> '')       AS with_material,
  COUNT(*) FILTER (WHERE companie IS NOT NULL AND companie <> '')       AS with_companie,
  COUNT(*) FILTER (WHERE producator IS NOT NULL AND producator <> '')   AS with_producator,
  COUNT(*) FILTER (WHERE data_expirare IS NOT NULL AND data_expirare <> '') AS with_expiry,
  COUNT(*) FILTER (WHERE adresa_producator IS NOT NULL AND adresa_producator <> '') AS with_addr
FROM extraction_results;
"
```

Pre-hardening baseline on the 328-document set: `material=220, companie=287, producator=191, expiry=165, addr=187`. A healthy post-reprocess run should land at or above these numbers.

**Post-hardening result (2026-04-18, after key rotation + settings fix + multi-cert fix):**

| Field         | Baseline | After | Δ    |
|---------------|----------|-------|------|
| material      | 220      | 221   | +1   |
| producator    | 191      | 196   | +5   |
| data_expirare | 165      | 179   | +14  |
| adresa        | 187      | 290   | +103 |
| companie      | 287      | 223   | -64  |

`companie` dropped because (a) Gemini 2.5 Flash is more conservative about speculative matches, and (b) the multi-cert fallback currently picks the first JSON object — for combined ISO docs that first object is often the certifying body, which is then rejected as "cert body on ISO doc" by the validator. Improving `companie` recall would mean merging non-null fields across the array instead of dropping everything but element 0. Noted but not urgent — the material/producator/expiry fields that drive material-package exports all improved.

---

## 7. Known Limitations & Open Items

- **Docker Desktop on Windows requires an active user session.** If the PC logs off (not just locks), the Docker engine stops and the app returns 502 through the tunnel. The tunnel itself stays up. Mitigation: keep the host logged in.
- **Postgres volume is on the local SSD with no automated backup.** Manual `pg_dump` is the only disaster-recovery path today. Fine for a closed beta with a handful of testers; flag for early resolution before onboarding more users.
- **`scripts/create-admin.ts` doesn't ship in the prod image.** The Node one-liner in §6.2 is the workaround; either copy `scripts/` into the backend Dockerfile or compile the TS file ahead of time if this becomes a frequent operation.
- **OpenRouter key was exposed in git history** before the required-secrets refactor. The prior key has been rotated and confirmed dead (§5.2); the `.env.backup.20260418-173905` file at repo root still contains the old value and should be deleted once the migration is confirmed stable.
- **Settings UI currently lets you pick a model that doesn't exist** (e.g. a typoed `latest` variant). The pipeline then hits OpenRouter with the bad model id and returns regex-only extractions. Worth adding a dropdown validator against `/models` later.
- **Pipeline does not authenticate users.** All user-scoping happens in the backend (`owner_user_id` filters on SELECT/UPDATE/DELETE). This is intentional — the pipeline is a pure worker — but if you ever expose `pipeline:8001` outside the Docker network, lock it down behind the same `INTERNAL_API_TOKEN` check used for backend routes.
- **Multi-certificate PDFs crash extraction.** When a single PDF holds multiple certificates (e.g. `ISO 14001+45001 PETROUZINEX - semnat.pdf`), Gemini sometimes replies with a JSON **array** of objects (one per certificate) instead of the single object the normalizer expects. The result is `'list' object has no attribute 'items'` and the document is marked `extraction_status=failed`. Workaround for now: reprocess such docs individually after splitting. Proper fix: in `pipeline/__init__.py::process_document` (or wherever the vision response is unpacked), detect `isinstance(ai_result, list)` and either pick the first element or merge non-null fields across siblings before handing to `normalize_extraction_result`.
