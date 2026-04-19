# CLAUDE.md — Ghid pentru colaboratori AI

Acest fișier e prima lectură pentru orice agent AI care lucrează pe codebase-ul Makyol Automation.

## Unde găsești documentația

Toată documentația proiectului e în [`docs/`](./docs/). Nu există docs dispersate prin cod.

**Citește întâi:** [`docs/index.md`](./docs/index.md) — harta topică, glosarul și secțiunea "Vreau să...".

## Cum alegi doc-ul potrivit pentru task

| Dacă task-ul este... | Citește |
|----------------------|---------|
| O schimbare pe o rută backend | [`docs/backend.md`](./docs/backend.md) + [`docs/api-reference.md`](./docs/api-reference.md) |
| O schimbare în clasificare/extracție | [`docs/pipeline.md`](./docs/pipeline.md) + [`docs/extraction-logic.md`](./docs/extraction-logic.md) |
| O schimbare în UI | [`docs/frontend.md`](./docs/frontend.md) |
| Schemă DB sau migrație nouă | [`docs/database.md`](./docs/database.md) |
| Autentificare / permisiuni | [`docs/auth-and-access.md`](./docs/auth-and-access.md) |
| Env var / setting nou | [`docs/configuration.md`](./docs/configuration.md) |
| Problemă în producție | [`docs/troubleshooting.md`](./docs/troubleshooting.md) + [`docs/runbook.md`](./docs/runbook.md) |
| Deploy / Cloudflare Tunnel / secrete | [`docs/deployment.md`](./docs/deployment.md) |
| "De ce e așa?" | [`docs/adr/`](./docs/adr/) |

## Reguli minime

1. **Nu duplica informații.** Env vars sunt doar în `docs/configuration.md` + `.env.example`. Alte docs fac link, nu copiază.
2. **Ancore `path:line`.** Când referi cod, scrie `src/index.ts:115`, nu "fișierul de bootstrap".
3. **Verifică înainte să scrii.** Docs cu `last_verified` mai vechi de 30 zile și `stability: runbook` — re-confirmă claim-urile rulând comenzile din secțiunea `## Verify freshness`.
4. **Limba.** Proză română, cod/comenzi/identificatori în engleză (nu traduce `certified_company`).
5. **Fără fișiere ciornă.** Nu crea docs temporare sau note de sesiune în `docs/` — folosește notițe interne sau TaskCreate.

## Când adaugi un doc nou

Copiază [`docs/_template.md`](./docs/_template.md), completează frontmatter-ul, adaugă intrarea în [`docs/index.md`](./docs/index.md). Reguli complete în [`docs/CONTRIBUTING-DOCS.md`](./docs/CONTRIBUTING-DOCS.md).

## Ce NU face

- Nu recrea documentația MVP veche din [`docs/archive/`](./docs/archive/) — acel sistem nu mai există.
- Nu hardcoda URL-uri de producție (`makyol.voostvision.ro`) în docs de arhitectură. URL-ul trăiește doar în `docs/deployment.md`.
- Nu comite secrete. Secretele stau în `.env` (gitignored) și în tabelul `settings` din Postgres.
