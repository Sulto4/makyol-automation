---
title: Frontend (React/Vite/Tailwind)
scope: frontend
stability: living
last_verified: 2026-04-19
related:
  - ./architecture.md
  - ./api-reference.md
  - ./auth-and-access.md
code_refs:
  - frontend/src/App.tsx
  - frontend/src/api/client.ts
  - frontend/src/components/ProtectedRoute.tsx
  - frontend/src/store
  - frontend/nginx/default.conf
  - frontend/Dockerfile
---

# Frontend

Aplicația React 18 + Vite + Tailwind, UI în română pentru Makyol Automation. În dev rulează pe `:5173` prin Vite dev server cu proxy `/api`→backend:3000. În prod e bundle static servit de nginx (`:80`) cu reverse-proxy `/api`→backend:3000.

## Rol

- UI pentru upload PDF (single + folder drag-drop)
- Dashboard cu stats + grafice + activitate recentă
- Tabel documente cu filtre + sortare + paginare client-side
- Pagină alerte (documente cu `review_status` non-OK)
- Pagină settings (editează `settings` table)
- Pagină admin pentru management utilizatori (admin-only)
- Export Excel + ZIP arhive

## Directory layout (`frontend/src/`)

| Folder | Rol |
|--------|-----|
| `api/` | Axios client + modele de apeluri (`client.ts`, `documents.ts`, `settings.ts`) |
| `components/` | Componente reutilizabile: `dashboard/`, `documents/`, `layout/`, `settings/`, `upload/`, `shared/`, plus `ProtectedRoute.tsx` |
| `hooks/` | React Query custom hooks: `useDocuments`, `useTheme`, `useChartTheme`, `useUpload` |
| `pages/` | Componente pagină (9): `DashboardPage`, `DocumentsPage`, `DocumentDetailPage`, `UploadPage`, `AlertsPage`, `SettingsPage`, `LoginPage`, `RegisterPage`, `AdminUsersPage` |
| `store/` | Zustand stores persistate: `authStore`, `filterStore`, `settingsStore`, `themeStore` |
| `styles/` | `globals.css` cu Tailwind + dark mode class |
| `types/` | TS types: `DocumentCategory`, `ProcessingStatus`, `ReviewStatus`, `ClassificationMethod`, `CertificateMetadata` |
| `utils/` | Helpers (date formatting, etc.) |

## Routing (`App.tsx`)

9 rute definite. Gate-ul de auth e `ProtectedRoute` + layout wrapper.

| Path | Element | Protecție | Notă |
|------|---------|-----------|------|
| `/login` | `LoginPage` | Public | Ecran login |
| `/register` | `RegisterPage` | Public, gated | Ascunsă dacă `VITE_REGISTER_ENABLED !== 'true'` (L16, L32) |
| `/` | `DashboardPage` | `ProtectedRoute` + Layout | Stats + grafice |
| `/documents` | `DocumentsPage` | `ProtectedRoute` + Layout | Tabel paginat |
| `/documents/:id` | `DocumentDetailPage` | `ProtectedRoute` + Layout | Detalii + review modal |
| `/upload` | `UploadPage` | `ProtectedRoute` + Layout | Drag-drop single + folder |
| `/alerts` | `AlertsPage` | `ProtectedRoute` + Layout | Docs cu `review_status='REVIEW'` (N detail fetch-uri în paralel) |
| `/settings` | `SettingsPage` | `ProtectedRoute` + Layout | Editează `settings` table |
| `/admin/users` | `AdminUsersPage` | `ProtectedRoute adminOnly` + Layout | Admin creează users |

Vezi definiția în `frontend/src/App.tsx:30-50`.

### `ProtectedRoute` (`frontend/src/components/ProtectedRoute.tsx`)

- `isAuthenticated` false → `<Navigate to="/login" state={{ from: location }} />`
- `adminOnly && !user.is_admin` → `<Navigate to="/" />`
- `VITE_AUTH_DISABLED === 'true'` (la L5) → bypass complet pentru dev (skip auth wall)

## State management

### Zustand stores (toate cu `persist` în localStorage)

| Store | Key localStorage | State | Acțiuni |
|-------|------------------|-------|---------|
| `authStore` (`store/authStore.ts`) | `makyol-auth` | `token`, `user`, `isAuthenticated` | `login(email, pass)`, `register`, `logout`, `refreshUser` |
| `settingsStore` | `makyol-settings` | Overlay local peste DB settings (OpenRouter key, model, temp, etc.) | Editare în UI înainte de Save |
| `filterStore` | `makyol-filters` | `categories[]`, `processingStatus`, `reviewStatus`, `search`, `currentPage`, `perPage`, `sortField`, `sortDirection` | Setters per câmp; reset la schimbare filtru |
| `themeStore` | `makyol-theme` | `mode` (light/dark/system), `resolvedTheme` | `setMode`, detectare sistem via matchMedia |

**Partialize pattern** (`authStore:64-68`) — persistă doar state-ul relevant, nu funcțiile.

**Auto-refresh user la mount** (`App.tsx:22-27`) — dacă există token persistat, `refreshUser()` validează cu `GET /api/auth/me` și curăță starea dacă tokenul a expirat.

