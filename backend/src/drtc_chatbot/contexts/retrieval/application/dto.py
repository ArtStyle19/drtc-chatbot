"""Results of the reference search (plain, framework-free)."""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from drtc_chatbot.contexts.retrieval.application.ports import Segment


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


class SearchMode(StrEnum):
    HYBRID = "hybrid"  # reference first, then words and meaning fused
    LEXICAL = "lexical"  # reference + words
    VECTOR = "vector"  # reference + meaning


# Why a search answered with less than it was asked for (the person is told; nothing fails).
DEGRADED_VECTOR_UNAVAILABLE = "vector_unavailable"  # no key, provider error or too slow
DEGRADED_VECTOR_NOT_INDEXED = "vector_not_indexed"  # the vectors have not been computed yet


@dataclass(frozen=True, slots=True)
class MatchedPassage:
    path: str
    citation: str
    page_start: int
    page_end: int
    snippet: tuple[Segment, ...]


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A reading unit (article, disposition or annex) that matches, with its best passage."""

    instrument_id: str
    instrument_short_name: str
    version_id: str
    edition_label: str
    verification_status: str
    unit_path: str
    path: str  # the best passage inside the unit (what the reader highlights)
    kind: str
    label: str
    title: str | None
    citation: str
    page_start: int
    page_end: int
    snippet: tuple[Segment, ...]
    matched: tuple[MatchedPassage, ...]  # passages of the unit that matched, best first
    via: tuple[str, ...]  # reference | lexical | vector
    score: float
    debug: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SearchFacet:
    instrument_id: str
    instrument_short_name: str
    count: int


@dataclass(frozen=True, slots=True)
class SearchResponse:
    query: str
    mode: SearchMode
    degraded: tuple[str, ...]
    total: int
    results: tuple[SearchResult, ...]
    facets: tuple[SearchFacet, ...]
    reference: str | None  # what was understood as a reference, e.g. "art. 5"
    latency_ms: float
