"""Parser of legal references typed by a person: ``art. 2 lit. e``, ``218.2``, ``anexo 2``…

It understands structure only (which article, numeral, literal, annex, title or disposition); the
norm is recognized separately (``norms.py``). Everything is deterministic: no similarity, no guessing.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass

from drtc_chatbot.contexts.retrieval.domain.ordinals import ORDINAL, ordinal_value
from drtc_chatbot.contexts.retrieval.domain.text import normalize

_NUMBER = r"\d+(?:\.\d+)*(?:-[a-z])?(?:\.\d+)*"
_ROMAN = r"(?=[ivx])x{0,3}(?:ix|iv|v?i{0,3})"  # I..XXXIX; "civil" is not a numeral
_GROUP_WORD = r"(?:complementarias?|transitorias?|derogatorias?|final(?:es)?)"
_GROUP = rf"(?:\s+(?:y\s+)?{_GROUP_WORD})"

_ABBREVIATIONS = (
    (re.compile(r"\bdcf\b"), "disposicion complementaria final"),
    (re.compile(r"\bdct\b"), "disposicion complementaria transitoria"),
    (re.compile(r"\bdcd\b"), "disposicion complementaria derogatoria"),
)

_DISPOSITION_ORDINAL_FIRST = re.compile(
    rf"\b(?P<ord>{ORDINAL})\s+disposici(?:on|ones)(?P<grp>{_GROUP}*)"
)
_DISPOSITION_GROUP_FIRST = re.compile(
    rf"\bdisposici(?:on|ones)(?P<grp>{_GROUP}+)(?:\s+(?P<ord>{ORDINAL}))?"
)
_SECTION = re.compile(rf"\bseccion\s+(?P<v>{ORDINAL}|\d+)\b")
_ANNEX = re.compile(rf"\banexos?\s+(?P<v>\d+|{_ROMAN}|unico)\b")
_TITLE = re.compile(rf"\btitulos?\s+(?P<v>{_ROMAN}|preliminar|\d+)\b")
_CHAPTER = re.compile(rf"\bcapitulos?\s+(?P<v>{_ROMAN}|\d+)\b")
_ARTICLE = re.compile(rf"\b(?:articulos?|arts?)\s+(?P<v>{_NUMBER}|{_ROMAN})\b")
_NUMERAL = re.compile(rf"\b(?:numeral(?:es)?|nums?)\s+(?P<v>{_NUMBER})\b")
_LITERAL = re.compile(r"\b(?:literal(?:es)?|lits?|letra|incisos?|incs?)\s+(?P<v>[a-zñ])\b")
_ITEM = re.compile(r"\b(?:incisos?|incs?)\s+(?P<v>\d+)\b")
_BARE_NUMERAL = re.compile(r"(?<![\w.-])(?P<v>\d+(?:-[a-z])?\.\d+(?:\.\d+)*)(?![\w.-])")

_RANK = {
    "seccion": 0, "titulo": 1, "capitulo": 2, "articulo": 3, "anexo": 3, "disposicion": 3,
    "numeral": 4, "literal": 5,
}  # fmt: skip
_DISPLAY = {"titulo": "título", "capitulo": "capítulo", "articulo": "art.", "anexo": "anexo"}
_GROUP_CANONICAL = {
    "complementaria": "complementaria", "complementarias": "complementaria",
    "transitoria": "transitoria", "transitorias": "transitoria",
    "derogatoria": "derogatoria", "derogatorias": "derogatoria",
    "final": "final", "finales": "final",
}  # fmt: skip


@dataclass(frozen=True, slots=True)
class Step:
    """One structural level of a reference. ``value`` is normalized (casefolded)."""

    kind: str  # seccion | titulo | capitulo | articulo | anexo | disposicion | numeral | literal
    value: (
        str  # "2", "4-a", "218.2", "e", "iv"; for dispositions the ordinal words ("" = the group)
    )
    group: tuple[str, ...] = ()  # disposition group, canonical singular words

    @property
    def rank(self) -> float:
        base = float(_RANK[self.kind])
        if self.kind == "numeral" and "." not in self.value:
            base += 0.5  # "inciso 2" goes below "numeral 35.1"
        return base

    def describe(self) -> str:
        """The step the way lawyers write it: ``art. 2``, ``lit. e)``, ``primera disposición final``."""
        value = self.value
        match self.kind:
            case "disposicion":
                return " ".join(part for part in (value, "disposición", *self.group) if part)
            case "literal":
                return f"lit. {value})"
            case "numeral":
                return f"num. {value}"
            case "seccion":
                return f"sección {value}"
            case "titulo" | "capitulo" | "articulo" | "anexo":
                label = value.capitalize() if value.isalpha() and len(value) > 4 else value.upper()  # noqa: PLR2004
                return f"{_DISPLAY[self.kind]} {label}"
        return f"{self.kind} {value}"


@dataclass(frozen=True, slots=True)
class ParsedSteps:
    steps: tuple[Step, ...]
    leftover: str  # what is not part of any step (norm mentions are still inside)


def canonical_group(words: str) -> tuple[str, ...]:
    found = []
    for word in words.replace("-", " ").split():
        canonical = _GROUP_CANONICAL.get(word)
        if canonical and canonical not in found:
            found.append(canonical)
    return tuple(found)


def parse_steps(normalized: str) -> ParsedSteps:
    """Extract the structural steps from an already normalized text, in hierarchical order."""
    text = normalized
    for pattern, replacement in _ABBREVIATIONS:
        text = pattern.sub(replacement, text)
    steps: list[Step] = []

    def take(pattern: re.Pattern[str], build: Callable[[re.Match[str]], list[Step]]) -> None:
        nonlocal text
        for match in pattern.finditer(text):
            steps.extend(build(match))
        text = pattern.sub(" ", text)

    def disposition(match: re.Match[str]) -> list[Step]:
        ordinal = (match.groupdict().get("ord") or "").strip()
        return [
            Step(
                "disposicion",
                ordinal if ordinal_value(ordinal) is not None else "",
                canonical_group(match.group("grp")),
            )
        ]

    take(_DISPOSITION_ORDINAL_FIRST, disposition)
    take(_DISPOSITION_GROUP_FIRST, disposition)
    take(_SECTION, lambda m: [Step("seccion", m.group("v"))])
    take(_ANNEX, lambda m: [Step("anexo", m.group("v"))])
    take(_TITLE, lambda m: [Step("titulo", m.group("v"))])
    take(_CHAPTER, lambda m: [Step("capitulo", m.group("v"))])

    def article(match: re.Match[str]) -> list[Step]:
        value = match.group("v")
        if "." in value and value[0].isdigit():  # "art 218.2" is numeral 218.2 of article 218
            return [Step("articulo", value.split(".")[0]), Step("numeral", value)]
        return [Step("articulo", value)]

    take(_ARTICLE, article)
    take(_NUMERAL, lambda m: [Step("numeral", m.group("v"))])
    take(_ITEM, lambda m: [Step("numeral", m.group("v"))])
    take(_LITERAL, lambda m: [Step("literal", m.group("v"))])
    # "218.2" typed alone is numeral 218.2 of article 218 (only when nothing else named an article)
    if not any(step.kind == "articulo" for step in steps):
        for match in _BARE_NUMERAL.finditer(text):
            value = match.group("v")
            steps.extend([Step("articulo", value.split(".")[0]), Step("numeral", value)])
        text = _BARE_NUMERAL.sub(" ", text)
    ordered = sorted(steps, key=lambda step: step.rank)  # stable: "lit e del art 2" → art, lit
    return ParsedSteps(tuple(_dedupe(ordered)), " ".join(text.split()))


def _dedupe(steps: list[Step]) -> list[Step]:
    seen: set[Step] = set()
    result = []
    for step in steps:
        if step not in seen:
            seen.add(step)
            result.append(step)
    return result


def parse_reference_text(raw: str) -> ParsedSteps:
    """Normalize ``raw`` and parse its structural steps (convenience for tests and callers)."""
    return parse_steps(normalize(raw))
