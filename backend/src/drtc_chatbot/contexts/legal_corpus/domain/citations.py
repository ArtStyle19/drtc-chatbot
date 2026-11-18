"""Legal citations: how a provision is cited, in short and in formal form.

The backend generates every citation (constitution I.2-3). Nothing here claims that a text is in
force: the formal form always states the verification status of the edition.
"""

from dataclasses import dataclass
from datetime import date

from drtc_chatbot.contexts.legal_corpus.domain.provisions import LegalEvent
from drtc_chatbot.contexts.legal_corpus.domain.reading import PathSegment, split_path
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    VerificationStatus,
)

_SHORT_NAMES = {
    InstrumentType.LAW: "Ley N.° {n}",
    InstrumentType.SUPREME_DECREE: "D.S. N.° {n}",
    InstrumentType.LEGISLATIVE_DECREE: "D. Leg. N.° {n}",
    InstrumentType.EMERGENCY_DECREE: "D.U. N.° {n}",
    InstrumentType.SINGLE_ORDERED_TEXT: "TUO de la Ley N.° {n}",
    InstrumentType.REGULATION: "Reglamento N.° {n}",
    InstrumentType.RESOLUTION: "Resolución N.° {n}",
    InstrumentType.REGIONAL_ORDINANCE: "Ordenanza Regional N.° {n}",
    InstrumentType.OTHER: "Norma N.° {n}",
}
_FORMAL_NAMES = {
    InstrumentType.LAW: "Ley N.° {n}",
    InstrumentType.SUPREME_DECREE: "Decreto Supremo N.° {n}",
    InstrumentType.LEGISLATIVE_DECREE: "Decreto Legislativo N.° {n}",
    InstrumentType.EMERGENCY_DECREE: "Decreto de Urgencia N.° {n}",
    InstrumentType.SINGLE_ORDERED_TEXT: "Texto Único Ordenado de la Ley N.° {n}",
    InstrumentType.REGULATION: "Reglamento N.° {n}",
    InstrumentType.RESOLUTION: "Resolución N.° {n}",
    InstrumentType.REGIONAL_ORDINANCE: "Ordenanza Regional N.° {n}",
    InstrumentType.OTHER: "Norma N.° {n}",
}
_VERIFICATION = {
    VerificationStatus.VERIFIED_CURRENT: "texto verificado como vigente",
    VerificationStatus.UNVERIFIED: "edición no verificada frente a la fuente oficial",
    VerificationStatus.PENDING_REVIEW: "edición en revisión jurídica (no verificada)",
    VerificationStatus.SUPERSEDED: "edición sustituida por una posterior",
    VerificationStatus.REPEALED: "norma derogada",
    VerificationStatus.UNKNOWN: "vigencia desconocida (no verificada)",
}
_SINGULAR = {
    "complementarias": "Complementaria",
    "transitorias": "Transitoria",
    "derogatorias": "Derogatoria",
    "finales": "Final",
    "complementaria": "Complementaria",
    "transitoria": "Transitoria",
    "derogatoria": "Derogatoria",
    "final": "Final",
}
_DOT = "."


@dataclass(frozen=True, slots=True)
class CitationSubject:
    """What the formatter needs to know about the norm, its edition and the cited text."""

    instrument_type: InstrumentType
    number: str
    title: str
    edition_label: str
    consolidated_as_of: date | None
    verification_status: VerificationStatus
    source_file_name: str
    page_start: int
    page_end: int
    superseded_by: LegalEvent | None = None  # set when the cited text is a replaced revision


@dataclass(frozen=True, slots=True)
class Citation:
    short: str
    formal: str


def describe_location(path: str) -> str:
    """``articulo:2/literal:e`` → ``art. 2, lit. e)``; ``disposiciones:finales/tercera`` → ``Tercera
    Disposición Final``."""
    parts: list[str] = []
    for index, segment in enumerate(split_path(path)):
        parts.extend(_describe_segment(segment, split_path(path)[: index + 1]))
    return ", ".join(parts)


def short_citation(subject: CitationSubject, path: str) -> str:
    name = _SHORT_NAMES[subject.instrument_type].format(n=subject.number)
    location = describe_location(path)
    text = f"{name}, {location}" if location else name
    return f"{text} (texto sustituido)" if subject.superseded_by else text


def format_citation(subject: CitationSubject, path: str) -> Citation:
    formal_name = _FORMAL_NAMES[subject.instrument_type].format(n=subject.number)
    location = describe_location(path)
    head = f"{formal_name}, {subject.title}"
    if location:
        head = f"{head}, {location}"
    edition = f"Edición: {subject.edition_label}"
    if subject.consolidated_as_of:
        edition += f", actualizada al {_date(subject.consolidated_as_of)}"
    parts = [head, f"{edition} ({_VERIFICATION[subject.verification_status]})"]
    if subject.superseded_by:
        parts.append(
            f"Texto sustituido por {subject.superseded_by.source}"
            + (
                f" ({_date(subject.superseded_by.published_on)})"
                if subject.superseded_by.published_on
                else ""
            )
            + ": no vigente"
        )
    parts.append(
        f"Fuente: {subject.source_file_name}, {_pages(subject.page_start, subject.page_end)} del PDF"
    )
    return Citation(short_citation(subject, path), ". ".join(parts) + ".")


def _pages(first: int, last: int) -> str:
    return f"p. {first}" if first == last else f"pp. {first}-{last}"


def _date(value: date) -> str:
    return value.strftime("%d-%m-%Y")


def _describe_segment(segment: PathSegment, so_far: list[PathSegment]) -> list[str]:
    key, value = segment.key, segment.value
    if key == "articulo":
        return [f"art. {value}"]
    if key == "numeral":
        previous = so_far[-2] if len(so_far) > 1 else None
        dotted = _DOT in value
        if dotted:
            return [f"num. {value}"]
        under_dotted = previous is not None and previous.key == "numeral" and _DOT in previous.value
        return [f"inc. {value}" if under_dotted else f"num. {value}"]
    if key == "literal":
        return [f"lit. {value})"]
    if key == "anexo":
        return [f"Anexo {value.upper()}"]
    if key == "titulo":
        return [f"Título {_roman_or_word(value)}"]
    if key == "capitulo":
        return [f"Capítulo {value}"]
    if key == "subcapitulo":
        return [f"Subcapítulo {value}"]
    if key == "seccion":
        return [f"Sección {value.capitalize()}"]
    if key == "disposiciones":
        return []  # named together with the ordinal that follows
    if key == "disposicion":
        return [f"{_ordinal(value)} Disposición"]
    if key == "":
        previous = so_far[-2] if len(so_far) > 1 else None
        if previous is not None and previous.key == "disposiciones":
            group = " ".join(
                _SINGULAR.get(word, word.capitalize()) for word in previous.value.split("-")
            )
            return [f"{_ordinal(value)} Disposición {group}"]
    return [f"{key}:{value}" if key else value]


def _roman_or_word(value: str) -> str:
    return (
        value.capitalize()
        if (value.isalpha() and not value.isupper()) or value == "PRELIMINAR"
        else value
    )


def _ordinal(slug: str) -> str:
    words = [word.capitalize() for word in slug.split("-")]
    text = " ".join(words)
    return text.replace("Unica", "Única").replace("Decimo", "Décimo").replace("Decima", "Décima")
