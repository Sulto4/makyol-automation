---
status: accepted
date: 2026-04-16
supersedes: —
---

# ADR 0003 — Settings autoritative în DB, `.env` doar fallback

## Context

Unele settings trebuie schimbate des, fără restart:
- `ai_model` — experimentăm cu modele OpenRouter (Gemini, Claude, GPT)
- `ai_temperature` — tuning
- `openrouter_api_key` — rotire urgentă la compromis
- `vision_max_pages` — tuning per tip de document
- `batch_concurrency` — scalare

Env vars nu se pretează — sunt baked la startup container. Un restart costă ~30s downtime + log noise.

Alternative considerate:
1. **Restart container la fiecare setting change.** Simplu dar friction mare + downtime la fiecare click Save.
2. **Configuration server separat (Consul, etcd).** Over-engineering pentru 6 chei.
3. **Fișier config montat ca volume, re-read pe SIGUSR1.** Funcționează dar nu are audit trail și UI.
4. **Tabel Postgres + API + hot-reload endpoint.** Folosește infrastructura existentă, se integrează cu audit log, UI direct pe DB.

## Decizie

**Sursa de adevăr pentru settings editable = tabelul `settings` din Postgres.** `.env` e doar **fallback de boot** când pipeline-ul pornește înainte ca backend-ul să fie ready (retries, apoi pică pe env).

**Fluxul:**

```
UI Settings → PUT /api/settings/:key
             └─► UPSERT settings + audit log
             └─► POST /api/pipeline/reload-settings (fire-and-forget, 5s timeout)
                  └─► pipeline GET /api/settings (cu INTERNAL_API_TOKEN)
                       └─► settings._apply_from_api_cache()
```

Cod:
- Definiție model + defaults: `src/services/settingsService.ts:9-15`
- Validări: `src/services/settingsService.ts:28-76`
- Pipeline fetch + reload: `pipeline/config.py:31-242`
- Hot-reload endpoint: `pipeline/api.py:118-132`

## Consecințe

**Pozitive:**
- Schimbare model AI din UI → efect în 1-2 secunde fără restart
- Audit log pentru fiecare change (`CONFIG_CHANGE` action type) — cine, când, ce valoare veche/nouă
- Validări centralizate în TS (ex: `ai_model` ∈ listă de 9 Vision-capable)
- Rotire cheie OpenRouter = 1 SQL + 1 curl, fără restart

**Negative:**
- **Două surse posibile pentru aceeași valoare** (DB + `.env`). Dacă nu clarificăm explicit care e autoritativă, utilizatorii schimbă `.env` și se plâng că "nu merge". Documentat explicit în [configuration.md#tabel-settings-db-autoritativ](../configuration.md#tabel-settings-db-autoritativ).
- Startup ordering — pipeline-ul pornește cu settings din DB; dacă DB-ul nu e încă up, cade pe `.env`, apoi pe hardcodate. Retry logic în `pipeline/config.py:31-76` (5 attempts × 2s) ameliorează dar nu elimină edge case-uri.
- Hot-reload e fire-and-forget (vezi [architecture.md#settings-hot-reload](../architecture.md#settings-hot-reload)) — dacă pipeline e jos temporar, update-ul UI reușește dar efectul apare la următoarea convergence.

## Cost de reversare

**Săptămâni.** Refactor-area ar însemna: mutare setting-uri înapoi în `.env`, restart pipeline la fiecare change, redesign UI Settings ca notă "restart needed". Undo-ul distruge audit trail-ul și UX-ul de rotire urgentă. Practic, ne-am legat de această decizie.

## Referințe

- [configuration.md](../configuration.md)
- [architecture.md#settings-hot-reload](../architecture.md#settings-hot-reload)
- [runbook.md#rotate-openrouter-key](../runbook.md#rotate-openrouter-key)
