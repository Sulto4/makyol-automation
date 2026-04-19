"""Heuristic country detection for distributor / producer addresses.

Used to decide whether `adresa_distribuitor` (and potentially other address
fields) refers to a Romanian location or to a foreign one. Output drives the
`distribuitor_not_romanian` review reason emitted from `validation.py`.

Strategy:
    1. Normalize input (lowercase, strip Romanian diacritics).
    2. If a foreign-country token is present → OTHER (takes precedence).
    3. Else, if any Romanian signal is present → RO.
    4. Else → OTHER (conservative default — favors human verification).

Returns `None` only when input is empty / whitespace, so callers can skip
alert emission for missing values.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Literal, Optional

Country = Literal["RO", "OTHER"]

# Romanian cities (lowercased, diacritics stripped). Covers county capitals and
# notable industrial towns that recur in supplier addresses.
_RO_CITIES: frozenset[str] = frozenset({
    "bucuresti", "cluj-napoca", "cluj napoca", "iasi", "timisoara", "constanta",
    "brasov", "sibiu", "oradea", "ploiesti", "bacau", "pitesti", "craiova",
    "galati", "arad", "targu mures", "tirgu mures", "buzau", "satu mare",
    "botosani", "baia mare", "suceava", "ramnicu valcea", "rimnicu valcea",
    "focsani", "tulcea", "resita", "slatina", "alba iulia", "giurgiu",
    "targoviste", "tirgoviste", "zalau", "deva", "bistrita", "vaslui",
    "miercurea ciuc", "sfantu gheorghe", "sfintu gheorghe", "piatra neamt",
    "calarasi", "slobozia", "alexandria", "roman", "medias", "turda",
    "mangalia", "saratel", "hunedoara", "campulung", "campina", "onesti",
    "reghin", "falticeni", "barlad", "sighisoara", "fagaras", "lugoj",
    "mioveni", "caracal", "husi", "odorheiu secuiesc", "carei",
})

# Romanian street / address prefixes. Match token-ish so "strand" doesn't fire.
_RO_STREET_PREFIXES: tuple[str, ...] = (
    r"\bstr\.", r"\bstrada\b", r"\bstr\b",
    r"\bbd\.", r"\bbulevardul\b", r"\bb-dul\b", r"\bb\.dul\b",
    r"\baleea\b", r"\bcalea\b", r"\bpiata\b", r"\bpta\.",
    r"\bsos\.", r"\bsoseaua\b", r"\bintrarea\b", r"\bintr\.",
    r"\bdn\d+\b",  # drumuri nationale
)

# Administrative hints unique to RO
_RO_ADMIN_HINTS: tuple[str, ...] = (
    r"\bjud\.", r"\bjudetul\b",
    r"\bsector\s*[1-6]\b",
    r"\bmun\.",
    r"\bcom\.",
    r"\bsat\s",
)

# Explicit country tokens. "OTHER" matches override everything else.
_FOREIGN_COUNTRIES: frozenset[str] = frozenset({
    # names in native + English + Romanian
    "italia", "italy", "italien",
    "germania", "germany", "deutschland",
    "franta", "france",
    "turcia", "turkey", "turkiye",
    "china", "p.r.c.", "p.r. china", "pr china",
    "spania", "spain", "espana",
    "polonia", "poland", "polska",
    "ungaria", "hungary", "magyarorszag",
    "bulgaria",
    "austria", "osterreich",
    "olanda", "netherlands", "holland", "nederland",
    "belgia", "belgium", "belgique",
    "grecia", "greece", "hellas",
    "cehia", "czech republic", "czechia",
    "slovacia", "slovakia",
    "suedia", "sweden",
    "elvetia", "switzerland", "schweiz", "suisse",
    "uk", "united kingdom", "regatul unit", "great britain", "england",
    "usa", "united states", "statele unite",
    "japan", "japonia",
    "korea", "coreea",
    "serbia", "srbija",
    "croatia", "hrvatska", "croatia",
    "slovenia",
    "ucraina", "ukraine",
    "rusia", "russia",
    "portugalia", "portugal",
    "irlanda", "ireland",
    "danemarca", "denmark",
    "finlanda", "finland",
    "norvegia", "norway",
})

_RO_POSTCODE_RE = re.compile(r"\b\d{6}\b")
_STREET_RE = re.compile("|".join(_RO_STREET_PREFIXES))
_ADMIN_RE = re.compile("|".join(_RO_ADMIN_HINTS))


def _normalize(addr: str) -> str:
    nfkd = unicodedata.normalize("NFKD", addr)
    without_diacritics = "".join(c for c in nfkd if not unicodedata.combining(c))
    return without_diacritics.lower().strip()


def detect_address_country(addr: Optional[str]) -> Optional[Country]:
    """Return 'RO', 'OTHER', or None (empty input).

    See module docstring for the decision order. Default when no signals match
    is 'OTHER' (conservative — favors flagging for human review).
    """
    if not addr or not addr.strip():
        return None

    norm = _normalize(addr)

    # Foreign-country tokens trump everything. Use word boundaries where the
    # token doesn't end in punctuation (e.g. "p.r.c.").
    for country in _FOREIGN_COUNTRIES:
        if "." in country or " " in country:
            if country in norm:
                return "OTHER"
        else:
            if re.search(rf"\b{re.escape(country)}\b", norm):
                return "OTHER"

    # Positive RO signals
    if "romania" in norm:
        return "RO"
    if re.search(r"\bro[-\s]?\d{5,6}\b", norm):  # RO-postcode
        return "RO"
    if _STREET_RE.search(norm):
        return "RO"
    if _ADMIN_RE.search(norm):
        return "RO"
    if _RO_POSTCODE_RE.search(norm):
        return "RO"
    for city in _RO_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", norm):
            return "RO"

    # Ambiguous → conservative default
    return "OTHER"


def is_romanian_address(addr: Optional[str]) -> Optional[bool]:
    """Convenience wrapper: True/False/None (empty input)."""
    country = detect_address_country(addr)
    if country is None:
        return None
    return country == "RO"
