"""Provisions (disposiciones): structural units of a legal instrument and their revisions."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class ProvisionKind(StrEnum):
    SECTION = "section"
    TITLE = "title"
    CHAPTER = "chapter"
    ARTICLE = "article"
    NUMERAL = "numeral"
    LITERAL = "literal"
    DISPOSITION = "disposition"
    ANNEX = "annex"


class RevisionStatus(StrEnum):
    """A text is current, or was superseded by a later norm (never overwritten)."""

    CURRENT = "current"
    SUPERSEDED = "superseded"


class EventKind(StrEnum):
    SUBSTITUTED = "substituted"
    INCORPORATED = "incorporated"
    MODIFIED = "modified"
    REPEALED = "repealed"


@dataclass(frozen=True, slots=True)
class LegalEvent:
    """Which norm produced a revision and when (best effort, from the editorial notes)."""

    kind: EventKind
    source: str
    published_on: date | None = None


@dataclass(frozen=True, slots=True)
class PageBox:
    """Where a line of the provision sits on a physical page (for the future highlighter)."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float


@dataclass(frozen=True, slots=True)
class ProvisionRevision:
    """One revision of one provision's text inside one instrument version."""

    path: str
    kind: ProvisionKind
    label: str
    title: str | None
    parent_path: str | None
    text: str
    revision: int
    status: RevisionStatus
    page_start: int
    page_end: int
    ordinal: int
    boxes: tuple[PageBox, ...] = ()
    event: LegalEvent | None = None


def validate_revision_set(revisions: Sequence[ProvisionRevision], *, page_count: int) -> None:
    """Invariants of the provisions of one instrument version.

    * at most ONE current revision per structural path (never two texts in force at once);
    * revisions of a path are numbered 1..n without gaps and only the last one may be current;
    * every parent path exists; pages lie inside the source document.
    """
    by_path: dict[str, list[ProvisionRevision]] = {}
    for revision in revisions:
        if not 1 <= revision.page_start <= revision.page_end <= page_count:
            raise InvariantViolationError(
                f"{revision.path} r{revision.revision}: pages "
                f"{revision.page_start}-{revision.page_end} "
                f"are outside the {page_count} pages of the source document"
            )
        by_path.setdefault(revision.path, []).append(revision)
    for path, items in by_path.items():
        numbers = sorted(item.revision for item in items)
        if numbers != list(range(1, len(items) + 1)):
            raise InvariantViolationError(f"{path}: revisions must be numbered 1..n without gaps")
        current = [item for item in items if item.status is RevisionStatus.CURRENT]
        if len(current) > 1:
            raise InvariantViolationError(f"{path}: more than one current revision")
        if current and current[0].revision != max(numbers):
            raise InvariantViolationError(f"{path}: only the latest revision can be current")
    for revision in revisions:
        if revision.parent_path is not None and revision.parent_path not in by_path:
            raise InvariantViolationError(f"{revision.path}: unknown parent {revision.parent_path}")
