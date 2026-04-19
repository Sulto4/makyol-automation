---
status: accepted
date: 2026-04-18
supersedes: —
---

# ADR 0005 — `INTERNAL_API_TOKEN` shared secret pentru pipeline → backend

## Context

Pipeline-ul are nevoie să apeleze `GET /api/settings` pe backend la startup și la fiecare `POST /api/pipeline/reload-settings`. După hardening-ul post-MVP, ruta `/api/settings` e behind `authGuard` — require Bearer JWT.

Pipeline-ul **nu e un user** — e un worker care orchestrează extracția. Opțiuni considerate:

1. **Seed un user "pipeline@internal"** cu JWT generat la deploy, rotat manual periodic. Necesită:
   - User în tabelul `users` (cu ce email dummy?)
   - Mecanism de generate JWT la deploy (inclus în scripts?)
   - Stocare JWT în env pipeline
   - Rotație (manual vs automat)

2. **Expune `/api/settings` fără auth.** Dar conține OpenRouter API key — secretele nu pot fi publice.

3. **Expune `/api/pipeline/internal-settings` fără auth** cu aceleași date. Duplicarea complică backend-ul și nu rezolvă problema dacă pipeline vrea și alte rute.

4. **Shared secret între backend și pipeline**, cu check în middleware-ul de auth care sari peste JWT dacă token-ul matches.

## Decizie

**`INTERNAL_API_TOKEN` env var partajat între backend și pipeline, ≥16 chars.** Backend middleware recunoaște acest token ca alternate auth și synthesizează un user intern admin.

```
src/middleware/authMiddleware.ts:52-61

const internalToken = process.env.INTERNAL_API_TOKEN;
if (internalToken && internalToken.length >= 16 && token === internalToken) {
  req.user = {
    id: '00000000-0000-0000-0000-000000000000',
    email: 'internal@pipeline',
    is_admin: true,
  };
  next();
  return;
}
```

Pipeline trimite ca `Authorization: Bearer <token>`:

```
pipeline/config.py:22-28

def _auth_headers() -> dict:
    if _INTERNAL_API_TOKEN:
        return {"Authorization": f"Bearer {_INTERNAL_API_TOKEN}"}
    return {}
```

Docker Compose injectează aceeași valoare în ambele servicii (`docker-compose.yml:56` + `:114`).

## Consecințe

**Pozitive:**
- **Zero overhead DB** pentru "userul" pipeline — nu există user real, doar sintetic la runtime
- **Zero rotație JWT** — rotația = update `.env` + redeploy compose
- **Zero cod nou** pe partea de generare/refresh JWT — middleware-ul e un if-branch
- Pipeline-ul are is_admin=true, deci poate scrie/citi orice (inclusiv setări)
- Check-ul ≥16 chars previne accidental dev-uri cu "token" gol sau "abc"

**Negative:**
- **Un singur secret pentru orice worker.** Dacă `.env` scurge, orice atacator poate impersona pipeline-ul (= admin acces la tot).
- **Nu identifică care instanță** a trimis request-ul. Toate request-urile pipeline ajung cu `user_id = '00000000-...'` în audit log. Dacă ai multe workers, nu distingem între ei.
- **Backend-ul trebuie să-l accepte pe orice rută protejată** (nu doar `/settings`) — pipeline poate oricând ajunge și la `/api/documents` cu drepturi admin. Poate un scope limitat ar fi fost mai curat.
- **Rotație = downtime.** Update `.env` necesită restart backend + pipeline simultan; altfel, în fereastra de tranziție, token-ul nou nu se potrivește cu cel vechi.

## Cost de reversare

**Săptămâni.** Migrarea la user real + JWT = creare user, seed script, stocare JWT în pipeline, logică de refresh (JWT expires) sau JWT pe termen lung (anti-pattern). Posibil, dar scurtă lista de beneficii nu justifică.

## Referințe

- [auth-and-access.md#middleware-stack-pentru-auth](../auth-and-access.md#middleware-stack-pentru-auth)
- [architecture.md#trust-boundaries](../architecture.md#trust-boundaries)
- [configuration.md](../configuration.md) — tabelul env vars
- Bug chain 2026-04-18 §5.3: incidentul care a declanșat implementarea (settings UI change nu ajungea la pipeline pentru că fetch-ul era 401)
