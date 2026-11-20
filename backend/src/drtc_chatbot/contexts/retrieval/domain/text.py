"""Text normalization for the reference search: no case, no accents, no ordinal signs."""

import re
import unicodedata

_NORM_SIGN = re.compile(r"\bn\s*[°º]|\bn\.\s*[°º]|\bnro\b\.?")
_ORDINAL_SIGNS = str.maketrans({"°": " ", "º": " ", "ª": " "})
_PUNCTUATION = re.compile(r"[()\[\]{}“”\"'«»¿?¡!;:,/\\]")
# Dots between digits (218.2) are kept, and so is the dot after a suffixed article label (4-A.1).
_STRAY_DOT = re.compile(r"(?<!\d)(?<!\d-[a-z])\.|\.(?!\d)")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Lowercase, accent-free, with single spaces; ``Art. 5° de la Ley N.° 27181`` → ``art 5 de la ley n 27181``.

    Dots between digits survive (``218.2``); hyphens survive (``4-A``, ``017-2009-MTC``).
    """
    folded = text.casefold()
    folded = _NORM_SIGN.sub(" n ", folded)  # before NFKD, which would turn "º" into "o"
    folded = folded.translate(_ORDINAL_SIGNS)
    decomposed = unicodedata.normalize("NFKD", folded)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    plain = _PUNCTUATION.sub(" ", plain)
    plain = _STRAY_DOT.sub(" ", plain)
    return _SPACES.sub(" ", plain).strip()
