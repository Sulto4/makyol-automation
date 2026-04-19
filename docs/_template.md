---
title: <Titlul doc-ului>
scope: <slug-scurt>              # ex: backend-auth, pipeline-vision
stability: living                # stable | living | runbook
last_verified: YYYY-MM-DD
related:
  - ./alt-doc.md
code_refs:
  - src/path/to/file.ts
  - pipeline/path/to/file.py
---

# <Titlul doc-ului>

<Un paragraf care explică ce acoperă acest document și ce NU acoperă.>

## <Prima secțiune — ex: Rol, Context, Overview>

<Conținut. Dacă enumeri 3+ lucruri, folosește tabel.>

| Coloană 1 | Coloană 2 | Coloană 3 |
|-----------|-----------|-----------|
|           |           |           |

## <A doua secțiune>

<Conținut.>

> **De ce:** <Bloc "De ce" doar pentru decizii ne-obișnuite. Ex: de ce am ales o tehnică care pare contra-intuitivă.>

## Verify freshness

Comenzi rulate din repo root, care re-confirmă claim-urile centrale din acest doc:

```bash
grep -n '<simbol>' <path>    # trebuie să returneze <ce aștepți>
ls <path>                     # trebuie să conțină <fișier>
```

Dacă o comandă eșuează sau returnează altceva → doc-ul e învechit; actualizează sau semnalează.
