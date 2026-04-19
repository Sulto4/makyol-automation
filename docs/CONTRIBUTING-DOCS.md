---
title: Reguli de contribuție pentru documentație
scope: docs-contributing
stability: stable
last_verified: 2026-04-19
related:
  - ./index.md
  - ./_template.md
---

# Cum adaugi sau modifici documentația

Reguli minime ca structura `docs/` să rămână navigabilă și docs-urile să nu divergă în timp. Folosește [_template.md](./_template.md) pentru docs noi și [adr/_template.md](./adr/_template.md) pentru ADR-uri (când le adăugăm în Valul 3).

## Unde trăiește fiecare tip de doc

| Tip | Locație | Exemplu |
|-----|---------|---------|
| Prezentare top-level | `docs/index.md` (doar editat, nu adăugat) | — |
| Arhitectură cross-cutting (stable) | `docs/<nume>.md` | `architecture.md`, `auth-and-access.md` |
| Reference per-serviciu (living) | `docs/<serviciu>.md` | `backend.md`, `pipeline.md`, `frontend.md` |
| Reference mecanic (living) | `docs/<nume>.md` | `api-reference.md`, `configuration.md`, `database.md` |
| Runbook operațional | `docs/runbook.md` (adaugă secțiune) | "Rotate cheie", "Backup DB" |
| Topologie / infrastructură | `docs/deployment.md` | — |
| Simptom/fix | `docs/troubleshooting.md` (adaugă rând) | — |
| Decizie arhitecturală | `docs/adr/NNNN-slug.md` | `0001-vision-unconditional.md` |
| Doc învechit | `docs/archive/<nume>.md` | `README-mvp.md` |

**Regula:** un doc are o singură casă. Dacă ești tentat să duplichezi conținut, fă link în loc.

## Frontmatter obligatoriu

Fiecare `.md` din `docs/` (și subfoldere) începe cu:

```yaml
---
title: <Titlul vizibil>
scope: <slug>           # unic per doc; ex: backend-auth, pipeline-vision
stability: <nivel>      # stable | living | runbook
last_verified: YYYY-MM-DD
related: [...]          # linkuri relative la alte docs
code_refs: [...]        # fișiere sursă pe care doc-ul le descrie
---
```

**Semantica `stability`:**

- `stable` — arhitectură, ADR-uri, invariante. Se schimbă doar când arhitectura se schimbă. Review trimestrial.
- `living` — reference docs care urmează codul. Actualizate în același commit cu schimbarea de cod.
- `runbook` — proceduri ops, URL-uri prod, path-uri credentiale. Actualizat la fiecare schimbare environment.

**`last_verified`:** data când cineva a rulat secțiunea `## Verify freshness` și comenzile au trecut. Pentru `runbook` mai vechi de 30 zile, re-verifică înainte de a executa procedura.

## Reguli de conținut

1. **Tabele peste proză** pentru enumerări (3+ rânduri). Mai ușor de scanat vizual și de parsat de AI.
2. **Ancore `path:line`** pentru toate referințele la cod. Scrie `src/index.ts:115`, nu "middleware-ul de auth din bootstrap".
3. **Blocul "De ce"** doar pentru decizii ne-obișnuite. Format: `> **De ce:** <un paragraf>`. Regulă: dacă un contribuitor nou ar întreba "dar de ce așa?", include-l. Altfel nu.
4. **Max 110 caractere/linie** (mai ușor de diff/review). Max adâncime `###` (fără `####`). Max 600 linii/doc; peste — split.
5. **Fără versiuni narative**. Nu scrie "la 2026-04-18 s-a întâmplat X" în doc `living`. Transformă în regulă durabilă ("simptom → cauză → fix").
6. **Secțiunea finală `## Verify freshness`** obligatorie. Include 2-4 comenzi grep/ls care re-confirmă claim-urile centrale. Ex:

   ```bash
   grep -n '_USE_VISION_FOR_ALL' pipeline/__init__.py  # trebuie L29 = True
   ```

