---
title: Deployment (producție + Cloudflare Tunnel)
scope: deployment
stability: runbook
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./configuration.md
  - ./runbook.md
  - ./troubleshooting.md
code_refs:
  - docker-compose.yml
  - frontend/Dockerfile
  - frontend/nginx/default.conf
  - pipeline/Dockerfile
  - Dockerfile
---

# Deployment

Topologia de producție a Makyol Automation. Sistemul rulează pe un **PC Windows** cu Docker Desktop, expus public prin **Cloudflare Tunnel**. Acest doc descrie shape-ul deploy-ului și fișierele din afara repo-ului. Pentru proceduri operaționale (rebuild, seed admin, rotate key) vezi [runbook.md](./runbook.md).

## URL public

**Live:** `https://makyol.voostvision.ro`

## Request path

```
Browser
 └─► Cloudflare edge (TLS termination, DDoS shield)
      └─► cloudflared tunnel (outbound din Windows PC)
           └─► nginx (Docker container frontend, :80)
                ├─► /            → static Vite bundle
                ├─► /api/        → http://backend:3000  (timeout 600s)
                ├─► /uploads/    → http://backend:3000
                └─► /health      → http://backend:3000/health
```

**Notă:** backend-ul NU e expus direct către host (doar `expose: 3000` în compose, fără `ports:` publicat). Toate request-urile HTTP vin prin nginx. Pipeline-ul e expus pe `:8001` host pentru debugging; nu e routat prin tunel.

## Docker services

Definite în `docker-compose.yml`. Toate cu `restart: unless-stopped`.

| Service | Image | Port host | Port intern | Rol |
|---------|-------|-----------|-------------|-----|
| `postgres` | `postgres:15-alpine` | `5432:5432` | 5432 | Date + audit log |
| `backend` | `makyol-automation-backend` (custom) | — (doar expose) | 3000 | API Node/Express |
| `pipeline` | `makyol-automation-pipeline` (custom) | `8001:8001` | 8001 | FastAPI worker (Python) |
| `frontend` | `makyol-automation-frontend` (custom) | `${FRONTEND_PORT:-80}:80` | 80 | nginx + Vite bundle |

**Volume:**
- `postgres_data` — named volume (date PostgreSQL, local SSD)
- `./uploads` — bind mount în backend + pipeline (PDF-uri)
- `./logs/backend`, `./logs/pipeline` — bind mount log-uri (rotație 50MB × 5)
- `./migrations` → `/docker-entrypoint-initdb.d` (postgres, doar la primul boot)

**Healthcheck-uri:**
- postgres: `pg_isready`
- backend: `node http.get('/health')`
- pipeline: `curl /api/pipeline/health`
- frontend: `curl http://127.0.0.1/` (necesită `apk add curl`, altfel `wget` din busybox eșuează)

## Cloudflare Tunnel

Tunel outbound de pe Windows PC → Cloudflare edge, deci nu sunt necesare porturi deschise pe firewall.

### Fișiere (toate pe Windows PC, **în afara repo-ului**)

| Ce | Unde |
|----|------|
| Binar `cloudflared` standalone (fără MSI/service) | `C:\Users\meler\bin\cloudflared.exe` |
| Config tunel | `C:\Users\meler\.cloudflared\config.yml` |
| Credentiale tunel | `C:\Users\meler\.cloudflared\<tunnel-id>.json` + `cert.pem` |
| Auto-start la logon | `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Cloudflared_Makyol.vbs` |

**Tunnel ID:** `4ff0a742-bf11-4497-a643-f902c7aaae8a` (name: `makyol-beta`)

### `config.yml` (conceptual)

```yaml
tunnel: 4ff0a742-bf11-4497-a643-f902c7aaae8a
credentials-file: C:\Users\meler\.cloudflared\4ff0a742-bf11-4497-a643-f902c7aaae8a.json

ingress:
  - hostname: makyol.voostvision.ro
    service: http://localhost:80
  - service: http_status:404
```

### VBS auto-start

Fișierul `.vbs` din Startup folder lansează `cloudflared.exe` ascuns la fiecare logon al utilizatorului. **Dezavantaj:** tunelul moare la logoff (nu doar la lock). PC-ul trebuie să rămână logat pentru ca URL-ul să fie accesibil.

> **De ce VBS în Startup în loc de `cloudflared service install`:** shell-ul Claude Code nu are permisiuni să creeze Windows services sau scheduled tasks (`schtasks` → Access Denied). VBS în Startup folder e user-level, nu necesită elevare. Trade-off acceptat.

## Dockerfile-uri

### Backend (`./Dockerfile`) — multi-stage

- **Builder:** `node:18-alpine`, copy `package*.json` + `tsconfig.json` + `src/`, `npm install` + `npm run build`
- **Runtime:** `node:18-alpine` + `dumb-init`, user non-root `nodejs:1001`, copy `dist/` + `package*.json`, `npm install --production`, `EXPOSE 3000`, healthcheck curl `/health`, CMD `npm start`

### Pipeline (`./pipeline/Dockerfile`)

- Base: `python:3.11-slim`
- System deps: `tesseract-ocr tesseract-ocr-ron tesseract-ocr-eng curl`
- User non-root: `pipeline:1001`
- Copy `pipeline/` + `requirements.txt` → pip install
- `EXPOSE 8001`, healthcheck `curl /api/pipeline/health`
- CMD `uvicorn pipeline.api:app --host 0.0.0.0 --port 8001`

