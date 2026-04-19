---
title: Configurare (env vars + settings table)
scope: configuration
stability: living
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./runbook.md
  - ./auth-and-access.md
code_refs:
  - .env.example
  - docker-compose.yml
  - src/services/settingsService.ts
  - src/models/settings.ts
  - pipeline/config.py
---

# Configurare

Două surse de configurare:

1. **Env vars** — citite la startup din `.env` (sau valori Compose default-uri). Pentru lucruri care nu se schimbă des (JWT secret, CORS, DB host).
2. **Tabel `settings` în Postgres** — editabil prin UI sau API. Pentru lucruri care se schimbă des (model AI, cheie OpenRouter, concurență batch).

**Regula esențială:** unde o cheie apare în ambele locuri (ex: `OPENROUTER_API_KEY`), **valoarea DB e autoritativă**; `.env` e doar fallback pentru boot sau mod dev fără DB. Pipeline-ul citește DB la startup (cu retry) și re-citește la `POST /api/pipeline/reload-settings`.

## Env vars

Valorile reale trăiesc în `.env` (gitignored). Template-ul e `.env.example`. În Compose, unele chei sunt forțate ca required (`${JWT_SECRET:?...}`) ceea ce înseamnă că containerul refuză să pornească fără ele.

| Cheie | Required | Default | Sursă | Scop |
|-------|----------|---------|-------|------|
| `NODE_ENV` | no | `development` | `.env` / Compose | `development` / `production` / `test` |
| `PORT` | no | `3000` | `.env` / Compose | Port backend intern |
| `LOG_LEVEL` | no | `info` | `.env` | `debug`/`info`/`warn`/`error` (Winston) |
| `DB_HOST` | yes | `postgres` (Compose) / `localhost` (dev) | `.env` / Compose | Host Postgres |
| `DB_PORT` | yes | `5432` | `.env` / Compose | |
| `DB_USER` | yes | `postgres` | `.env` / Compose | |
| `DB_PASSWORD` | yes | `postgres` (demo) | `.env` / Compose | **Rotează în prod** |
| `DB_NAME` | yes | `pdfextractor` | `.env` / Compose | |
| `DB_POOL_MIN` | no | `2` | `.env` | pg.Pool min connections |
| `DB_POOL_MAX` | no | `10` | `.env` | pg.Pool max connections |
| `MAX_FILE_SIZE` | no | `10485760` (10MB) | `.env` / Compose | Upload limit per fișier (multer) |
| `UPLOAD_DIR` | no | `./uploads` | `.env` / Compose | Destinație PDF-uri încărcate |
| `API_PREFIX` | no | `/api` | `.env` / Compose | Prefix rute backend |
| `CORS_ORIGIN` | no | `http://localhost:5173` | `.env` / Compose | CSV list; în prod include `https://makyol.voostvision.ro` |
| `PUBLIC_URL` | no | `http://localhost` | `.env` | Doar documentare/logging |
| `PIPELINE_URL` | yes | `http://pipeline:8001` (Compose) / `http://localhost:8001` (dev) | Compose | URL pipeline pentru backend |
| `OPENROUTER_API_KEY` | **yes (prod)** | — | `.env` / Compose | Fallback pentru Vision AI; valoarea DB e autoritativă |
| `AI_MODEL` | no | `google/gemini-2.5-flash` | `.env` / Compose | Model default; hot-reloadabil din DB |
| `JWT_SECRET` | **yes (prod)** | — (Compose refuză să pornească) | `.env` | Semnarea JWT. Generează: `openssl rand -hex 32` |
| `JWT_EXPIRES_IN` | no | `7d` | `.env` | Durată token |
| `REGISTER_ENABLED` | no | `false` | `.env` / Compose | `POST /api/auth/register` întoarce 403 când `false`. Flip temporar la `true` pentru primul admin |
| `AUTH_DISABLED` | no | `false` | `.env` | **NU** seta `true` în prod; bypass JWT complet |
| `INTERNAL_API_TOKEN` | **yes (prod)** | — | `.env` / Compose | Secret partajat backend↔pipeline pentru `GET /api/settings`. Min 16 chars. Generează: `openssl rand -hex 32` |
| `VITE_REGISTER_ENABLED` | no | `false` | Compose build arg | Ascunde ruta `/register` în bundle frontend |
| `FRONTEND_PORT` | no | `80` | Compose | Port host pentru nginx |
| `BACKEND_API_URL` | no | `http://backend:3000` | Compose (pipeline) | Pipeline folosește pentru fetch settings |
| `ADMIN_EMAIL` | comentat | — | `.env` | Consumat de `scripts/create-admin.ts` (nu shippat în imaginea prod) |
| `ADMIN_PASSWORD` | comentat | — | `.env` | Idem |
| `PIPELINE_OCR_POOL_SIZE`, `PIPELINE_PAGE_RENDER_POOL_SIZE`, `PIPELINE_TEXT_ENGINE_POOL_SIZE` | no | `3`/`4`/`4` | Env pipeline | Dimensiune pool-uri interne (vezi `pipeline/thread_pools.py`) |

### Settings specifice serviciilor

**Backend** citește toate env vars de mai sus. Config derivat: `src/config/app.ts`, `src/config/database.ts`.

**Pipeline** citește: `BACKEND_API_URL`, `INTERNAL_API_TOKEN`, `OPENROUTER_API_KEY` (fallback), `AI_MODEL` (fallback), plus pool sizing.

**Frontend (build-time)** citește doar `VITE_*`: `VITE_REGISTER_ENABLED`.

## Tabel `settings` (DB autoritativ)

