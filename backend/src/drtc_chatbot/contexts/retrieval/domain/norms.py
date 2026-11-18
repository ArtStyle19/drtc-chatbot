"""Recognizing which norm a person means: acronyms, numbers, titles and the aliases of the manifest."""

import re
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from drtc_chatbot.contexts.retrieval.domain.text import normalize

_TYPE_PREFIXES: dict[str, tuple[str, ...]] = {
    "ley": ("ley",),
    "decreto_supremo": ("decreto supremo", "ds", "d s"),
    "decreto_legislativo": ("decreto legislativo", "dl", "d leg", "dleg"),
    "decreto_de_urgencia": ("decreto de urgencia", "du", "d u"),
    "texto_unico_ordenado": ("ley", "tuo ley", "tuo de la ley", "texto unico ordenado de la ley"),
    "reglamento": ("reglamento",),
    "resolucion": ("resolucion",),
}
_PARENTHETICAL = re.compile(r"\(([^)]+)\)")
# Something that looks like a norm ("ley 99999", "ds 017-2020-mtc") even if it is not in the corpus.
_UNKNOWN_NORM = re.compile(
    r"\b(?:ley|decreto supremo|decreto legislativo|decreto de urgencia|resolucion|ds|dl|du|d s|d leg)"
    r"\s+(?:n\s+)?(?P<number>\d[\d-]*(?:-[a-z]+)*)"
)


@dataclass(frozen=True, slots=True)
class NormInfo:
    """What the search needs to know about a norm of the corpus."""

    instrument_id: str
    instrument_type: str
    number: str
    title: str
    short_name: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NormMentions:
    instrument_ids: tuple[str, ...]  # recognized norms, in order of first mention
    unknown: str | None  # something that looks like a norm but is not in the corpus
    remainder: str  # the text without the norm mentions


class NormIndex:
    """Longest-alias-wins recognizer. An alias shared by two norms recognizes both (ambiguous)."""

    def __init__(self, norms: Sequence[NormInfo]) -> None:
        by_alias: dict[str, set[str]] = defaultdict(set)
        for norm in norms:
            for alias in self._aliases(norm):
                by_alias[alias].add(norm.instrument_id)
        self._by_alias = {alias: tuple(sorted(ids)) for alias, ids in by_alias.items()}
        ordered = sorted(self._by_alias, key=lambda alias: (-len(alias), alias))
        # "(?<![\w-])" / "(?![\w-])": whole tokens only, so "27181" never matches inside "127181-a"
        self._pattern = (
            re.compile(r"(?<![\w-])(?:" + "|".join(re.escape(a) for a in ordered) + r")(?![\w-])")
            if ordered
            else None
        )

    @staticmethod
    def _aliases(norm: NormInfo) -> set[str]:
        aliases = {normalize(alias) for alias in norm.aliases}
        number = normalize(norm.number)
        aliases.add(number)
        for prefix in _TYPE_PREFIXES.get(norm.instrument_type, ()):
            aliases.update({f"{prefix} {number}", f"{prefix} n {number}"})
        for text in (norm.title, norm.short_name):
            aliases.add(normalize(text))
            for inner in _PARENTHETICAL.findall(text):
                aliases.add(normalize(inner))
            aliases.add(normalize(_PARENTHETICAL.sub(" ", text)))
            aliases.update(normalize(clause) for clause in text.split(",") if " " in clause.strip())
        return {alias for alias in aliases if alias}

    def find(self, normalized: str) -> NormMentions:
        found: list[str] = []
        remainder = normalized
        if self._pattern is not None:
            for match in self._pattern.finditer(normalized):
                for instrument_id in self._by_alias[match.group(0)]:
                    if instrument_id not in found:
                        found.append(instrument_id)
            remainder = self._pattern.sub(" ", normalized)
        unknown = _UNKNOWN_NORM.search(remainder)
        return NormMentions(
            tuple(found),
            unknown.group(0) if unknown else None,
            " ".join(remainder.split()),
        )
