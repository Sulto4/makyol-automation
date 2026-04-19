---
title: Troubleshooting (simptom → cauză → fix)
scope: troubleshooting
stability: runbook
last_verified: 2026-04-19
related:
  - ./runbook.md
  - ./configuration.md
  - ./deployment.md
  - ./auth-and-access.md
code_refs:
  - src/middleware/rateLimiter.ts
  - src/middleware/authMiddleware.ts
  - pipeline/config.py
  - pipeline/__init__.py
---

# Troubleshooting

Lookup simptom → cauză → fix pentru problemele observate în producție. Fiecare intrare e un eveniment real transformat într-un reminder durabil. Pentru comenzi operaționale vezi [runbook.md](./runbook.md).

## Rânduri goale în tabelul de documente / AlertsPage {#alerts-empty-rows}

**Simptom:** primele 20-60 rânduri au date, restul sunt goale. DocumentsPage / AlertsPage arată category/filename dar câmpurile extrase (material, companie, etc.) lipsesc pe multe rânduri.

**Cauză probabilă:** rate limiter global trunchiat. AlertsPage face `useDocumentDetails(allIds)` — un fetch per document în paralel. La 300+ docs, burst-ul depășește cota apiLimiter. Backend returnează 429 `Too Many Requests`; React Query cache-uiește răspunsul cu `extraction: null`.

**Fix:** verifică `apiLimiter.limit` în `src/middleware/rateLimiter.ts:34`. Trebuie ≥ 2000:

```bash
grep -A5 "apiLimiter" src/middleware/rateLimiter.ts | grep "limit:"
```

Dacă e 100 (setare inițială), crește la 2000 + `docker compose up -d --build backend`. Comportamentul gol dispare după refresh.

**Prevenire:** la scalare utilizatori reali, monitorizează numărul de docs per user — dacă unii ajung la 1000+ docs, ia în calcul paginarea AlertsPage sau fetch on-demand.

---

## Reprocess-all scade material/producator la ~4 {#reprocess-fill-rate-drop}

**Simptom:** rulezi `POST /api/documents/reprocess-all`, după termen fill-rate-ul cade de la 220 la 4 pe `material` și producator. UI arată `extraction_model = regex_fallback` pe toate docs recent procesate.

**Cauză probabilă:** cheia OpenRouter e invalidă (rotită, expirată, suspendată). Pipeline-ul primește 401 de la OpenRouter, prinde excepția tăcut și cade pe regex extraction, suprascriind rândurile cu rezultate mult mai slabe.

**Fix:**

1. Verifică cheia:
   ```bash
   docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
     -c "SELECT value->>'openrouter_api_key' FROM settings WHERE key='openrouter_api_key';" \
     | tail -3 | cut -c1-12
   # primele caractere trebuie să înceapă cu sk-or-v1-
   ```

2. Test rapid OpenRouter:
   ```bash
   CURRENT_KEY=$(docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
     -t -c "SELECT value::text FROM settings WHERE key='openrouter_api_key';" | tr -d '"' | xargs)
   curl -s https://openrouter.ai/api/v1/auth/key -H "Authorization: Bearer $CURRENT_KEY"
   ```

