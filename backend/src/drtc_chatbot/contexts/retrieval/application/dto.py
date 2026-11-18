"""Results of the reference search (plain, framework-free)."""

from dataclasses import dataclass
from enum import StrEnum


class LookupStatus(StrEnum):
    RESOLVED = "resolved"  # exactly one thing matches
    AMBIGUOUS = "ambiguous"  # several match: the person chooses (we never choose for them)
    NOT_FOUND = "not_found"  # we understood the reference, but it does not exist
    UNRECOGNIZED = "unrecognized"  # the text is not a reference


@dataclass(frozen=True, slots=True)
class LookupHit:
    instrument_id: str
    instrument_short_name: str
    instrument_title: str
    citation: str  # short citation; for a whole norm, its short name
    version_id: str | None = None
    edition_label: str | None = None
    verification_status: str | None = None
    path: str | None = None  # None = the norm itself
    unit_path: str | None = None
    kind: str | None = None
    label: str | None = None
    title: str | None = None
    snippet: str | None = None
    page_start: int | None = None


@dataclass(frozen=True, slots=True)
class LookupResult:
    status: LookupStatus
    query: str
    message: str
    reference: str | None  # what we understood, e.g. "art. 2, lit. e)"
    norms: tuple[str, ...]  # short names of the norms we understood
    total: int
    hits: tuple[LookupHit, ...]
    ignored_text: str | None = None  # words that were not part of any reference
