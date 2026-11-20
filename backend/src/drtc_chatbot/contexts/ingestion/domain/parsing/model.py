"""Plain data model produced by the parsers (and published to the legal corpus as DTOs)."""

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


class ParsedKind(StrEnum):
    """Kind of structural unit. Values match the legal corpus provision kinds."""

    SECTION = "section"
    TITLE = "title"
    CHAPTER = "chapter"
    ARTICLE = "article"
    NUMERAL = "numeral"
    LITERAL = "literal"
    DISPOSITION = "disposition"
    ANNEX = "annex"

    @property
    def is_container(self) -> bool:
        return self in {ParsedKind.SECTION, ParsedKind.TITLE, ParsedKind.CHAPTER}


class RevisionStatus(StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"


class EventKind(StrEnum):
    SUBSTITUTED = "substituted"
    INCORPORATED = "incorporated"
    MODIFIED = "modified"
    REPEALED = "repealed"


class NoteKind(StrEnum):
    AMENDMENT = "amendment"
    CONCORDANCE = "concordance"
    FOOTNOTE = "footnote"
    PREAMBLE = "preamble"
    EPILOGUE = "epilogue"


@dataclass(frozen=True, slots=True)
class TextBox:
    """Bounding box of a line on a physical PDF page (PDF points, origin bottom-left)."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True, slots=True)
class SourceLine:
    """One line of extracted text with the physical page it came from."""

    page: int
    text: str
    box: TextBox | None = None
    small: bool = False  # set in a smaller type than the body (page footnotes)


@dataclass(frozen=True, slots=True)
class ParsedEvent:
    """Why a revision exists: the norm that substituted, incorporated or repealed the text."""

    kind: EventKind
    source: str
    published_on: date | None = None


@dataclass(frozen=True, slots=True)
class ParsedProvision:
    """One revision of one provision. A replaced provision yields several revisions."""

    path: str
    kind: ParsedKind
    label: str
    title: str | None
    parent_path: str | None
    text: str
    revision: int
    status: RevisionStatus
    page_start: int
    page_end: int
    ordinal: int
    boxes: tuple[TextBox, ...] = ()
    event: ParsedEvent | None = None


@dataclass(frozen=True, slots=True)
class ParsedNote:
    """Editorial material kept for the reviewer: (*) notes, concordances, footnotes."""

    kind: NoteKind
    text: str
    page: int
    path: str | None = None


@dataclass(frozen=True, slots=True)
class Anomaly:
    """Something the parser could not interpret with confidence (never silently dropped)."""

    code: str
    message: str
    page: int
    excerpt: str
    path: str | None = None


@dataclass(frozen=True, slots=True)
class ParseResult:
    provisions: tuple[ParsedProvision, ...] = ()
    notes: tuple[ParsedNote, ...] = ()
    anomalies: tuple[Anomaly, ...] = ()
    metrics: dict[str, int] = field(default_factory=dict)

    def current(self) -> tuple[ParsedProvision, ...]:
        return tuple(p for p in self.provisions if p.status is RevisionStatus.CURRENT)
