"""Unified date normalization for extraction results.

Reality check: vision returns data_expirare in wildly inconsistent formats —
Romanian month names, dashes, slashes, underscores, ISO-8601, two-digit
years, dates with trailing commentary ("14.02.2027, cu conditia vizarii
anuale"), and occasionally duration phrases ("Valabil 5 ani",
"Pe durata contractului"). The strict validator accepted only DD.MM.YYYY,
which sent ~90% of flagged documents to REVIEW for a field that was in fact
correctly extracted — just not formatted the way the validator expected.

This module provides a single function that:

  1. Strips trailing commentary/notes from a value that starts with a
     parseable date.
  2. Accepts numeric dates in any reasonable separator (`.`, `/`, `-`,
     `_`, whitespace) and normalizes to DD.MM.YYYY.
  3. Accepts ISO-8601 (YYYY-MM-DD / YYYY.MM.DD).
  4. Recognizes Romanian and English month names — full, abbreviated,
     diacritics present or stripped, any casing — and normalizes.
  5. Expands two-digit years (`26.02.26` → `26.02.2026`) using a
     ±50-year window from the current year so past/future both work.
  6. Recognizes explicit duration phrases ("5 ani", "Valabil 3 ani",
     "perioadă de 5 ani", "Pe durata contractului") and returns them
     unchanged but tagged `duration`, so the validator can accept them
     without flagging REVIEW.

The return contract is (normalized: str | None, kind: str) where kind is:
    "date"     — parsed successfully, DD.MM.YYYY string
    "duration" — recognized duration, value kept as-is (possibly tidied)
    "raw"      — couldn't parse, caller should keep original
    "empty"    — input was blank

The pipeline uses `kind` to decide what to persist and how to validate;
the validator uses `kind` to decide whether to flag the value.
"""

from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import date
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Month name lookup
#
# We normalize the incoming month text via _fold() (lowercase + strip
# diacritics + collapse whitespace) before looking up, so this table only
# needs to hold the folded forms.
# ---------------------------------------------------------------------------

_MONTHS: dict[str, int] = {
    # Romanian full names
    "ianuarie": 1, "februarie": 2, "martie": 3, "aprilie": 4,
    "mai": 5, "iunie": 6, "iulie": 7, "august": 8,
    "septembrie": 9, "octombrie": 10, "noiembrie": 11, "decembrie": 12,
    # Romanian common abbreviations
    "ian": 1, "feb": 2, "mar": 3, "apr": 4, "iun": 6, "iul": 7,
    "aug": 8, "sep": 9, "sept": 9, "oct": 10, "noi": 11, "nov": 11,
    "dec": 12,
    # English full + abbreviations (docs translated to English show up too).
    # Note: Romanian "mai" (5) is already covered above; English "may" is a
    # distinct spelling so it gets its own entry here.
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "jun": 6, "jul": 7,
}


