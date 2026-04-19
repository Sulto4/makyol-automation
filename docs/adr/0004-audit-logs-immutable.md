---
status: accepted
date: 2026-04-11
supersedes: —
---

# ADR 0004 — Audit logs strict immutable (SQL RULES + cod)

## Context

Sistemul e folosit pentru documente de conformitate — un audit trail trebuie să fie **demonstrabil neintervenit**. O implementare doar la nivel de aplicație (metode `.create()` fără `.update()`/`.delete()` în model) poate fi ocolită:
- Shell direct în DB (ex: `docker exec psql`)
- Utilizator cu acces DB dar nu la cod (DBA extern)
- Bug într-un controller care face UPDATE "din greșeală" pe un log

Alternative considerate:
1. **Doar cod immutable (fără DB constraint).** Vulnerabil la ocolire.
2. **Hash chain (Merkle).** Cryptographic proof dar complex — over-engineering pentru scara actuală.
3. **Log separat, write-only (Syslog, CloudWatch, etc.).** Dependență de sistem extern, cost.
4. **Postgres RULES `DO INSTEAD NOTHING` pentru UPDATE + DELETE.** Blocaj la nivel DB, orice acces (aplicație, shell, ORM) nu poate modifica.

## Decizie

**Dublă apărare:** RULES SQL la DB + metode lipsă în model.

**La nivel SQL** (migration 003):

```sql
migrations/003_create_audit_logs_table.sql:70-73

CREATE RULE audit_logs_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE audit_logs_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;
```

Un UPDATE / DELETE devine NO-OP **fără eroare**. Liniște silențioasă — cine încearcă crede că a funcționat, dar tabelul e neschimbat. Asta e voit: nu vrem să semnalizăm că există protecție (ar putea ajuta atacatori să caute bypass).

**La nivel de cod** (`src/models/AuditLog.ts`):
- `AuditLogModel` expune `create`, `findById`, `findByEntity`, `findByUser`, `findAll`, `count`
- **NU** expune `update` sau `delete`
- Comentariul din cod: "This model does NOT include update() or delete() methods as audit logs are immutable per system requirements"

**Acceptare eșec audit:** dacă `audit_logs.create()` pică (DB down, network), `auditService` prinde eroarea și log-uiește un warning — **rutele business continuă**. Trade-off: silent log drop posibil, dar preferăm să servim request-uri decât să 500-uim user-ul pentru o problemă audit tranzientă.

## Consecințe

**Pozitive:**
- Audit trail provably immutable — demonstrabil în audit extern
- Imposibil să modifici un log accidental în cod
- Compatibil cu eventuală export / legal discovery fără îngrijorări de tampering
- Indexuri GIN pe `before_value`, `after_value`, `metadata` permit query rapid

**Negative:**
- **Nu poți corecta typoes sau loguri greșite.** Un log cu `action_type` setat greșit rămâne pe veci. Compromisul: dacă trebuie corectat, creează un log nou cu `reason: "corrects log #NNN"`.
- **Silent log drop la eșec DB** = zero vizibilitate asupra pierderii. Monitorizare: filtru pe warn-uri `Failed to create audit log`.
- RULES vs trigger — `DO INSTEAD NOTHING` e mai rapid decât un trigger dar mai puțin flexibil. Nu putem log-ui tentativa de DELETE într-un alt tabel.

## Cost de reversare

**Luni (sau ireversibil pentru garanții trecute).**

- Drop RULES = 2 SQL statement-uri
- Adăugare metode în model = câteva ore cod + teste
- **Dar:** garanția de immutability pentru log-urile existente se pierde în momentul drop. Un audit care a cerut "dovedește că niciun log n-a fost modificat din ianuarie 2026 până acum" devine nedemonstrabil.

## Referințe

- [architecture.md#audit-log-immutable](../architecture.md#audit-log-immutable)
- [database.md#audit_logs-migration-003-cu-rules-de-immutability](../database.md#audit_logs-migration-003-cu-rules-de-immutability)
- `src/models/AuditLog.ts` (comentariu clasă)
