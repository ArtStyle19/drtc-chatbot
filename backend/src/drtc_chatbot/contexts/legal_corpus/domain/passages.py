"""Context of a provision for the content search: where it sits and what its parent says.

A passage such as ``e) Servicio de Transporte de Personas: …`` means nothing without the article
that introduces it ("Para efectos de la presente Ley, entiéndase por:"), and a numeral is found
better when the title of its chapter is part of what is indexed. Pure functions over the rows of
one approved edition.
"""

from collections.abc import Mapping
from dataclasses import dataclass

from drtc_chatbot.contexts.legal_corpus.domain.citations import describe_location
from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind

LEAD_LENGTH = 300
_ROMAN_LABEL_MAX = 4  # I, IV, VIII… are shown in capitals; "primera" as a word
SEPARATOR = " › "
INDEXABLE_KINDS = frozenset(
    {
        ProvisionKind.ARTICLE,
        ProvisionKind.NUMERAL,
        ProvisionKind.LITERAL,
        ProvisionKind.DISPOSITION,
        ProvisionKind.ANNEX,
    }
)
_CONTAINER_NAMES = {
    ProvisionKind.SECTION: "Sección",
    ProvisionKind.TITLE: "Título",
    ProvisionKind.CHAPTER: "Capítulo",
}


@dataclass(frozen=True, slots=True)
class ProvisionText:
    """The current text of one provision (containers included: they only give context)."""

    path: str
    kind: ProvisionKind
    label: str
    title: str | None
    text: str
    page_start: int
    page_end: int
    parent_path: str | None = None


def _label(row: ProvisionText) -> str:
    title = f" – {row.title.strip()}" if row.title and row.title.strip() else ""
    match row.kind:
        case ProvisionKind.ARTICLE:
            return f"Art. {row.label}{title}"
        case ProvisionKind.NUMERAL:
            return f"num. {row.label}"
        case ProvisionKind.LITERAL:
            return f"lit. {row.label})"
        case ProvisionKind.DISPOSITION | ProvisionKind.ANNEX:
            return f"{describe_location(row.path)}{title}"
        case _:
            name = _CONTAINER_NAMES[row.kind]
            number = (
                row.label.upper() if len(row.label) <= _ROMAN_LABEL_MAX else row.label.capitalize()
            )
            heading = f"{name} {number}"
            return f"{heading}: {row.title.strip()}" if row.title and row.title.strip() else heading


def ancestors(row: ProvisionText, by_path: Mapping[str, ProvisionText]) -> list[ProvisionText]:
    """Parents of ``row``, outermost first (the chain stops if a parent is unknown or loops)."""
    chain: list[ProvisionText] = []
    seen = {row.path}
    parent = by_path.get(row.parent_path or "")
    while parent is not None and parent.path not in seen:
        chain.append(parent)
        seen.add(parent.path)
        parent = by_path.get(parent.parent_path or "")
    chain.reverse()
    return chain


def breadcrumb(short_name: str, row: ProvisionText, by_path: Mapping[str, ProvisionText]) -> str:
    """``Ley 27181 (LGTTT) › Título I: Definiciones › Art. 2 – De las definiciones › lit. e)``."""
    parts = [short_name, *(_label(a) for a in ancestors(row, by_path)), _label(row)]
    return SEPARATOR.join(parts)


def lead_of(row: ProvisionText, by_path: Mapping[str, ProvisionText]) -> str | None:
    """The beginning of the nearest parent that has its own text (numerals and literals only)."""
    if row.kind not in {ProvisionKind.NUMERAL, ProvisionKind.LITERAL}:
        return None
    for parent in reversed(ancestors(row, by_path)):
        text = " ".join(parent.text.split())
        if text:
            return text[:LEAD_LENGTH].rstrip()
    return None
