---
title: Database (schema + migrații + izolare)
scope: database
stability: stable
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./backend.md
  - ./auth-and-access.md
code_refs:
  - migrations
  - src/models
---

# Database

Postgres 15 (Alpine) cu 5 tabele principale. Acest doc descrie schema, regulile de izolare per-utilizator și ordinea migrațiilor. Pentru comportament cross-service vezi [architecture.md](./architecture.md).

## Tabele

| Tabel | Scop | PK | Owner scoping |
|-------|------|----|--------------:|
| `documents` | Metadata PDF-uri încărcate + status procesare | `id SERIAL` | `owner_user_id UUID` |
| `extraction_results` | Rezultate extracție (text + JSONB metadata + câmpuri normalizate) | `id SERIAL` | `owner_user_id UUID` |
| `audit_logs` | Istoric immutable al acțiunilor | `id SERIAL` | n/a (are `user_id`) |
| `users` | Conturi utilizatori + JWT auth | `id UUID` | n/a |
| `settings` | Config key-value cu JSONB | `key VARCHAR` | n/a (global) |

Toate tabelele au triggeri `update_updated_at_column()` (definit în migration 001) pentru auto-refresh pe `updated_at`.

### `documents` (migration 001 + cols adăugate ulterior)

| Coloană | Tip | Constraint | Sursă |
|---------|-----|------------|-------|
| `id` | SERIAL | PK | 001 |
| `filename` | VARCHAR(255) | NOT NULL | 001 |
| `original_filename` | VARCHAR(255) | NOT NULL | 001 |
| `file_path` | TEXT | NOT NULL | 001 |
| `file_size` | INTEGER | CHECK > 0 | 001 |
| `mime_type` | VARCHAR(100) | default `application/pdf` | 001 |
| `processing_status` | VARCHAR(50) | CHECK ∈ {pending, processing, completed, failed} | 001 |
| `error_message` | TEXT | nullable | 001 |
| `uploaded_at` / `processing_started_at` / `processing_completed_at` | TIMESTAMPTZ | audit timestamps | 001 |
| `categorie` | VARCHAR | — (una din 14 categorii) | 003 |
| `confidence` | DECIMAL | — | 003 |
| `metoda_clasificare` | VARCHAR | CHECK ∈ {filename_regex, text_rules, ai, text_override, vision, filename+text_agree, filename_wins, fallback} | 003 + 006 |
| `relative_path` | TEXT | pentru export ZIP structură folder | 007 |
| `human_review_method` | VARCHAR | din migration 008 | 008 |
| `owner_user_id` | UUID | FK users(id); backfilled la prima admin | 011 + 014 |
| `page_count` | INTEGER | — | 015 |

**Indexuri:** `processing_status`, `uploaded_at DESC`, `filename`.

### `extraction_results` (migration 002 + cols)

| Coloană | Tip | Sursă |
|---------|-----|-------|
| `id` | SERIAL PK | 002 |
| `document_id` | INTEGER FK `documents(id)` ON DELETE CASCADE + UNIQUE | 002 |
| `extracted_text` | TEXT | 002 |
| `metadata` | JSONB default `'{}'` | 002 |
| `confidence_score` | DECIMAL(3,2) | CHECK [0,1] — 002 |
| `extraction_status` | VARCHAR(50) | CHECK ∈ {pending, success, partial, failed} — 002 |
| `error_details` | JSONB | 002 |
| `material`, `companie`, `producator`, `distribuitor`, `adresa_producator`, `data_expirare`, `extraction_model`, `nume_document`, etc. | VARCHAR/TEXT | adăugate progresiv |
| `adresa_distribuitor` | TEXT | 005 |
| `owner_user_id` | UUID FK users(id) | 012 + 014 |

**Indexuri:** `document_id`, `extraction_status`, `created_at DESC`, **GIN pe `metadata`** (pentru query JSONB).

### `audit_logs` (migration 003, cu RULES de immutability)