Definit de migration `004_create_settings_table.sql`: `(key VARCHAR PK, value JSONB, created_at, updated_at)`. Citire/scriere prin `src/models/settings.ts::SettingModel`; logica de validare în `src/services/settingsService.ts`.

### Chei cunoscute

Enum-ul `SettingKey` în `src/models/settings.ts:36-43` definește cheile cu type-safety. Default-urile sunt în `src/services/settingsService.ts:9-15`. Validarea în `src/services/settingsService.ts:28-76`.

| Cheie | Tip | Default | Validare | Hot-reload pipeline? | Notă |
|-------|-----|---------|----------|---------------------|------|
| `openrouter_api_key` | string | — | required | ✅ | Valoarea DB e sursă de adevăr; `.env` fallback |
| `ai_model` | string | `google/gemini-2.5-flash` | options list (9 modele Vision-capable) | ✅ | `google/gemini-2.5-pro`, `anthropic/claude-sonnet-4.5`, etc. Lista completă în `src/services/settingsService.ts:40-50` |
| `ai_temperature` | number | `0.0` | `[0, 1]` | ✅ | Păstrat la 0.0 pentru stabilitate extracție |
| `tesseract_path` | string | `D:\Tesseract-OCR\tesseract.exe` | optional | ✅ (doar Windows) | Linux ignoră setarea, folosește `/usr/bin/tesseract` (vezi `pipeline/config.py:166-171`) |
| `vision_max_pages` | number | `3` | `[1, 10]` | ✅ | Pipeline randerează primele (N-1) pagini + ultima |
| `batch_concurrency` | number | `3` | `[1, 10]` | ❌ (backend-only, re-citit la fiecare request) | Concurență `reprocess-all` |

### Hot-reload {#hot-reload}

**Flow:**
1. UI (`SettingsPage`) face `PUT /api/settings/:key` cu noua valoare.
2. Backend validează contra `VALIDATION_RULES`, face UPSERT în tabel, scrie audit log `CONFIG_CHANGE`.
3. Backend trimite fire-and-forget `POST http://pipeline:8001/api/pipeline/reload-settings` (timeout 5s).
4. Pipeline `reload_settings()` re-face `GET http://backend:3000/api/settings` cu `Authorization: Bearer INTERNAL_API_TOKEN`.
5. Pipeline actualizează singleton-ul `settings` în memorie; `pytesseract.tesseract_cmd` e rescris dacă path-ul s-a schimbat.

**Cod relevant:**
- Backend trigger: `src/controllers/settingsController.ts` (funcția `notifyPipelineReload`)
- Pipeline endpoint: `pipeline/api.py:118-132` (`@app.post("/api/pipeline/reload-settings")`)
- Pipeline fetch: `pipeline/config.py:31-76` (`fetch_settings_from_api`)
- Pipeline reload: `pipeline/config.py:201-242` (`reload_settings`)

**Caz de eșec:** dacă pipeline-ul e jos, save-ul din UI reușește (fire-and-forget, erori log-uite dar nu returnate). La next request sau la restart pipeline, valorile DB sunt re-citite oricum.

> **De ce fire-and-forget:** operatorul nu trebuie pedepsit dacă pipeline-ul e temporar nedisponibil. Setarea se păstrează în DB; pipeline-ul convergeează la noua valoare la următoarea oportunitate.

### Key chain pentru `openrouter_api_key`

```
UI → PUT /api/settings/openrouter_api_key → DB settings (jsonb)
                                         └─► POST /reload-settings (fire-and-forget)
                                              └─► pipeline reload_settings()
                                                   └─► GET /api/settings (cu INTERNAL_API_TOKEN)
                                                        └─► settings.openrouter_api_key := value

.env OPENROUTER_API_KEY → folosit doar dacă fetch-ul DB eșuează la boot
                          (retry 5× × 2s, apoi cădere pe .env)
```

> **Atenție istoric:** la 2026-04-18 s-a rotit cheia OpenRouter după ce cea veche a fost expusă în git history. Există un key hardcodat în `pipeline/config.py:157` ca fallback de last-resort dev — **nu e** o cheie validă în prod, a fost invalidată. Nu folosi pentru dezvoltare.

## Cum setezi o valoare

**Prin UI (recomandat pentru `ai_model`, `ai_temperature`, `openrouter_api_key`, etc.):**
Settings page → modifică → Save. Pipeline-ul reîncarcă automat.

**Prin CLI (pentru rotate-openrouter-key urgent sau seed):**
Vezi [runbook.md](./runbook.md#rotate-openrouter-key).

**Prin POST `/api/settings/initialize`:**
Populează default-urile pentru cheile care lipsesc din DB. Util la prima instalare.

## Verify freshness

```bash
# Cele 6 chei de settings trebuie să existe în enum
grep -E "^\s+[A-Z_]+ = '" src/models/settings.ts
# trebuie 6 linii

# Default-urile sunt setate
grep -A6 "DEFAULT_SETTINGS" src/services/settingsService.ts | head -20

# Validation rules pentru ai_model are listă de modele
grep -A11 "AI_MODEL" src/services/settingsService.ts | grep -E "'(google|anthropic|openai)"

# Env vars din .env.example sunt complete
grep -E "^[A-Z_]+=" .env.example | wc -l
# ≥ 18 chei

# INTERNAL_API_TOKEN e în Compose pentru ambele servicii
grep -c "INTERNAL_API_TOKEN" docker-compose.yml
# ≥ 2 match-uri

# Pipeline citește din backend cu header de auth
grep -n "_auth_headers" pipeline/config.py
# trebuie L22-28 + folosit în fetch
```
