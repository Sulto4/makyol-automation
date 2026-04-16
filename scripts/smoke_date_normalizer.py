"""Smoke-test the date normalizer against the edge cases that drove Pachet 3."""

from pipeline.date_normalizer import normalize_data_expirare

CASES = [
    # Canonical numeric already in target form
    ("14.02.2027", "date", "14.02.2027"),
    ("14.02.2027, cu conditia vizarii anuale", "date", "14.02.2027"),
    # Separators
    ("14/02/2027", "date", "14.02.2027"),
    ("14-02-2027", "date", "14.02.2027"),
    ("14_02_2027", "date", "14.02.2027"),
    ("14 02 2027", "date", "14.02.2027"),
    # ISO
    ("2027-02-14", "date", "14.02.2027"),
    ("2027.02.14", "date", "14.02.2027"),
    # 2-digit years
    ("14.02.27", "date", "14.02.2027"),
    ("14-02-27", "date", "14.02.2027"),
    # Romanian month names
    ("24 iulie 2028", "date", "24.07.2028"),
    ("24 Iulie 2028", "date", "24.07.2028"),
    ("24-iul-2028", "date", "24.07.2028"),
    ("11noiembrie2024", "date", "11.11.2024"),
    ("24 iulie 2028, cu reinnoire anuala", "date", "24.07.2028"),
    ("31 decembrie 2030", "date", "31.12.2030"),
    ("1 ianuarie 2026", "date", "01.01.2026"),
    # Diacritics variants
    ("24 noiembrie 2028", "date", "24.11.2028"),
    ("15 martie 2027", "date", "15.03.2027"),
    # English months
    ("May 19, 2028", "date", "19.05.2028"),
    ("Dec 12 2028", "date", "12.12.2028"),
    ("Oct 23, 2028", "date", "23.10.2028"),
    ("January 5, 2027", "date", "05.01.2027"),
    # Prefix phrases
    ("Valid through 2026-04-26.", "date", "26.04.2026"),
    ("Valid to 2026-04-26", "date", "26.04.2026"),
    ("This certificate is valid to 2026-04-26", "date", "26.04.2026"),
    ("Valabil pana la 31.12.2028", "date", "31.12.2028"),
    ("Valabil până la 31.12.2028", "date", "31.12.2028"),
    ("Data expirarii: 14.02.2027", "date", "14.02.2027"),
    ("Data de expirare: 14.02.2027", "date", "14.02.2027"),
    ("Expiry date: 2026-04-26", "date", "26.04.2026"),
    # Range — take tail
    ("2024-03-26 — 2027-03-25", "date", "25.03.2027"),
    ("31 aprilie 2024 – 31 martie 2027", "date", "31.03.2027"),
    ("14.02.2024 - 14.02.2027", "date", "14.02.2027"),
    ("2024-03-26 to 2027-03-25", "date", "25.03.2027"),
    # Durations — kept as-is with kind=duration
    ("Valabil 5 ani", "duration", None),
    ("5 ani", "duration", None),
    ("24 de luni", "duration", None),
    ("Pe durata contractului", "duration", None),
    ("pe durata derularii contractului", "duration", None),
    ("nelimitat", "duration", None),
    ("valabil pana la epuizarea stocului", "duration", None),
    # Month-year bare form — last day of month
    ("11-2027", "date", "30.11.2027"),
    ("12/2028", "date", "31.12.2028"),
    ("02-2024", "date", "29.02.2024"),   # leap year
    ("02-2023", "date", "28.02.2023"),   # non-leap
    ("13-2027", "raw", None),             # month out of range → raw
    # Multi-line duration
    ("2 ani\n50 ani\n2 ani\n6 luni\n30 ani", "duration", None),
    # Feminine / pe o perioada variants
    ("valabila pe o perioadă de 5 ani", "duration", None),
    ("valabilă pe perioada contractului", "duration", None),
    ("Valabilă pe o perioadă de 5 ani.", "duration", None),
    # Edge: empty
    ("", "empty", None),
    (None, "empty", None),
    # Edge: unparseable raw
    ("n/a", "raw", None),
    ("TBD", "raw", None),
]

passed = 0
failed: list[tuple] = []
for value, expected_kind, expected_out in CASES:
    got_out, got_kind = normalize_data_expirare(value)
    ok_kind = got_kind == expected_kind
    ok_out = expected_out is None or got_out == expected_out
    if ok_kind and ok_out:
        passed += 1
    else:
        failed.append((value, expected_kind, expected_out, got_kind, got_out))

print(f"passed {passed}/{len(CASES)}")
for row in failed:
    value, exp_kind, exp_out, got_kind, got_out = row
    print(f"  FAIL: {value!r} -> kind={got_kind} out={got_out!r}  (wanted kind={exp_kind} out={exp_out!r})")
