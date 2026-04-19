---
status: accepted
date: 2026-04-16
supersedes: —
---

# ADR 0002 — Flag `AUTH_DISABLED` pentru bypass complet

## Context

După adăugarea JWT auth (migration 010 + middleware), dev loop-ul a devenit greoi:
- Fiecare test E2E trebuie să facă login înainte să atingă rutele protejate
- Dev local pe frontend fără backend real — Storybook-uri și probe de UI nu aveau token
- Un coleg care pornește prima oară aplicația trebuie să facă `REGISTER_ENABLED=true` → register → copy token → configurează frontend → restart

Alternative considerate:
1. **Stub-uiește auth în teste.** Necesită mocks peste tot modelul Auth + middleware.
2. **Mod "guest" permanent.** Prea apropiat de producție — periculos.
3. **Flag env care dezactivează auth complet în dev.** Simplu, explicit, imposibil de activat accidental în prod dacă urmezi practici.

## Decizie

Env var `AUTH_DISABLED=true` sare peste middleware-ul de autentificare pentru **toate** rutele protejate.

```
src/index.ts:115-121
const authDisabled = process.env.AUTH_DISABLED === 'true';
if (authDisabled) {
  logger.warn('AUTH_DISABLED=true — authentication bypassed on all routes. DO NOT USE IN PRODUCTION.');
}
const authGuard = authDisabled
  ? (_req: any, _res: any, next: any) => next()
  : requireAuth;
```

În frontend există paralelul `VITE_AUTH_DISABLED=true` care sare peste `ProtectedRoute`.

**Protecții contra accident:**
- Log warn explicit la fiecare startup cu flag-ul activat
- `docker-compose.yml:54` are default `${AUTH_DISABLED:-false}`
- Compose enforceaza `JWT_SECRET:?...` required — dacă e prod și lipsește secret-ul, container-ul pică; asta forțează un JWT_SECRET real, implicând un dev conscient

## Consecințe

**Pozitive:**
- Dev loop rapid — Postman/curl fără pași de auth
- Teste E2E pot targeta rute direct
- Tourist mode pe UI local (un coleg nou vede imediat aplicația fără să configureze nimic)

**Negative:**
- **Catastrofic dacă activat în producție.** Efectiv removes toate check-urile de autorizație — orice rută, inclusiv admin, devine deschisă.
- Când se setează un default-prost (ex: .env lăsat cu AUTH_DISABLED=true), e greu de observat până nu verifici log-urile
- Reduce acoperirea testelor reale de auth — testele scrise cu flag activat nu acoperă JWT flow

**Mitigări:**
- DEPLOYMENT_NOTES-20260418.md hardening checklist verifică explicit `AUTH_DISABLED=false` în prod
- Log warn la startup e loud
- Logica middleware e izolată — e clar unde e bypass-ul dacă cineva caută

## Cost de reversare

**Imediat.** Scoatere flag = 2-line edit în `src/index.ts`. Testele care depindeau de el trebuie refactorizate să facă login real — câteva ore de muncă per suită de teste.

## Referințe

- [auth-and-access.md#feature-flags-de-auth](../auth-and-access.md#feature-flags-de-auth)
- [configuration.md](../configuration.md) — tabelul env vars
- [deployment.md#hardening-checklist-beta-închis](../deployment.md#hardening-checklist-beta-închis)
