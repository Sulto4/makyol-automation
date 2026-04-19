---
title: Index documentație Makyol Automation
scope: docs-index
stability: living
last_verified: 2026-04-19
related:
  - ../README.md
  - ../CLAUDE.md
---

# Documentația Makyol Automation

Hartă centrală a documentației. Fiecare intrare spune ce acoperă doc-ul și marchează stabilitatea lui (cât de des se schimbă).

## Harta doc-urilor

| Doc | Scop | Stabilitate | Status |
|-----|------|-------------|--------|
| [architecture.md](./architecture.md) | Diagrama 4-service, request path, trust boundaries | stable | ✅ |
| [backend.md](./backend.md) | Structura `src/`, rute, middleware, modele | living | ✅ |
| [pipeline.md](./pipeline.md) | Structura `pipeline/`, FastAPI, flow-uri | living | ✅ |
| [frontend.md](./frontend.md) | `frontend/src/`, routing, Zustand, React Query | living | ✅ |
| [database.md](./database.md) | Schema tabele, migration ledger, owner isolation | stable | ✅ |
| [api-reference.md](./api-reference.md) | Tabel complet rute HTTP backend + pipeline | living | ✅ |
| [configuration.md](./configuration.md) | Env vars + chei `settings` table | living | ✅ |
| [auth-and-access.md](./auth-and-access.md) | JWT, `INTERNAL_API_TOKEN`, admin flow | stable | ✅ |
| [extraction-logic.md](./extraction-logic.md) | Clasificare cascade, Vision, G4/G5, KB | stable | ✅ |
| [runbook.md](./runbook.md) | Proceduri ops (seed admin, rotate key, backup) | runbook | ✅ |
| [deployment.md](./deployment.md) | Topologie producție, Cloudflare Tunnel, VBS | runbook | ✅ |
| [troubleshooting.md](./troubleshooting.md) | Simptom → cauză → fix | runbook | ✅ |
| [development.md](./development.md) | Dev loop local, teste, cum adaugi o rută | living | ✅ |
| [adr/](./adr/) | Decizii arhitecturale cu motivație | stable | ✅ (5 ADRs) |
| [archive/](./archive/) | Docs învechite (MVP pre-hardening) | — | ✅ |

### ADR-uri (decizii arhitecturale)

| ADR | Decizie | Status |
|-----|---------|--------|
| [0001](./adr/0001-vision-unconditional.md) | Vision AI aplicat necondiționat la fiecare document | accepted |
| [0002](./adr/0002-auth-disabled-flag.md) | Flag `AUTH_DISABLED` pentru bypass dev | accepted |
| [0003](./adr/0003-settings-db-authoritative.md) | Settings autoritative în DB, `.env` doar fallback | accepted |
| [0004](./adr/0004-audit-logs-immutable.md) | Audit logs strict immutable (SQL RULES + cod) | accepted |
| [0005](./adr/0005-internal-api-token.md) | `INTERNAL_API_TOKEN` shared secret pentru pipeline → backend | accepted |

**Legendă stabilitate:**
- `stable` — adevăr arhitectural, se schimbă rar (odată cu arhitectura)
- `living` — urmărește codul, se schimbă cu codul
- `runbook` — stare operațională, se schimbă cu environment-ul

## "Vreau să..."

