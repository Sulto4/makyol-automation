# Makyol Automation

Sistem de clasificare și extracție automată pentru PDF-uri de conformitate în construcții (ISO, CE, Agremente, Fișe tehnice, etc.) folosit pe un șantier de autostradă din România de către compania turcă **Makyol**.

**Live:** https://makyol.voostvision.ro (beta închis — cont creat de administrator)

## Stack

| Serviciu | Tehnologie | Port | Rol |
|----------|-----------|------|-----|
| `postgres` | PostgreSQL 15 | 5432 | Date + audit logs (immutable) |
| `backend` | Node/TypeScript/Express | 3000 (intern) | Auth JWT, rute API, orchestrare |
| `pipeline` | Python/FastAPI | 8001 | Clasificare + Vision AI (Gemini 2.5 Flash via OpenRouter) |
| `frontend` | React + Vite + Tailwind | 80 (prin nginx) | UI în română |

Totul orchestrat prin `docker-compose.yml`; în producție în spatele unui Cloudflare Tunnel.

## Quickstart (dev local)

```bash
cp .env.example .env
# Editează .env — în principal JWT_SECRET + OPENROUTER_API_KEY
docker compose up -d --build
# → http://localhost (nginx) · http://localhost:8001/api/pipeline/health (pipeline)
```

Crearea primului admin: vezi [`docs/runbook.md#seed-admin`](./docs/runbook.md#seed-admin).

## Documentație

Toată documentația este în [`docs/`](./docs/). Punctul de intrare este [`docs/index.md`](./docs/index.md).

**Cele mai utile documente:**
- [`docs/architecture.md`](./docs/architecture.md) — schema celor 4 servicii și fluxul unei cereri
- [`docs/api-reference.md`](./docs/api-reference.md) — toate rutele HTTP
- [`docs/configuration.md`](./docs/configuration.md) — env vars + chei `settings` table
- [`docs/runbook.md`](./docs/runbook.md) — proceduri de ops (seed admin, rotate key, etc.)
- [`docs/troubleshooting.md`](./docs/troubleshooting.md) — simptom → cauză → fix

Pentru colaboratori AI vezi [`CLAUDE.md`](./CLAUDE.md).

## Licență

ISC