### Frontend (`./frontend/Dockerfile`) — multi-stage

- **Builder:** `node:20-alpine`, accept build args `VITE_REGISTER_ENABLED` + `VITE_AUTH_DISABLED`, `npm ci` + `npm run build`
- **Runtime:** `nginx:alpine`, `apk add --no-cache curl` (pentru healthcheck), copy `dist/` → `/usr/share/nginx/html`, copy `nginx/default.conf` → `/etc/nginx/conf.d/default.conf`, `EXPOSE 80`, healthcheck `curl -fsS http://127.0.0.1/`

## Hardening checklist (beta închis)

Actualizat 2026-04-18:

| Flag / setting | Valoare prod | De ce |
|---|---|---|
| `JWT_SECRET` | generat cu `openssl rand -hex 32` | Compose refuză start fără `?:...` check |
| `REGISTER_ENABLED` | `false` | Admin creează users prin `/admin/users` |
| `VITE_REGISTER_ENABLED` | `false` (build arg) | Frontend-ul ascunde ruta `/register` |
| `AUTH_DISABLED` | `false` (NU seta true) | Doar dev |
| `INTERNAL_API_TOKEN` | secret ≥16 chars (`openssl rand -hex 32`) | Fără el, reload-ul de setări din pipeline primește 401 |
| `CORS_ORIGIN` | include `https://makyol.voostvision.ro` | Altfel browser-ul respinge la fetch dacă vreodată domeniul se schimbă |
| `app.set('trust proxy', 1)` | setat (`src/index.ts:67`) | IP real pentru rate limiters |
| `apiLimiter.limit` | 2000/min | AlertsPage face N detail fetch-uri în paralel |
| Backend port host | NU publicat | Doar nginx vede backend |
| `OPENROUTER_API_KEY` | setat în `.env` + sincronizat în `settings` table | DB e autoritativ; `.env` e fallback la boot |

## Constrângeri cunoscute

- **Docker Desktop pe Windows cere sesiune logată.** Dacă PC-ul se delogează (nu doar lock), Docker engine se oprește și app-ul returnează 502 prin tunel. Tunelul rămâne up. Soluție: păstrează PC-ul logat.
- **Volum Postgres pe SSD local, fără backup automat.** `pg_dump` manual (vezi [runbook.md#backup-restore](./runbook.md#backup-restore)). Flag de rezolvat înainte de onboarding mai mulți useri.
- **`scripts/create-admin.ts` NU e în imaginea prod** — folosește one-liner-ul inline din [runbook.md#seed-admin](./runbook.md#seed-admin).
- **Setting UI permite model care nu există.** Dacă tastezi greșit un nume de model (ex: `google/gemini-invalid`), pipeline-ul obține 404 de la OpenRouter și cade pe regex. Noul dropdown din UI restrânge la 9 modele Vision-capable validate.
- **Pipeline NU autentifică apelurile venite la `:8001`.** Toate apelurile vin de la backend pe rețeaua Docker. Dacă expui `:8001` extern, lock-uiește cu același `INTERNAL_API_TOKEN`.
- **Multi-certificate PDFs** (un PDF cu 2+ certificate separate) — Gemini returnează array de obiecte; normalizatorul așteaptă un singur obiect și aruncă `'list' object has no attribute 'items'`. Workaround: reprocess individual după split. Fix durabil: detectează `isinstance(ai_result, list)` în `pipeline/__init__.py::process_document`, merge non-null fields peste siblings.
- **OpenRouter key hardcodat** în `pipeline/config.py:157` ca fallback dev — invalidată; nu folosește pentru dezvoltare.

## Cum schimbi hosting-ul

Arhitectura nu e legată de Windows sau Cloudflare. Pentru migrare:

- **Orice Docker host** (Linux VM, Mac Mini, AWS EC2) — compose file-ul rulează identic. Rețeaua internă Docker e aceeași.
- **Tunel alternativ** — poți înlocui Cloudflare Tunnel cu: Tailscale Funnel, ngrok, port-forward direct + cert Let's Encrypt pe nginx. Modifici doar `frontend/nginx/default.conf` și config-ul tunelului.
- **Docker host fără GUI** (server Linux) — rezolvă problema "sesiune delogată" din Windows; pe Linux serviciile Docker rulează independent.

Detalii migrare concret într-un ADR dedicat dacă/când se întâmplă.

## Verify freshness

```bash
# 4 servicii în compose
grep -E "^  (postgres|backend|pipeline|frontend):" docker-compose.yml
# 4 match-uri

# Backend NU are `ports:` expus (doar expose:)
grep -B2 "3000:3000" docker-compose.yml
# NU trebuie găsit

# Pipeline are port 8001 expus
grep "8001:8001" docker-compose.yml
# 1 match

# Frontend cu curl pentru healthcheck
grep "apk add.*curl" frontend/Dockerfile
# 1 match

# Nginx timeout 600s
grep -E "proxy_(read|send)_timeout\s+600" frontend/nginx/default.conf
# trebuie ≥ 1 match

# Cloudflared config există (pe Windows PC, în afara repo)
# ls "C:\Users\meler\.cloudflared\config.yml"

# Tunnel up
curl -sI https://makyol.voostvision.ro/health
# HTTP/2 200 când e up; HTTP/2 502 când Docker Desktop e jos
```
