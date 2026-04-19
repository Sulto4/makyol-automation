---
title: Runbook (proceduri ops)
scope: runbook
stability: runbook
last_verified: 2026-04-19
related:
  - ./configuration.md
  - ./deployment.md
  - ./troubleshooting.md
code_refs:
  - docker-compose.yml
  - scripts/create-admin.ts
  - pipeline/api.py
---

# Runbook

Proceduri de ops pentru Makyol Automation. Fiecare intrare e self-contained cu trigger, pași, verificare și rollback.

**Mediul de bază:** comenzi rulate din repo root (`E:\Vibe Local Proiecte\makyol-automation`) în shell bash (Git Bash pe Windows). Pentru comenzi SQL împotriva containerului Postgres folosim `docker exec`.

---

## Rebuild + restart după o schimbare de cod

**Când rulezi:** ai schimbat cod în `src/`, `pipeline/`, `frontend/src/`, sau configurație Docker.

**Pași:**

```bash
docker compose up -d --build
```

Pentru un singur serviciu:

```bash
docker compose up -d --build backend       # doar backend
docker compose up -d --build pipeline      # doar pipeline
docker compose up -d --build frontend      # doar frontend
```

Compose respectă healthcheck-urile: backend așteaptă postgres, frontend așteaptă backend.

**Verifică:**

```bash
docker compose ps
# toate containerele trebuie "healthy" sau "running"

docker compose logs backend --tail=30
docker compose logs pipeline --tail=30
```

**Rollback:** `git revert` commit-ul problemă + `docker compose up -d --build`.

---

## Seed / reset admin {#seed-admin}

**Când rulezi:** prima instalare, admin uitat parola, sau vrei să creezi un admin de urgență.

**Sursa de adevăr:** tabelul `users` din Postgres. `scripts/create-admin.ts` NU e inclus în imaginea backend producție — folosește metoda inline de mai jos.

**Pași:**

```bash
docker compose exec -e ADMIN_EMAIL=you@example.com -e ADMIN_PASSWORD='choose-a-strong-one' backend \
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
    'INSERT INTO users (email, password_hash, is_admin, is_active) VALUES (\$1, \$2, true, true) RETURNING id, email',
    [e, hash]);
  console.log('created', res.rows[0]); await pool.end();
})();
"
```

**Verifică:**

```bash
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT id, email, is_admin, is_active FROM users WHERE email = 'you@example.com';"
```

**Reset parolă pentru admin existent:** fie folosește UI-ul `/admin/users` → click pe user → "Resetează parolă", fie rulează același SQL cu `UPDATE users SET password_hash = ...` (generează hash cu `bcrypt.hash(password, 10)`).

**Rollback:** `DELETE FROM users WHERE email = '...'` — atenție, va orfaniza documentele cu `owner_user_id = <acest UUID>`; în practică nu face rollback, doar dezactivează prin UI (`PATCH /admin/users/:id/active`).

> **De ce inline în loc de script:** Dockerfile-ul backend nu copiază `scripts/`. Variantele alternative (copiază scriptul, instalează `ts-node` în imaginea prod, compilează la JS) adaugă complexitate pentru o operație care se rulează de 2-3 ori.

---

## Kick reprocess-all de la CLI

**Când rulezi:** după rotate cheie OpenRouter, după schimbare model AI, sau pentru a re-procesa docs cu extraction incomplete.

**Pași:**

```bash
# 1. Obține token admin
ADMIN=$(curl -s -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"<admin-email>","password":"<password>"}' \
  | grep -oE '"token":"[^"]+"' | cut -d'"' -f4)

# 2. Pornește reprocess-all (job in-memory async pe backend)
curl -s -X POST http://localhost/api/documents/reprocess-all \
  -H "Authorization: Bearer $ADMIN"
```

**Concurență:** citită din `settings.batch_concurrency` (clamped `[1..10]`, default 3). Pentru a schimba concurency, update setarea din UI — efectul la următorul reprocess.

**Verifică:**

```bash
# Urmărește logul pipeline — ar trebui să vezi linii per document
docker compose logs pipeline --tail=50 -f

# Sanity check fill-rate după ce a terminat (vezi procedura de mai jos)
```

**Rollback / întrerupe:**