| Coloană | Tip | Notă |
|---------|-----|------|
| `id` | SERIAL PK | |
| `timestamp` | TIMESTAMPTZ | data acțiunii |
| `user_id` | — | VARCHAR(255) la creare; mutat la UUID FK users(id) prin 013 |
| `action_type` | VARCHAR(100) | CHECK enum (vezi mai jos) |
| `entity_type` | VARCHAR(100) | CHECK ∈ {document, extraction_result, compliance_check, report, user, config} |
| `entity_id` | INTEGER | nullable |
| `before_value`, `after_value`, `metadata` | JSONB | state pre/post + context |
| `created_at` | TIMESTAMPTZ | |

**Action types** (în cod la `src/models/AuditLog.ts:6-15`):
`document_upload`, `document_status_change`, `document_delete`, `document_review`, `compliance_check_execution`, `report_generation`, `user_login`, `config_change`. `document_review` adăugat prin migration 009.

**Indexuri:** `timestamp DESC`, `created_at DESC`, `user_id`, `action_type`, `entity_type`, `entity_id`, compozit `(user_id, action_type)` + `(entity_type, entity_id)`, plus **GIN** pe `before_value`, `after_value`, `metadata`.

**Immutable la nivel SQL** (migration 003 L70, L73):
```sql
CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```
Un UPDATE sau DELETE devine NO-OP fără eroare. În plus, `AuditLogModel` în `src/models/AuditLog.ts` nu expune metode `update`/`delete` — dublă apărare.

> **De ce immutable la nivel SQL:** codul aplicație poate fi ocolit (shell-uri directe în DB). RULE-urile Postgres fac imposibil accidental de a muta un log — și mult mai greu de făcut intenționat.

### `users` (migration 010)

| Coloană | Tip | Notă |
|---------|-----|------|
| `id` | UUID | PK, default `gen_random_uuid()` (extensia `pgcrypto`) |
| `email` | CITEXT | UNIQUE, NOT NULL; case-insensitive matching (extensia `citext`) |
| `password_hash` | TEXT | bcrypt hash (10 rounds) |
| `is_admin` | BOOLEAN | default false; **primul user înregistrat auto-becomes admin** (logica în `authService.ts`) |
| `is_active` | BOOLEAN | default true; `PATCH /admin/users/:id/active` flip |
| `created_at`, `updated_at`, `last_login_at` | TIMESTAMPTZ | `touchLastLogin` la login |

**Indexuri:** `email`, `created_at DESC`.

**Extensii necesare:** `pgcrypto` (UUID gen) + `citext` (email case-insensitive).

### `settings` (migration 004)

| Coloană | Tip |
|---------|-----|
| `key` | VARCHAR PK |
| `value` | JSONB (orice tip serializabil) |
| `created_at`, `updated_at` | TIMESTAMPTZ |

