---
title: Auth & Access Control
scope: auth
stability: stable
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./api-reference.md
  - ./backend.md
  - ./configuration.md
code_refs:
  - src/services/authService.ts
  - src/middleware/authMiddleware.ts
  - src/middleware/rateLimiter.ts
  - src/routes/auth.ts
  - src/routes/adminUsers.ts
  - migrations/010_create_users_table.sql
---

# Auth & Access Control

Modelul de autentificare și autorizare: JWT-based, bcrypt hashing, rate-limited, cu bypass pentru dev și secret partajat pentru comunicarea backend ↔ pipeline. Acest doc acoperă mecanica. Pentru rute concrete vezi [api-reference.md](./api-reference.md).

## Principii

- **Un singur gate:** login JWT la `/api/auth/login`. Nu există Cloudflare Access overlay.
- **Prima înregistrare = admin.** User-ul cu `COUNT(*) = 0` la `users` devine automat admin. Toți ceilalți vin regular (toggle-abili ulterior de admin).
- **Owner-scoped default.** Rutele de documents filtrează pe `req.user.id`. Admin vede tot.
- **Immutable audit.** Fiecare acțiune auth (login, create user, config change) → `audit_logs.create()`.

## JWT signing + verify

`src/services/authService.ts:55-80`

**Payload:**
```typescript
interface AuthTokenPayload {
  sub: string;        // user.id (UUID)
  email: string;
  is_admin: boolean;
}
```

**Config:**
- `JWT_SECRET` — citit din env la fiecare call (`getJwtSecret`). **Min 16 chars** — altfel throw la `getJwtSecret()`. Generează: `openssl rand -hex 32`.
- `JWT_EXPIRES_IN` — default `7d` (7 zile). Env-override.

**Sign** (`signJwt(user)`): `jwt.sign(payload, secret, { expiresIn })`.

**Verify** (`verifyJwt(token)`):
- `TokenExpiredError` → `AuthError('TOKEN_EXPIRED', 'Sesiune expirată...', 401)`
- Orice altă problemă → `AuthError('INVALID_TOKEN', 'Token invalid', 401)`
- Verifică `sub` și `email` prezent (defense in depth)

## Password hashing

`bcrypt` (`bcryptjs` package), **10 rounds** (`src/services/authService.ts:6`).

- Hash la create (`register`, `createUserAsAdmin`, `resetUserPassword`)
- Compare la login (`verifyPassword`)
- Reset password: min 8 chars validare (`authService.ts:156`)

**Email normalization:** toate operațiile fac `.trim().toLowerCase()` — datorită `CITEXT` la nivelul DB, case-ul e irelevant oricum, dar normalizăm explicit.

## Middleware stack pentru auth

`src/middleware/authMiddleware.ts`

### `createAuthMiddleware(authService)`

Returnează un middleware care:

1. **Extract Bearer token** din header `Authorization`. Lipsă → 401 `MISSING_TOKEN`.
2. **Check `INTERNAL_API_TOKEN`** (L52-61). Dacă env-ul e setat (≥16 chars) și tokenul matches → synthesizează un user intern:
   ```typescript
   req.user = {
     id: '00000000-0000-0000-0000-000000000000',
     email: 'internal@pipeline',
     is_admin: true,
   };
   ```
3. **Altfel, verify JWT** via `authService.verifyJwt(token)`. Populează `req.user = {id, email, is_admin}`.
4. **Eșec** → 401 structurat (`TOKEN_EXPIRED` sau `INVALID_TOKEN`).

### `requireAdmin`

Trebuie montat **după** `createAuthMiddleware` (folosește `req.user`):
- `!req.user` → 401
- `!req.user.is_admin` → 403 `ADMIN_REQUIRED`

## Cum se aplică în rute

`src/index.ts` organizează așa:

```typescript
// Public
app.use(`${API}/auth/login`, authLimiter);
app.use(`${API}/auth/register`, authLimiter);
app.use(`${API}/auth`, createAuthRoutes(pool));  // register, login, me (cu requireAuth intern)

// Dev bypass (DOAR dev)
const authGuard = AUTH_DISABLED
  ? (_req, _res, next) => next()   // skip totul
  : requireAuth;

// Protected
app.use(`${API}/documents`,  authGuard, createDocumentRoutes(pool));
app.use(`${API}/audit-logs`, authGuard, createAuditLogRoutes(pool));
app.use(`${API}/settings`,   authGuard, createSettingsRoutes(pool));

// Admin-only (router-ul atașează intern requireAuth + requireAdmin)
app.use(`${API}/auth/admin/users`, createAdminUsersRoutes(pool));
```

## Feature flags de auth

| Flag | Tip | Default | Efect |
|------|-----|---------|-------|
| `REGISTER_ENABLED` | backend env | `false` | Dacă `false`, controllerul `register` returnează 403. Flip la `true` **temporar** pentru primul admin, apoi înapoi. |
| `AUTH_DISABLED` | backend env | `false` | Dacă `true`, toate rutele protejate sar peste middleware. `req.user` e undefined → controllerele tratează ca și admin. **NU** în prod. |
| `VITE_REGISTER_ENABLED` | frontend build arg | `false` | Dacă `false`, ruta `/register` nu se afișează în App.tsx; butonul "creează cont" lipsește din LoginPage. |
| `VITE_AUTH_DISABLED` | frontend build arg | `false` | Dacă `true`, `ProtectedRoute` returnează `<Outlet>` direct (fără check auth). Doar dev. |