```bash
docker compose restart backend
```

Job-ul e in-memory; restart-ul îl oprește. Documentele deja re-procesate au valorile actualizate în DB.

---

## Rotate cheia OpenRouter {#rotate-openrouter-key}

**Când rulezi:** cheia a fost compromisă, OpenRouter a rotit-o, sau OpenRouter returnează `401 {"error":"User not found"}` (vezi [troubleshooting.md](./troubleshooting.md)).

**Sursa de adevăr:** tabelul `settings` din Postgres (NU `.env` — `.env` e doar fallback).

**Pași:**

```bash
NEW_KEY='sk-or-v1-...'

# 1. Update DB (sursa autoritativă)
docker exec -i pdfextractor-postgres psql -U postgres -d pdfextractor -v new_key="$NEW_KEY" <<'SQL'
UPDATE settings SET value = to_jsonb(:'new_key'::text), updated_at = NOW()
  WHERE key = 'openrouter_api_key';
SQL

# 2. Forțează pipeline să re-citească (backend ar fi făcut asta oricum la un UI save)
curl -s -X POST http://localhost:8001/api/pipeline/reload-settings

# 3. Updatează și .env pentru coerență (fallback dev / boot)
# Editează manual: OPENROUTER_API_KEY=sk-or-v1-...
```

**Verifică:**

```bash
# Test direct OpenRouter
curl -s https://openrouter.ai/api/v1/auth/key -H "Authorization: Bearer $NEW_KEY" | head

# Rulează un extraction pe un doc; verifică extraction_model în UI
# — trebuie să aibă prefix `vision:` NU `regex_fallback`
```

**Rollback:** rulează același UPDATE cu cheia veche din password manager. Dacă cheia veche a fost deja invalidă (cazul tipic), alternativa e să setezi temporar `AUTH_DISABLED=true` în dev, sau să reactivezi cheia din dashboard-ul OpenRouter.

---

## Stop / start tunelul Cloudflare {#cloudflare-tunnel}

**Când rulezi:** debug "merge local dar nu merge pe makyol.voostvision.ro", update tunel, sau oprit intenționat (să nu expui app-ul).

**Pași:**

```bash
# Stop — URL-ul public întoarce 502 imediat
# Găsește PID-ul cloudflared (PowerShell):
#   Get-Process cloudflared | Select-Object Id, StartTime
# Apoi:
taskkill //PID <pid> //F

# Start manual (fără reboot)
wscript.exe "C:\Users\meler\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Cloudflared_Makyol.vbs"

# Dezactivează auto-start permanent
# Șterge VBS-ul de mai sus din Startup folder
```

**Verifică:**

```bash
curl -sI https://makyol.voostvision.ro/health
# 200 OK când e live, 502 când nu
```

Alternativ, dashboard: Cloudflare Zero Trust → Networks → Tunnels → `makyol-beta`. Vezi starea edge + conexiunile active.

**Rollback:** `wscript.exe` din nou pe VBS sau reboot (VBS-ul se execută la logon).

---

## Sanity check fill-rate bază de date

**Când rulezi:** după reprocess-all, după schimbare model AI, sau să verifici dacă extracția produce date utile.

**Pași:**

```bash
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor -c "
SELECT
  COUNT(*) FILTER (WHERE material IS NOT NULL AND material <> '')        AS with_material,
  COUNT(*) FILTER (WHERE companie IS NOT NULL AND companie <> '')        AS with_companie,
  COUNT(*) FILTER (WHERE producator IS NOT NULL AND producator <> '')    AS with_producator,
  COUNT(*) FILTER (WHERE data_expirare IS NOT NULL AND data_expirare <> '') AS with_expiry,
  COUNT(*) FILTER (WHERE adresa_producator IS NOT NULL AND adresa_producator <> '') AS with_addr,
  COUNT(*) AS total
FROM extraction_results;
"
```

**Baseline 2026-04-18 post-hardening (328 docs):**

| Câmp | Valoare |
|------|---------|
| `material` | 221 |
| `companie` | 223 |
| `producator` | 196 |
| `data_expirare` | 179 |
| `adresa_producator` | 290 |

Scăderi bruște față de aceste numere indică probabil: cheie OpenRouter invalidă (fallback regex), schimbare model AI inferior, sau migrație care a resetat coloane.