| Vreau să... | Citește |
|-------------|---------|
| Adaug o rută nouă în backend | [backend.md](./backend.md) + [api-reference.md](./api-reference.md) + [database.md](./database.md) (dacă tabel nou) |
| Adaug o categorie nouă de document | [extraction-logic.md](./extraction-logic.md) + [pipeline.md](./pipeline.md#EXTRACTION_SCHEMA) |
| Schimb modelul AI folosit | UI Settings → cheia `ai_model` (vezi [configuration.md](./configuration.md#settings-table)) |
| Rotesc cheia OpenRouter | [runbook.md](./runbook.md#rotate-openrouter-key) |
| Creez un admin nou | [runbook.md](./runbook.md#seed-admin) |
| Debug "pipeline nu primește setări noi" | [troubleshooting.md](./troubleshooting.md) → caută "INTERNAL_API_TOKEN" |
| Debug "câmpuri goale în tabel" | [troubleshooting.md](./troubleshooting.md) → "rate limit burst" |
| Setez mediul de dezvoltare | [development.md](./development.md) + [configuration.md](./configuration.md) |
| Pornesc/opresc tunelul Cloudflare | [runbook.md](./runbook.md#cloudflare-tunnel) |
| Fac backup la baza de date | [runbook.md](./runbook.md#backup-restore) |
| Operez pe host Mac Mini (macOS) | [runbook.md](./runbook.md#host-mac-mini) + [deployment.md](./deployment.md#deployment-on-macos-mac-mini-production-host) |
| Adaug un doc nou | [CONTRIBUTING-DOCS.md](./CONTRIBUTING-DOCS.md) + copiază [\_template.md](./_template.md) |

## Glosar

**Makyol** — compania turcă de construcții pentru care sistemul extrage date din PDF-uri de conformitate. Lucrează pe o autostradă din România.

**Pachet** — grupare logică de PDF-uri pentru un material/furnizor, folosită la export Excel (un "pachet" = un rând în Excel-ul final cu hyperlinks la PDF-uri).

**Categorie** — una din cele 14 clase de document recunoscute: `ISO`, `CE`, `FISA_TEHNICA`, `AGREMENT`, `AVIZ_TEHNIC`, `AVIZ_SANITAR`, `DECLARATIE_CONFORMITATE`, `CERTIFICAT_CALITATE`, `AUTORIZATIE_DISTRIBUTIE`, `CUI`, `CERTIFICAT_GARANTIE`, `DECLARATIE_PERFORMANTA`, `AVIZ_TEHNIC_SI_AGREMENT`, `ALTELE`. Vezi [extraction-logic.md](./extraction-logic.md).

**ALTELE** — categoria "nu știu" / "nu se încadrează". Semnalul că clasificarea nu a avut destulă încredere.

**`review_status`** — câmpul care marchează dacă un document necesită revizuire umană. Valori: `OK`, `REVIEW` (din G5 suspicious-expiry), `NEEDS_CHECK` (toate câmpurile extrase sunt null), `FAILED`.

**OwnerFilter** — pattern prin care rutele de documente filtrează după `owner_user_id` la nivelul modelului (nu middleware). Admin vede tot; utilizator regulat vede doar documentele proprii. Implementat în `src/models/Document.ts`.

**G4** — fallback: dacă AI nu returnează `data_expirare` dar filename conține `DD.MM.YYYY`, folosește ultima dată candidată din filename. Cod: `pipeline/__init__.py`.

**G5** — guard: dacă `data_expirare` e >180 zile în trecut ȘI filename nu corroborează, marchează `review_status = "REVIEW"` (deseori e o dată de emitere citită greșit ca dată de expirare). Cod: `pipeline/__init__.py:46`.

**Vision AI unconditional** — `_USE_VISION_FOR_ALL = True` în `pipeline/__init__.py:29`. Fiecare document, indiferent de calitatea textului extras, e randat la 300 DPI și trimis la Gemini 2.5 Flash via OpenRouter. Extracția text rămâne ca fallback când Vision returnează None.

**`INTERNAL_API_TOKEN`** — secret partajat între backend și pipeline (≥16 caractere), trimis ca `Authorization: Bearer` în apeluri pipeline→backend (`GET /api/settings`). Fără el, reload-ul de setări din pipeline primește 401. Implementat în `src/middleware/authMiddleware.ts:52`.

**Knowledge base (KB)** — `pipeline/schemas/knowledge_base.json`: alias-uri și CUI-uri pentru companii cunoscute (TERAPLAST, VALROM, REHAU, etc.). Fuzzy match cu `rapidfuzz.WRatio ≥ 92`.

**SRAC, RENAR, ACAR, ARS** — organisme românești de certificare (SRAC: Societatea Română de Asigurare a Calității; RENAR: Asociația de Acreditare; etc.). Apar ca `issuing_organization` în rezultatele de extracție.

**Reprocess-all** — endpoint `POST /api/documents/reprocess-all` care re-rulează pipeline-ul pe documente existente. Concurență limitată de setarea `batch_concurrency` (clamped `[1..10]`), citită la fiecare apel.

**Settings hot-reload** — backend-ul apelează `POST /api/pipeline/reload-settings` fire-and-forget (5s timeout, erori înghițite) după fiecare upsert din `/api/settings/:key`. Pipeline re-citește din backend. Vezi [configuration.md](./configuration.md#hot-reload).

**Host producție** — Mac Mini (macOS), runtime Docker: OrbStack. Istoric: prima desfășurare live 2026-04-18 pe PC Windows + Docker Desktop, migrată ulterior pe Mac Mini pentru uptime always-on. Ambele variante descrise în [deployment.md](./deployment.md).

## Convenții de contribuție

- Fiecare doc începe cu frontmatter YAML (vezi [_template.md](./_template.md)).
- Fiecare doc are o secțiune finală `## Verify freshness` cu comenzi grep/ls care re-confirmă claim-urile.
- Ancore `path:line` pentru toate referințele la cod. Ex: `src/index.ts:115`.
- Docs `stability: runbook` au `last_verified` actualizat la fiecare modificare.

Pentru reguli complete: [CONTRIBUTING-DOCS.md](./CONTRIBUTING-DOCS.md).

## Verify freshness

```bash
# Toate doc-urile principale
ls docs/index.md docs/architecture.md docs/configuration.md docs/api-reference.md \
   docs/runbook.md docs/_template.md docs/CONTRIBUTING-DOCS.md \
   docs/backend.md docs/pipeline.md docs/frontend.md docs/database.md \
   docs/auth-and-access.md docs/extraction-logic.md docs/deployment.md \
   docs/troubleshooting.md docs/development.md

# 5 ADR-uri + template
ls docs/adr/_template.md docs/adr/0001-*.md docs/adr/0002-*.md \
   docs/adr/0003-*.md docs/adr/0004-*.md docs/adr/0005-*.md

# Arhivele conțin docs MVP + snapshot DEPLOYMENT_NOTES
ls docs/archive/README-mvp.md docs/archive/API-mvp.md docs/archive/SETUP-mvp.md \
   docs/archive/VERIFICATION_SUMMARY.md docs/archive/verification_results.md \
   docs/archive/DEPLOYMENT_NOTES-20260418.md

# DEPLOYMENT_NOTES.md NU trebuie să mai fie în docs/ (a fost split)
test ! -f docs/DEPLOYMENT_NOTES.md && echo "OK: split complet"

# Fiecare doc are frontmatter YAML
for f in docs/*.md docs/adr/*.md; do
  head -1 "$f" | grep -q "^---$" || echo "MISSING FRONTMATTER: $f"
done
```