def _fold(s: str) -> str:
    """Lowercase + strip diacritics + collapse whitespace."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    no_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", no_accents).strip().lower()


# ---------------------------------------------------------------------------
# Regex toolbox
#
# Each pattern anchors at the START of the string so that a value like
# "14.02.2027, cu conditia vizarii anuale" matches the date first and the
# trailing commentary is discarded by the caller.
# ---------------------------------------------------------------------------

# DD <sep> MM <sep> YYYY (or YY). Separators: . / - _ or whitespace.
_NUM_DATE_RE = re.compile(
    r"^\s*(?P<d>\d{1,2})\s*[./_\-\s]\s*(?P<m>\d{1,2})\s*[./_\-\s]\s*(?P<y>\d{2,4})\b"
)

# YYYY-MM-DD / YYYY.MM.DD / YYYY/MM/DD (ISO-ish)
_ISO_DATE_RE = re.compile(
    r"^\s*(?P<y>\d{4})\s*[./_\-]\s*(?P<m>\d{1,2})\s*[./_\-]\s*(?P<d>\d{1,2})\b"
)

# DD <sep> MonthText <sep> YYYY  (e.g. "24 iulie 2028", "24-Iul-2028",
# "24noiembrie2024"). MonthText has no internal whitespace; the rest of the
# string may be anything.
_TEXT_DATE_RE = re.compile(
    r"^\s*(?P<d>\d{1,2})\s*[.,\-_/\s]*\s*(?P<mo>[A-Za-zĂÂÎȘȚăâîșț]{3,})\s*[.,\-_/\s]*\s*(?P<y>\d{2,4})\b",
    re.UNICODE,
)

# MM <sep> YYYY — month-only granularity (e.g. "11-2027", "12/2028" on ISO
# certificates that specify only the expiration month). We interpret the
# expiry as the last day of that month, which is the conventional reading
# for certificate validity periods.
_MONTH_YEAR_RE = re.compile(
    r"^\s*(?P<m>\d{1,2})\s*[./_\-\s]\s*(?P<y>\d{4})\b"
)

# MonthText <sep> DD,? <sep> YYYY  (English ordering: "May 19, 2028",
# "Dec.12 2028", "Oct 23, 2028"). Same character-class toolkit as above,
# but the month leads and day follows.
_ENGLISH_TEXT_DATE_RE = re.compile(
    r"^\s*(?P<mo>[A-Za-zĂÂÎȘȚăâîșț]{3,})\s*[.,\-_/\s]*\s*(?P<d>\d{1,2})\s*[.,\-_/\s]*\s*(?P<y>\d{2,4})\b",
    re.UNICODE,
)

# Prefix phrases we strip off before attempting to parse a date. These are
# the intros that real-world certificates wrap around the actual date
# ("Valid through 2026-04-26.", "valabil pana la 31.12.2028"), often with
# trailing punctuation. The regex is case-insensitive on the ASCII parts.
_DATE_PREFIX_RE = re.compile(
    r"^\s*(?:"
    r"valid\s+(?:through|to|until|till)|"
    r"this\s+certificate\s+is\s+valid\s+(?:to|until|through)|"
    r"valabil(?:itate|[aă])?\s+(?:pana|p[âa]n[ăa])\s+la|"
    r"expir[aă]?\s+la|"
    r"expires\s+on|"
    r"expiry\s+date\s*[:\-]?|"
    r"data\s+expir[aă]rii\s*[:\-]?|"
    r"data\s+de\s+expirare\s*[:\-]?"
    r")\s*[:\-]?\s*",
    re.IGNORECASE,
)

# Range form: "31 aprilie 2024 – 31 martie 2027" or "2024-03-26 — 2027-03-25".
# Both halves share the date syntax we already handle; we want the *end*.
# A bare "-" is deliberately NOT included because it would split numeric
# dates like "24-07-2028"; we only treat it as a range separator when
# flanked by whitespace (" - ").
_RANGE_SEPARATORS_RE = re.compile(
    r"\s*(?:—|–|÷|\s-\s|\sto\s|\bpana\s+la\b|\bp[âa]n[ăa]\s+la\b)\s*",
    re.IGNORECASE,
)

# Duration phrases we consider valid as-is. Units in Romanian + English.
# The `(?:de\s+)?` between the number and unit catches phrases like
# "24 de luni" which Romanian uses naturally for anything >= 20.
_DURATION_RES = [
    # "5 ani", "24 de luni", "2 ani de la receptie", "valabil 5 ani",
    # "perioada de 5 ani"
    re.compile(
        r"^\s*(?:valabil(?:itate)?[:\s]+)?\s*\d+\s*(?:de\s+)?(?:ani|an|luni|luna|zile|zi)\b.*$",
        re.IGNORECASE,
    ),
    # "perioada / perioadă de 5 ani" (number may or may not be present
    # — "pe perioada contractului" is also valid). Optional leading
    # "valabil(a/ă)" covers phrasings like "valabila pe o perioadă de 5 ani",
    # "valabilă pe perioada ...".
    re.compile(
        r"^\s*(?:valabil[aăi]?\s+)?(?:pe\s+(?:o\s+)?)?perioad[aă](?:\s+de\s+\d+\s+(?:de\s+)?(?:ani|luni|zile))?.*$",
        re.IGNORECASE,
    ),
    # "pe durata contractului", "pe durata derularii contractului"
    re.compile(r"^\s*pe\s+durat[aă]\b.*$", re.IGNORECASE),
    # Same thing but starting with "durata" without "pe"
    re.compile(r"^\s*durat[aă]\s+(?:contractului|agrementului|avizului)\b.*$", re.IGNORECASE),
    # "nelimitat", "permanent", "pe termen nelimitat", "indefinite"
    re.compile(
        r"^\s*(?:pe\s+termen\s+)?(?:nelimitat[aă]?|permanent[aă]?|indefinite|nedeterminat[aă]?)\b.*$",
        re.IGNORECASE,
    ),
    # "valabil pana la epuizare(a stocului)" etc. — "epuizar\w*" to cover
    # both the indefinite ("epuizare") and the articled ("epuizarea") forms.
    re.compile(
        r"^\s*valabil(?:itate|[aă])?\s+(?:pana|p[âa]n[ăa])\s+la\s+epuizar\w*.*$",
        re.IGNORECASE,
    ),
    # "Notificarea/Certificatul/Documentul este valabil(ă) pe perioada..."
    re.compile(
        r"^\s*(?:notificarea|certificatul|documentul|avizul)\b.*(?:valabil|perioad[aă])\b.*$",
        re.IGNORECASE,
    ),
    # English equivalents — also allow "of" between number and unit for
    # parity with Romanian "de"
    re.compile(
        r"^\s*(?:valid\s+for\s+)?\s*\d+\s*(?:of\s+)?(?:years|year|months|month|days|day)\b.*$",
        re.IGNORECASE,
    ),
]


def _expand_two_digit_year(y: int) -> int:
    """Turn a 2-digit year into 4 digits using a ±50 year window."""
    if y >= 100:
        return y
    current = date.today().year
    century = (current // 100) * 100
    candidate = century + y
    # If the 2-digit year is more than 50 years in the future, assume it
    # was meant to be last century. Inverse for >50 years in the past.
    if candidate - current > 50:
        candidate -= 100
    elif current - candidate > 50:
        candidate += 100
    return candidate


def _format_date(d: int, m: int, y: int) -> Optional[str]:
    """Validate (d, m, y) and format as DD.MM.YYYY. Return None if invalid."""
    try:
        dt = date(y, m, d)
    except ValueError:
        return None
    return dt.strftime("%d.%m.%Y")


def _try_numeric(value: str) -> Optional[str]:
    m = _NUM_DATE_RE.match(value)
    if not m:
        return None
    d, mo, y = int(m.group("d")), int(m.group("m")), int(m.group("y"))
    y = _expand_two_digit_year(y)
    return _format_date(d, mo, y)


def _try_iso(value: str) -> Optional[str]:
    m = _ISO_DATE_RE.match(value)
    if not m:
        return None
    d, mo, y = int(m.group("d")), int(m.group("m")), int(m.group("y"))
    return _format_date(d, mo, y)


def _resolve_month(folded: str) -> Optional[int]:
    """Look up a folded month token in _MONTHS, falling back to prefix match.

    Prefix fallback catches OCR tails like "iuliei" or "iulie." and keeps
    us from over-counting REVIEW cases for a one-character difference.
    """
    mo_num = _MONTHS.get(folded)
    if mo_num is not None:
        return mo_num
    for k, v in _MONTHS.items():
        if folded.startswith(k):
            return v
    return None


def _try_text_month(value: str) -> Optional[str]:
    m = _TEXT_DATE_RE.match(value)
    if not m:
        return None
    mo_num = _resolve_month(_fold(m.group("mo")))
    if mo_num is None:
        return None
    d, y = int(m.group("d")), int(m.group("y"))
    y = _expand_two_digit_year(y)
    return _format_date(d, mo_num, y)


def _try_month_year(value: str) -> Optional[str]:
    """Parse "MM-YYYY" / "MM.YYYY" — certificates that list only month+year.

    Returns the last day of the month (natural expiry reading). The first
    number must fall in 1..12, which prevents accidental matches on
    two-number leads that are not month-year pairs.
    """
    m = _MONTH_YEAR_RE.match(value)
    if not m:
        return None
    mo = int(m.group("m"))
    y = int(m.group("y"))
    if not 1 <= mo <= 12:
        return None
    last_day = calendar.monthrange(y, mo)[1]
    return _format_date(last_day, mo, y)


def _try_english_text_date(value: str) -> Optional[str]:
    """Parse "Month DD, YYYY" ordering (e.g. "May 19, 2028", "Oct 23 2028").

    Guards against false positives by requiring the leading word to be a
    recognized month name — arbitrary English phrases that happen to start
    with a letter-word and contain numbers (e.g. "Notificarea 23 2028")
    will not parse.
    """
    m = _ENGLISH_TEXT_DATE_RE.match(value)
    if not m:
        return None
    mo_num = _resolve_month(_fold(m.group("mo")))
    if mo_num is None:
        return None
    d, y = int(m.group("d")), int(m.group("y"))
    y = _expand_two_digit_year(y)
    return _format_date(d, mo_num, y)


def _is_duration(value: str) -> bool:
    """Check if `value` reads as a duration phrase.

    Vision sometimes returns multi-line durations concatenated with newlines
    (e.g. when a cert lists per-product guarantees as "2 ani\\n50 ani\\n..."),
    so we collapse whitespace before matching — the `.*$` tails in the
    patterns don't cross newlines under default regex flags.
    """
    collapsed = re.sub(r"\s+", " ", value).strip()
    for r in _DURATION_RES:
        if r.match(collapsed):
            return True
    return False


_PARSERS = (
    _try_numeric,
    _try_iso,
    _try_text_month,
    _try_english_text_date,
    # MM-YYYY last so it does not preempt parsers that expect three tokens.
    _try_month_year,
)


def _parse_date(candidate: str) -> Optional[str]:
    """Run every date parser on `candidate`, return the first DD.MM.YYYY hit."""
    for parser in _PARSERS:
        parsed = parser(candidate)
        if parsed:
            return parsed
    return None


def normalize_data_expirare(value: Optional[str]) -> Tuple[Optional[str], str]:
    """Try hard to turn `value` into a canonical DD.MM.YYYY date string.

    See module docstring for the semantics of the (normalized, kind) tuple.
    """
    if value is None:
        return None, "empty"
    v = str(value).strip()
    if not v:
        return None, "empty"

    # Strip an intro phrase like "Valid through:" or "valabil pana la" so
    # the parsers below can anchor on the actual date characters.
    v_stripped = _DATE_PREFIX_RE.sub("", v).strip()

    # If the value is a range ("2024-03-26 — 2027-03-25",
    # "31 aprilie 2024 – 31 martie 2027"), prefer the *end* half — that's
    # the expiration date. We try the tail first but still fall back to the
    # full string so single dates with stray dashes aren't broken.
    candidates = [v_stripped]
    parts = _RANGE_SEPARATORS_RE.split(v_stripped)
    if len(parts) > 1:
        tail = parts[-1].strip()
        if tail and tail != v_stripped:
            candidates.insert(0, tail)

    # Each parser is anchored at the string start — so a value like
    # "14.02.2027, cu conditia vizarii anuale a certificatului" matches the
    # date and the trailing comment is dropped implicitly.
    for candidate in candidates:
        parsed = _parse_date(candidate)
        if parsed:
            return parsed, "date"

    # Explicit duration phrase — keep the value, mark it so the validator
    # can accept it without forcing DD.MM.YYYY format.
    if _is_duration(v):
        # Normalize whitespace/casing minimally — users asked for a tidy
        # output but not a reworded one.
        tidy = re.sub(r"\s+", " ", v).strip()
        # Strip a single trailing period / comma.
        tidy = re.sub(r"[.,]\s*$", "", tidy)
        return tidy, "duration"

    # Couldn't parse — hand the string back untouched so the caller can
    # store it and the validator can decide.
    return v, "raw"


# ---------------------------------------------------------------------------
# Filename date scanner
#
# Counterpart to normalize_data_expirare for the G4 filename fallback.
# Scans anywhere in the filename for DD<sep>MM<sep>YYYY or DD<text-month>YYYY
# and returns every hit — the caller then decides which one to use
# (typically the most recent plausible expiry).
# ---------------------------------------------------------------------------

# DD <opt-sep> MonthText <opt-sep> YYYY, no word boundaries on the ends
# because filenames often pack dates against other tokens ("11noiembrie2024"
# or "21nov2027" seen in the wild).
_FILENAME_TEXT_DATE_RE = re.compile(
    r"(\d{1,2})\s*[.\-_/ ]*([A-Za-zĂÂÎȘȚăâîșț]{3,})\s*[.\-_/ ]*(\d{4})",
    re.UNICODE,
)


def scan_filename_dates(filename: str) -> list[date]:
    """Return every concrete date we can pull out of a filename.

    Handles both numeric DD[_.-]MM[_.-]YYYY (already covered by the pipeline's
    regex) and text-month variants ("11noiembrie2024", "21nov2027"). The
    caller is responsible for filtering (e.g. year >= current-1) and for
    picking the preferred candidate.
    """
    stem = filename.rsplit(".", 1)[0]
    out: list[date] = []

    # Numeric hits — duplicate of the pipeline regex but kept here so the
    # scanner is self-contained and unit-testable.
    for m in re.finditer(
        r"(?<![0-9])(\d{1,2})[._\-](\d{1,2})[._\-](\d{4})(?![0-9])", stem
    ):
        d, mo, y = (int(g) for g in m.groups())
        try:
            out.append(date(y, mo, d))
        except ValueError:
            continue

    # Text-month hits.
    for m in _FILENAME_TEXT_DATE_RE.finditer(stem):
        d_txt, mo_txt, y_txt = m.groups()
        mo_num = _resolve_month(_fold(mo_txt))
        if mo_num is None:
            continue
        try:
            out.append(date(int(y_txt), mo_num, int(d_txt)))
        except ValueError:
            continue

    return out