3. Dacă `401 {"error":"User not found"}` → rotește cheia. Vezi [runbook.md#rotate-openrouter-key](./runbook.md#rotate-openrouter-key).

4. După rotate: re-rulează reprocess-all. Fill-rate trebuie să revină la baseline.

**Prevenire:** nu commit-ui cheia OpenRouter. `.env.example` are placeholder. Dacă o cheie a fost expusă accidental (git push cu secret), rotește imediat și consideră git history compromisă.

---

## Settings din UI nu ajung la pipeline {#settings-not-propagating}

**Simptom:** schimbi `ai_model` din Settings UI, re-procesezi un doc, UI arată `extraction_model = vision:gemini-2.5-flash` deși ai setat `anthropic/claude-sonnet-4.5`.

**Cauză probabilă 1:** `INTERNAL_API_TOKEN` lipsește sau e < 16 chars. Pipeline-ul cheamă `GET /api/settings` → backend returnează 401 → pipeline-ul înghițe eroarea și rămâne pe valorile vechi.

**Cauză probabilă 2:** backend-ul nu apelează `POST /api/pipeline/reload-settings` după save. Verifică logurile.

**Fix pentru cauza 1:**

```bash
# Verifică că e setat în env-ul backend + pipeline
docker compose exec backend printenv INTERNAL_API_TOKEN | wc -c    # ≥ 16 + \n
docker compose exec pipeline printenv INTERNAL_API_TOKEN | wc -c   # ≥ 16 + \n
```

Dacă oricare e gol:
```bash
# Generează un token nou
openssl rand -hex 32
# Pune în .env: INTERNAL_API_TOKEN=<valoarea generată>
docker compose up -d backend pipeline
```

**Fix pentru cauza 2:**

```bash
# Forțează manual reload
curl -s -X POST http://localhost:8001/api/pipeline/reload-settings
# Răspunsul trebuie să conțină `changed` și `current` cu noul model
```

**Prevenire:** secția `## Verify freshness` din [configuration.md](./configuration.md#verify-freshness) include check-ul pentru INTERNAL_API_TOKEN în compose — rulează la deploy.

---

## Frontend container "unhealthy" {#frontend-unhealthy}

**Simptom:** `docker ps` sau `docker compose ps` arată `pdfextractor-frontend` cu status `unhealthy`. Aplicația răspunde totuși normal la request-uri. Sau: healthcheck eșuează cu `wget: Connection refused`.

**Cauză:** nginx:alpine vine cu busybox `wget` care are resolver DNS minimal. În contextul healthcheck-ului Docker, `wget` pe `localhost:80` uneori returnează Connection refused chiar dacă nginx ascultă la `0.0.0.0:80`.

**Fix:** asigură-te că `frontend/Dockerfile` instalează `curl` și healthcheck-ul folosește `curl`, nu `wget`:

```bash
grep -B1 -A1 "apk add.*curl\|curl.*http" frontend/Dockerfile
# trebuie: RUN apk add --no-cache curl
# trebuie: HEALTHCHECK ... CMD curl -fsS http://127.0.0.1/
```

Dacă lipsește, adaugă + rebuild:
```bash
docker compose up -d --build frontend
```

**Prevenire:** healthcheck-urile bazate pe busybox tool-uri sunt fragile. Preferă `curl` explicit.

---

## `extraction_model` arată un model vechi în ciuda schimbării {#stale-extraction-model-label}

**Simptom:** schimbi din UI `ai_model` la `google/gemini-2.5-flash`, re-procesezi docs, UI afișează `extraction_model = vision:gemini-2.0-flash` pentru fiecare rând.

**Cauză:** label-ul fallback era hardcodat în `pipeline/__init__.py`. Când codul nu primește numele modelului de la vision_fallback, folosește label-ul default. Bug istoric (pre-2026-04-18): label-ul hardcodat era `"gemini-2.0-flash"` indiferent ce model era activ.

**Fix:** label-ul trebuie să fie derivat dinamic din `settings.ai_model`. Verifică:

```bash
grep -n "vision:" pipeline/__init__.py
# nu trebuie să vezi literal "gemini-2.0-flash" — doar settings.ai_model.replace("google/", "")
```

Dacă găsești un literal hardcodat, înlocuiește cu `settings.ai_model.replace("google/", "")` (import `settings` în top-of-file).

**Prevenire:** testează extraction_model în timpul development: schimbă modelul din UI, re-procesează un singur doc, verifică label-ul în UI. Label-ul trebuie să urmărească modelul activ.

---

## Multi-certificate PDF crash {#multi-cert-crash}

**Simptom:** un PDF specific (ex: `ISO 14001+45001 XYZ - semnat.pdf`) eșuează cu `'list' object has no attribute 'items'`. `extraction_status = failed` în DB.

**Cauză:** Gemini detectează 2 certificate distincte în PDF, returnează JSON array de obiecte (unul per cert) în loc de un singur obiect. `normalize_extraction_result` iterează cu `.items()` pe structura primită și explodează pe tipul greșit.

**Fix rapid:** split manual PDF-ul în docs individuale, re-upload. Sau ignoră docs combinate.

**Fix durabil** (de implementat): în `pipeline/__init__.py::process_document`, după call-ul vision, detectează:

```python
if isinstance(ai_result, list):
    # Strategia 1: pick first
    ai_result = ai_result[0] if ai_result else {}
    # Strategia 2 (mai bună): merge non-null fields across siblings
    # ai_result = {k: v for item in ai_result for k, v in item.items() if v}
```

**Prevenire:** detectabil în advance — PDF-urile cu mai multe certificate au deseori `+` în filename (ex: `ISO+OHSAS`, `9001+14001+45001`).

---

## 502 la URL-ul public, local funcționează {#public-502-local-ok}

**Simptom:** `https://makyol.voostvision.ro` întoarce 502 Bad Gateway. `http://localhost/health` funcționează local.

**Cauză probabilă 1:** Docker Desktop e oprit (PC s-a delogat, Docker Desktop a cedat). Tunelul rămâne up și se plânge că upstream-ul localhost:80 nu răspunde.

**Cauză probabilă 2:** tunelul `cloudflared` s-a oprit (PC-ul s-a restart-at și VBS-ul de startup n-a pornit, sau procesul a murit).

**Fix:**

```bash
# Verifică Docker Desktop
docker compose ps
# Dacă "Cannot connect to Docker daemon" → pornește Docker Desktop din Start Menu

# Verifică tunelul cloudflared pe Windows (PowerShell):
# Get-Process cloudflared | Select-Object Id, StartTime
# Dacă lipsește → relansează VBS-ul:
wscript.exe "C:\Users\meler\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Cloudflared_Makyol.vbs"

# Verifică live
curl -sI https://makyol.voostvision.ro/health
```

**Prevenire:** setează Windows să nu se delogheze automat la inactivitate. Monitorizează tunelul din Cloudflare Zero Trust dashboard → Networks → Tunnels → `makyol-beta`.

---

## Pipeline nu pornește: "AI connectivity: AUTH FAILED" la startup {#pipeline-auth-failed}

**Simptom:** `docker compose logs pipeline --tail=30` arată `AI connectivity: AUTH FAILED (status=401, key=sk-or-v1-..., response=...)`. Pipeline răspunde totuși la `/health`, dar fiecare `/process` cade pe regex fallback.

**Cauză:** cheia OpenRouter invalidă la startup. Startup hook (`pipeline/api.py:60-98`) trimite un ping OpenRouter pentru validare. 401 indică key invalid.

**Fix:** rotire cheie (vezi [#reprocess-fill-rate-drop](#reprocess-fill-rate-drop)).

**Notă:** pipeline-ul NU se oprește la startup auth fail (prin design — să poată servi health checks și să permită rotația prin `/reload-settings` fără restart). Verifică sistematic log-ul după deploy.

---

## Docker compose up eșuează: "JWT_SECRET is required" {#compose-jwt-required}

**Simptom:** la `docker compose up -d`, compose refuză să pornească backend-ul cu mesaj `JWT_SECRET is required (openssl rand -hex 32)`.

**Cauză:** `.env` lipsește sau nu are `JWT_SECRET`. Compose (`docker-compose.yml:52`) are sintaxa `${JWT_SECRET:?...}` care forțează valoarea să existe.

**Fix:**

```bash
openssl rand -hex 32
# Copy output în .env: JWT_SECRET=<valoarea>
docker compose up -d
```

Același mecanism forțează și `OPENROUTER_API_KEY` (`docker-compose.yml:115`).

**Prevenire:** `.env.example` listează toate variabilele obligatorii. La instalare nouă, copy + completează.

---

## Căutat în grabă: locul exact al erorii

Când nu ești sigur unde să cauți:

| Simptom | Primul loc de verificat |
|---------|------------------------|
| 401 pe rute autentificate | `src/middleware/authMiddleware.ts` + env `JWT_SECRET` + `INTERNAL_API_TOKEN` |
| 403 pe `/register` | env `REGISTER_ENABLED` (trebuie `true` temporar) |
| 403 pe `/admin/*` | `src/middleware/authMiddleware.ts::requireAdmin` — userul nu e `is_admin=true` |
| 429 Too Many Requests | `src/middleware/rateLimiter.ts` |
| 500 la `/api/documents/*` | log backend + pipeline simultan (`docker compose logs -f backend pipeline`) |
| 422 la `/api/documents` | pipeline a returnat eroare; log pipeline |
| CSRF / CORS | `CORS_ORIGIN` în `.env` (listă CSV, include domeniul frontend) |
| Upload eșuează cu "File too large" | `MAX_FILE_SIZE` (backend) + `client_max_body_size` (nginx) |
| Settings save OK dar comportament vechi | pipeline nu a reîncărcat — curl `/api/pipeline/reload-settings` manual |

## Verify freshness

```bash
# apiLimiter la 2000
grep -A5 "apiLimiter" src/middleware/rateLimiter.ts | grep "limit:"
# trebuie 2000

# INTERNAL_API_TOKEN e ghidat în Compose
grep "INTERNAL_API_TOKEN:" docker-compose.yml | wc -l
# ≥ 2

# Frontend Dockerfile instalează curl
grep -c "apk add.*curl" frontend/Dockerfile
# ≥ 1

# Pipeline auth headers folosite la fetch
grep -n "_auth_headers\|INTERNAL_API_TOKEN" pipeline/config.py
# ≥ 2 match-uri

# Label dinamic pentru extraction_model (fără "gemini-2.0-flash" hardcodat)
grep -n "gemini-2.0-flash" pipeline/__init__.py
# NU trebuie găsit
```