**Rollback:** nu există — raportul e read-only. Dacă fill-rate-ul e scăzut, urmează [troubleshooting.md](./troubleshooting.md) sau rulează `rotate-openrouter-key` și un nou reprocess-all.

---

## Backup + restore Postgres {#backup-restore}

**Când rulezi:** înainte de migrație majoră, înainte de upgrade Postgres, sau periodic (până setăm backup automat).

**Sursa de adevăr:** volume Docker `postgres_data`. NU există backup automat încă — flag de rezolvat înainte de a adăuga mai mulți utilizatori.

**Backup:**

```bash
# Dump gzipped cu timestamp
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker exec pdfextractor-postgres pg_dump -U postgres -F c pdfextractor \
  > "./backups/pdfextractor-${TIMESTAMP}.dump"

# Pentru backup uploads
tar czf "./backups/uploads-${TIMESTAMP}.tar.gz" uploads/
```

**Restore:**

```bash
# Opri backend (previne write-uri în timpul restore)
docker compose stop backend

# Drop + recreate DB
docker exec -i pdfextractor-postgres psql -U postgres <<SQL
DROP DATABASE IF EXISTS pdfextractor;
CREATE DATABASE pdfextractor;
SQL

# Restore din dump
docker exec -i pdfextractor-postgres pg_restore -U postgres -d pdfextractor \
  < "./backups/pdfextractor-20260418-123000.dump"

# Restart backend (migrations rulează idempotent la startup)
docker compose start backend
```

**Verifică:**

```bash
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT COUNT(*) FROM documents; SELECT COUNT(*) FROM users;"
```

**Rollback:** restore cu dump-ul de dinainte (dacă ai făcut unul). Dacă nu — volumele Docker sunt încă pe disc în `postgres_data`; dar DROP DATABASE e ireversibil fără backup.

> **Atenție:** acest proces coboară serviciul 1-5 minute. Pentru schimbări în prod, coordonează cu utilizatorii.

---

## Inițializează default settings în DB

**Când rulezi:** prima instalare (fresh DB), sau ai adăugat o cheie nouă în `DEFAULT_SETTINGS` și vrei să populezi.

**Pași:**

```bash
# Cere token JWT (fie login, fie folosește INTERNAL_API_TOKEN dacă e setat)
curl -s -X POST http://localhost/api/settings/initialize \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

Rezultat: populează orice cheie din `DEFAULT_SETTINGS` care lipsește, returnează numărul creat. Nu suprascrie valorile existente.

**Verifică:**

```bash
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT key, value FROM settings ORDER BY key;"
```

**Rollback:** nu e destructiv — dacă o cheie nu trebuia acolo, `DELETE FROM settings WHERE key = '...'`.

---

## Schimbă modelul AI folosit

**Când rulezi:** experimentezi, OpenRouter deprecizează un model, sau migrezi de la Gemini la Claude.

**Sursa de adevăr:** cheia `ai_model` din `settings` (valori validate contra `VALIDATION_RULES.ai_model.options` în `src/services/settingsService.ts:40-50`).

**Prin UI (recomandat):**
Settings → AI Model → alege din dropdown → Save. Pipeline reîncarcă automat.

**Prin CLI:**

```bash
curl -X PUT http://localhost/api/settings/ai_model \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"value": "anthropic/claude-sonnet-4.5"}'
```

**Verifică:**

```bash
# Confirm pipeline a reîncărcat
curl -s http://localhost:8001/api/pipeline/stats

# Re-procesează un doc de test; verifică `extraction_model` în rezultat
```

**Rollback:** PUT cu modelul anterior. Pentru a testa înainte de commit, păstrează vechiul model notat.

---

## Verify freshness

```bash
# Compose ps arată toate serviciile
docker compose ps | grep -E "postgres|backend|pipeline|frontend"

# Compose logs nu explodează
docker compose logs --tail=5 | head -20

# Endpoint reload-settings există pe pipeline
curl -s -X POST http://localhost:8001/api/pipeline/reload-settings
# trebuie JSON cu `changed` + `current`

# Settings table există cu cheile așteptate
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT key FROM settings ORDER BY key;"
```