> **De ce 2 flag-uri pentru register (backend + frontend):** backend-ul e sursa de adevăr — un user determinat poate POST direct la `/api/auth/register`. Flag-ul frontend ascunde doar UI-ul; backend-ul refuză. Ambele trebuie `false` pentru închidere reală.

## Rate limiting

`src/middleware/rateLimiter.ts`

| Limiter | Scope | Limita | Key |
|---------|-------|--------|-----|
| `authLimiter` (L8) | `/api/auth/login` + `/api/auth/register` | 5/min | IP |
| `apiLimiter` (L34) | `/api/*` | 2000/min | IP |

**`skipSuccessfulRequests: true` pe `authLimiter`** — un login reușit nu consumă din cota; doar login-urile eșuate contează. Un user care tastează greșit de 3 ori + reușește la a 4-a nu e pedepsit.

**IP real** — `app.set('trust proxy', 1)` la `src/index.ts:67`. Chain: Cloudflare → nginx → backend. `trust proxy 1` = încredere într-un singur hop (nginx), IP real din `X-Forwarded-For` pus de Cloudflare.

> **De ce 2000/min global:** AlertsPage face fetch de detalii în paralel pentru fiecare document (`useDocumentDetails(allIds)`). La 300+ documente, vechiul cap 100/min trunchia burst-ul și lăsa rânduri goale. Vezi [troubleshooting.md](./troubleshooting.md) §AlertsPage-empty-rows.

## Seed primul admin

Nu există UI-only flow pentru primul admin — trebuie fie:
1. Flip temporar `REGISTER_ENABLED=true`, register via UI, flip înapoi.
2. Rulează comanda inline din [runbook.md#seed-admin](./runbook.md#seed-admin) — bcrypt hash direct în DB. **Recomandat** pentru primul admin.

## Admin creează users

După login ca admin:
- UI: `/admin/users` → "Utilizator nou" → email + parolă generată → copy din toast
- CLI: `POST /api/auth/admin/users` cu Bearer admin + `{email, password, isAdmin?}`

Activare/dezactivare user: `PATCH /api/auth/admin/users/:id/active` cu `{is_active: boolean}`. **Împiedică self-deactivation** (nu-ți poți scoate propriul admin).

Reset parolă: `PATCH /api/auth/admin/users/:id/password` cu `{password}` (min 8 chars).

## OwnerFilter — user regulat vs admin

`documentController` + alte controllere derivă ownerul așa:

```typescript
function ownerOf(req: Request): string | null {
  if (req.user?.is_admin) return null;   // admin vede tot
  return req.user?.id ?? null;           // user regulat filtrat
}
```

Pasat la `DocumentModel.findById(id, owner)` etc. Vezi [database.md#ownerfilter-pattern](./database.md#ownerfilter-pattern).

**Pipeline-ul, autentificat cu `INTERNAL_API_TOKEN`, are `is_admin=true`** → fără filtrare. Asta e voit: pipeline-ul e un worker pur care poate procesa orice document.

## Audit log pentru acțiuni auth

Logate prin `AuditLogModel.create()` (immutable):

| Action type | Când |
|-------------|------|
| `USER_LOGIN` | `authService.login()` reușit |
| `CONFIG_CHANGE` | fiecare `PUT /api/settings/:key` sau `DELETE` |
| `DOCUMENT_UPLOAD`, `DOCUMENT_STATUS_CHANGE`, `DOCUMENT_DELETE`, `DOCUMENT_REVIEW` | acțiuni pe documente |

Eșecul de audit NU blochează request-ul business (log warn + continue). Vezi [architecture.md#audit-log-immutable](./architecture.md#audit-log-immutable).

## Verify freshness

```bash
# JWT_SECRET min 16 chars check
grep -n "secret.length < 16" src/services/authService.ts
# trebuie L27

# JWT expires default 7d
grep -n "JWT_EXPIRES_IN\s*||\s*'7d'" src/services/authService.ts
# trebuie L37

# bcrypt 10 rounds
grep -n "BCRYPT_ROUNDS\s*=\s*10" src/services/authService.ts
# trebuie L6

# First user auto-admin
grep -n "countAll()" src/services/authService.ts
# trebuie L90-92

# INTERNAL_API_TOKEN alternate auth
grep -n "internal@pipeline" src/middleware/authMiddleware.ts
# trebuie L56

# Rate limiter login 5/min
grep -A5 "authLimiter" src/middleware/rateLimiter.ts | grep "limit:"
# trebuie: limit: 5,

# Rate limiter global 2000/min
grep -A5 "apiLimiter" src/middleware/rateLimiter.ts | grep "limit:"
# trebuie: limit: 2000,

# Admin router include requireAdmin
grep -n "requireAdmin" src/routes/adminUsers.ts
# trebuie L5, L13
```