## Limba

- Proză, titluri, explicații, "De ce" — **română**.
- Nume de variabile, comenzi shell, path-uri, env vars, field names SQL, nume de tabele, clase, funcții — **engleză** (cum sunt în cod).
- Nu traduce simboluri. `certified_company` rămâne `certified_company`, nu "companie_certificată".

## Cum adaugi un doc nou

1. **Confirmă că trebuie un doc nou**, nu o secțiune într-unul existent. Regula: dacă conținutul se potrivește natural sub un `##` al unui doc existent, adaugă-l acolo.
2. Copiază [`_template.md`](./_template.md) în locația potrivită (vezi tabelul de sus).
3. Umple frontmatter-ul complet (fără câmpuri goale).
4. Scrie conținutul. Folosește tabele, ancore `path:line`, blocuri "De ce" când e cazul.
5. Adaugă comenzile `Verify freshness` — rulează-le și asigură-te că trec.
6. **Adaugă o intrare în [`index.md`](./index.md)** — un rând în tabelul de docs + eventual un rând în "Vreau să...".
7. Dacă e un termen nou relevant, **adaugă-l în glosarul din [`index.md`](./index.md)**.

## Cum modifici un doc existent

1. Actualizează conținutul.
2. Actualizează `last_verified: YYYY-MM-DD` în frontmatter (data curentă).
3. Rulează secțiunea `## Verify freshness` — toate comenzile trebuie să treacă. Dacă nu trec, înseamnă că doc-ul a ieșit din sincron cu codul; fixează doc-ul sau codul.
4. Dacă schimbarea afectează cross-links, actualizează și doc-urile care referă.

## Cum depreciezi un doc

1. Mută-l în `docs/archive/` cu sufixul care explică contextul (ex: `-mvp.md` pentru pre-hardening, sau data snapshot).
2. La începutul fișierului arhivat adaugă un banner:

   ```markdown
   > **Depreciat.** <un rând despre ce era și de ce a fost înlocuit>.
   > Pentru versiunea curentă vezi [../<nou-doc>.md](../<nou-doc>.md).
   ```

3. Dacă alte docs linkau la cel depreciat, actualizează linkurile să indice la doc-ul nou (sau elimină linkurile dacă conținutul nu mai e relevant).
4. Actualizează `docs/index.md` să nu mai listeze doc-ul depreciat în tabelul principal (opțional: menționează în secțiunea `archive/`).

## Anti-patterns (ce NU face)

- ❌ **Duplicare conținut.** Env vars doar în `configuration.md` + `.env.example`. Proceduri doar în `runbook.md`. Restul face link.
- ❌ **URL-uri prod hardcodate în arhitectură.** `makyol.voostvision.ro` e doar în `deployment.md`. Arhitectura zice "în spatele unui tunel Cloudflare (vezi deployment.md)".
- ❌ **Fișiere ciornă.** Nu `NOTES.md`, `TODO.md`, `meeting-2026-xx.md` în `docs/`. Folosește task tracker sau notițe externe.
- ❌ **Fără ancore line.** "Middleware-ul de bootstrap" e ambiguu; `src/index.ts:115` e precis.
- ❌ **Prea multe niveluri de header.** Max `###`. Dacă simți nevoia de `####`, split doc-ul.
- ❌ **Citări de comportament specific timpului.** "Fill-rate de azi e X" devine învechit; "baseline 2026-04-18: X" e durabil.

## Verify freshness

```bash
# Toate docs-urile din docs/ au frontmatter
for f in docs/*.md docs/adr/*.md; do
  head -1 "$f" | grep -q "^---$" || echo "MISSING FRONTMATTER: $f"
done

# _template.md există
ls docs/_template.md

# Scripts/verify_docs.py (Valul 3) — momentan încă nu e scris
```