### React Query

- **Client unic** instanțiat în `main.tsx` (defaults: `staleTime 30s`, `refetchOnWindowFocus false`)
- **Custom hooks** în `hooks/useDocuments.ts` și altele:
  - Listă documente cu auto-polling 5s dacă orice doc e `processing`
  - `useDocumentDetails(allIds)` — `useQueries` paralel pentru N documente (folosit în AlertsPage)
  - `useDocumentStats` — fără auto-refetch
  - Mutations (reprocess, clear, review) invalidează `['documents']` + `['document-stats']` la success

## API client (`frontend/src/api/client.ts`)

- **Axios instance** cu `baseURL: '/api'` (L5)
- **Request interceptor** (L14-20) — injectează `Authorization: Bearer ${token}` din `useAuthStore.getState()`
- **Response interceptor** (L28-51) — normalizează erori:
  - 401 pe non-auth routes → `useAuthStore.getState().logout()` (sesiunea expiră)
  - Extrage `error.response.data.error.message`
  - Fallback: `"Eroare de conexiune la server"`
- **Upload progress** — rutele de upload folosesc `onUploadProgress` pentru progress bar

Module API:
- `api/documents.ts` — list, get, upload, upload-folder, reprocess, review, stats, export-archive, clear-all
- `api/settings.ts` — list, get, update, delete

## Build config

### `vite.config.ts`

- Port dev: `5173`
- Proxy dev: `/api` → `http://127.0.0.1:3000`, `/uploads` → `http://127.0.0.1:3000`
- Path alias: `@/*` → `src/*`

### Env vars (`VITE_*`)

| Var | Scop | Default |
|-----|------|---------|
| `VITE_REGISTER_ENABLED` | Afișează ruta `/register` | `false` în prod |
| `VITE_AUTH_DISABLED` | Dev bypass auth wall | `false` (doar dev) |

Baked în bundle la build time. Schimbare = rebuild frontend (nu hot-reload).

### Tailwind

- `tailwind.config.js`: `darkMode: 'class'`, `content: ['src/**/*.{ts,tsx}']`, fonts Inter
- Dark mode bazat pe `html.dark` class, controlat de `themeStore`

## Nginx (`frontend/nginx/default.conf`)

Servit de container frontend în prod.

- `listen 80`
- `client_max_body_size 25M` (headroom peste 10MB backend limit)
- **Gzip:** enabled, types text/css, application/json, application/javascript, min_length 1024
- **Cache:**
  - `/index.html` → `no-store, no-cache, must-revalidate` (SPA shell)
  - `/assets/` → `30d expires, public, immutable` (Vite hashed assets)
- **Proxy:**
  - `/api/` → `http://backend:3000` (600s send + read timeouts pentru Vision AI)
  - `/uploads/` → `http://backend:3000`
  - `/health` → `http://backend:3000/health`
- **SPA fallback:** `try_files $uri $uri/ /index.html`

> **De ce timeout 600s pe `/api/`:** Vision AI + OpenRouter + randare PDF poate depăși 5 minute pentru docs scanate multi-pagini. Valori mai mici au tăiat request-uri legitime.

## Dockerfile (`frontend/Dockerfile`)

Multi-stage:
1. **Builder** — `node:20-alpine`, copiază `package*.json` + `tsconfig*` + `vite.config.ts` + `tailwind.config.js` + `postcss.config.js` + `src/`, acceptă build args (`VITE_REGISTER_ENABLED`, `VITE_AUTH_DISABLED`), rulează `npm ci` + `npm run build`
2. **Runtime** — `nginx:alpine`, `apk add curl` (pentru healthcheck — vezi [troubleshooting.md](./troubleshooting.md)), copiază `dist/` → `/usr/share/nginx/html`, copiază `nginx/default.conf` → `/etc/nginx/conf.d/default.conf`, healthcheck `curl -fsS http://127.0.0.1/`

## i18n

**Fără framework i18n.** Tot textul UI e hardcodat în română. Mesaje de eroare, butoane, tab-uri, labels — toate direct în componente. Nu există traducere în alte limbi.

Format date: `DD.MM.YYYY` (match cu backend `data_expirare`).

## Verify freshness

```bash
# App.tsx are 9 rute
grep -cE "<Route path=" frontend/src/App.tsx
# trebuie ≥ 8 (login, register condițional, și 7 protejate)

# 4 store-uri Zustand
ls frontend/src/store/*.ts | wc -l
# trebuie 4

# 9 pagini
ls frontend/src/pages/*.tsx | wc -l
# trebuie 9

# ProtectedRoute are adminOnly + AUTH_DISABLED check
grep -n "VITE_AUTH_DISABLED\|adminOnly" frontend/src/components/ProtectedRoute.tsx

# api/client.ts are baseURL și Bearer interceptor
grep -E "baseURL: '/api'|Authorization.*Bearer" frontend/src/api/client.ts
# trebuie 2 match-uri

# Nginx config are 600s timeout
grep -n "proxy_read_timeout\|proxy_send_timeout" frontend/nginx/default.conf | grep 600
```
