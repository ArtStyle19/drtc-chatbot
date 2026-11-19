"""Accent-insensitive matching for the words search.

PostgreSQL's Spanish stemmer only recognises suffixes such as "-ción" WITH the accent, so the plural
"apelaciones" and a singular typed without accent ("apelacion") end up as different stems. Measured on
the real corpus: 366 of its 6,403 distinct words (202 of them "-ción") stem differently when typed
without the accent. Instead of guessing rules, the index remembers which accented words the corpus
really has, and a search text is extended with the accented form of every word typed without accent
that exists in the corpus. Both forms then stem as the document does. Pure functions.
"""

import re
from collections.abc import Iterable, Mapping

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)  # runs of letters (ñ included)
_ACCENTS = str.maketrans("áéíóúü", "aeiouu")
_ACCENTED = frozenset("áéíóúü")
# A word ending in -ion after a consonant is stressed on the last syllable, so it carries the accent
# (apelación, unión, camión). The most frequent family (202 of the 366 words measured): "apelacion" -> "apelación". A fallback for
# when the corpus only has the plural ("notificaciones"), whose stem the stemmer does recognise.
_ION_ENDING = re.compile(r"(?<=[bcdfghjklmnñpqrstvwxyz])ion$")


def words(text: str) -> list[str]:
    """The words of a text, lowercased, in order (digits and punctuation are not words)."""
    return [match.group(0).casefold() for match in _WORD.finditer(text)]


def has_accent(word: str) -> bool:
    return any(char in _ACCENTED for char in word)


def strip_accents(word: str) -> str:
    """Removes the acute accent and the diaeresis from vowels; ``ñ`` is a different letter and stays."""
    return word.translate(_ACCENTS)


def accent_pairs(texts: Iterable[str]) -> set[tuple[str, str]]:
    """``(typed without accent, as written)`` for every accented word of the texts."""
    pairs: set[tuple[str, str]] = set()
    for text in texts:
        for word in words(text):
            if has_accent(word):
                pairs.add((strip_accents(word), word))
    return pairs


def expand_query(text: str, variants: Mapping[str, Iterable[str]]) -> str:
    """The text plus the accented form of each unaccented word: the one the corpus has, or "-ión"."""
    extra: dict[str, None] = {}
    for word in words(text):
        if has_accent(word):
            continue
        for accented in variants.get(word, ()):
            extra[accented] = None
        if _ION_ENDING.search(word):
            extra[_ION_ENDING.sub("ión", word)] = None
    return f"{text} {' '.join(extra)}" if extra else text
