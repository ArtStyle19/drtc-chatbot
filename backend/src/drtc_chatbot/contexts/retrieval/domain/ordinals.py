"""Spanish ordinals used by dispositions: primera, décima primera, única…"""

_UNIQUE = -1
_UNITS = {
    "primer": 1, "primera": 1, "primero": 1, "segunda": 2, "segundo": 2, "tercer": 3,
    "tercera": 3, "tercero": 3, "cuarta": 4, "cuarto": 4, "quinta": 5, "quinto": 5,
    "sexta": 6, "sexto": 6, "septima": 7, "septimo": 7, "octava": 8, "octavo": 8,
    "novena": 9, "noveno": 9,
}  # fmt: skip
_TENS = {"decima": 10, "decimo": 10, "vigesima": 20, "vigesimo": 20}
_SPECIAL = {"undecima": 11, "undecimo": 11, "duodecima": 12, "duodecimo": 12}
_ONLY = {"unica": _UNIQUE, "unico": _UNIQUE}

ORDINAL_WORD = (
    r"(?:primer[oa]?|segund[oa]|tercer[oa]?|cuart[oa]|quint[oa]|sext[oa]|septim[oa]|octav[oa]|"
    r"noven[oa]|decim[oa]|undecim[oa]|duodecim[oa]|vigesim[oa]|unic[oa])"
)
ORDINAL = rf"{ORDINAL_WORD}(?:\s+{ORDINAL_WORD})?"


def ordinal_value(words: str) -> int | None:
    """``"decima primera"`` → 11, ``"unica"`` → -1 (the only one), unknown → None."""
    parts = words.replace("-", " ").split()
    if len(parts) == 1:
        word = parts[0]
        return _ONLY.get(word) or _SPECIAL.get(word) or _UNITS.get(word) or _TENS.get(word)
    if len(parts) == 2 and parts[0] in _TENS and parts[1] in _UNITS:  # noqa: PLR2004
        return _TENS[parts[0]] + _UNITS[parts[1]]
    return None