Vezi [configuration.md#tabel-settings-db-autoritativ](./configuration.md#tabel-settings-db-autoritativ) pentru chei cunoscute.

## FK graph

```
users.id (UUID)
  ├──< documents.owner_user_id
  ├──< extraction_results.owner_user_id
  └──< audit_logs.user_id  (după migration 013)

documents.id (SERIAL)
  └──< extraction_results.document_id  (ON DELETE CASCADE + UNIQUE)
```

- Șterg un user → documentele lui **NU** se șterg cascade (`owner_user_id` e nullable post-backfill). În practică user-ii nu se șterg, doar `is_active=false`.
- Șterg un document → `extraction_results` se șterge CASCADE.

## Migration ledger

Aplicate în ordine alfabetică de `runMigrations` la fiecare startup (`src/index.ts:22-54`). Idempotent prin `IF NOT EXISTS` + catch "already exists".

| # | Fișier | Scop | Data |
|---|--------|------|------|
| 001 | `001_create_documents_table.sql` | Tabel documents + triggers + indexuri | 2026-04-10 |
| 002 | `002_create_extraction_results_table.sql` | Tabel extraction_results + GIN metadata | 2026-04-10 |
| 003 | `003_add_classification_extraction_columns.sql` | Adaugă `categorie`, `confidence`, `metoda_clasificare` la documents | — |
| 003* | `003_create_audit_logs_table.sql` | Tabel audit_logs + RULES immutable + indexuri + GIN | 2026-04-11 |
| 004 | `004_create_settings_table.sql` | Tabel settings (key JSONB) | — |
| 005 | `005_add_adresa_distribuitor.sql` | Coloană `adresa_distribuitor` în extraction_results | — |
| 006 | `006_update_metoda_clasificare_constraint.sql` | Update CHECK enum pentru `metoda_clasificare` | — |
| 007 | `007_add_relative_path.sql` | Coloană `relative_path` pentru export ZIP | — |
| 008 | `008_add_human_review_method.sql` | Coloană `human_review_method` | — |
| 009 | `009_add_document_review_action_type.sql` | Adaugă `document_review` la CHECK `action_type` audit_logs | — |
| 010 | `010_create_users_table.sql` | Tabel users (UUID + CITEXT) | 2026-04-16 |
| 011 | `011_add_owner_to_documents.sql` | Coloană `owner_user_id` în documents + FK | — |
| 012 | `012_add_owner_to_extraction_results.sql` | Coloană `owner_user_id` în extraction_results | — |
| 013 | `013_alter_audit_logs_user_id.sql` | `user_id` VARCHAR → UUID FK users(id) | — |
| 014 | `014_backfill_existing_documents.sql` | Populează `owner_user_id` pentru docs vechi cu primul admin | — |
| 015 | `015_add_page_count_to_documents.sql` | Coloană `page_count` | — |

> **Atenție numerotare duplicată:** există `003_add_classification_extraction_columns.sql` **ȘI** `003_create_audit_logs_table.sql`. Rulează în ordine alfabetică deterministă (sort). Recomandare implicită: pentru migrații noi folosește prefix 016+.

## OwnerFilter pattern

Toate SELECT/UPDATE/DELETE pentru `documents` și `extraction_results` primesc un argument `owner: string | null`:

- **`string` UUID** → query-ul adaugă `AND owner_user_id = $N`. Pasat din controller: `req.user.id` pentru user regulat.
- **`null`** → query fără filtrare. Pasat când: `req.user.is_admin === true`, sau caller-ul e pipeline (cu `INTERNAL_API_TOKEN`).

Exemplu concret în `src/models/Document.ts::findById(id, owner)`:
```typescript
let query = 'SELECT * FROM documents WHERE id = $1';
const values: any[] = [id];
if (owner !== null) {
  query += ' AND owner_user_id = $2';
  values.push(owner);
}
```

> **De ce la nivel de model și nu middleware:** un middleware care adaugă filtrul poate fi omis accidental pe o rută nouă, breach silent. Modelul cere explicit argument `owner` — omiterea e eroare TypeScript, nu bug latent.

## Audit trail: ce se loghează

Fiecare write pe entitate → un `audit_logs.create()` cu:
- `user_id` = caller-ul (sau null pentru sistem)
- `action_type` din enum
- `entity_type` din enum
- `entity_id` PK-ul entității
- `before_value` + `after_value` (JSONB cu starea)
- `metadata` cu context (IP, user-agent, etc. dacă e relevant)

Eșecul audit-ului nu blochează rutele business — e log.warn + continue (risk: log drop silent). Tradeoff acceptat: preferăm să serverm request-ul decât să 500-uim un user pe o problemă audit temporară.

## Backup + restore

Volumul Postgres e named (`postgres_data` în `docker-compose.yml:139`). NU e backup automat. Manual cu `pg_dump`. Vezi [runbook.md#backup-restore](./runbook.md#backup-restore).

## Verify freshness

```bash
# 16 fișiere migrație (15 numerotate + 2 × 003)
ls migrations/*.sql | wc -l
# trebuie 16

# 5 tabele principale
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
# trebuie: audit_logs, documents, extraction_results, settings, users

# RULES de immutability pe audit_logs
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT rulename FROM pg_rules WHERE tablename='audit_logs';"
# trebuie: audit_logs_no_update, audit_logs_no_delete

# Extensii pgcrypto + citext
docker exec pdfextractor-postgres psql -U postgres -d pdfextractor \
  -c "SELECT extname FROM pg_extension WHERE extname IN ('pgcrypto', 'citext');"

# AuditLogModel nu are update/delete
grep -E "^\s+(async\s+)?(update|delete)\(" src/models/AuditLog.ts
# NU trebuie match (sau doar findBy-ul, nu metode de modificare)
```
