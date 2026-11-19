"""Ports of the retrieval context. Adapters live in infrastructure."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Protocol

from drtc_chatbot.contexts.retrieval.domain.chunking import PassageText
from drtc_chatbot.contexts.retrieval.domain.evaluation import (
    GoldenQuestion,
    MethodReport,
    RankedResult,
)
from drtc_chatbot.contexts.retrieval.domain.norms import NormInfo
from drtc_chatbot.shared_kernel.application import Actor


@dataclass(frozen=True, slots=True)
class IndexedProvision:
    """A current provision as the reference search sees it (its own types, not the corpus')."""

    path: str
    unit_path: str
    kind: str
    label: str
    title: str | None
    snippet: str
    page_start: int
    citation: str
    parent_path: str | None = None


@dataclass(frozen=True, slots=True)
class IndexedEdition:
    version_id: str
    edition_label: str
    verification_status: str
    entries: tuple[IndexedProvision, ...]

    def match_paths(self) -> list[tuple[IndexedProvision, str]]:
        """Each entry with the path references are matched against.

        An article's own path is ``articulo:5`` and its numerals live under it, but a person may cite
        "art. 5 del título I" or "num. 5.1, título I": the container of the top-level unit is put in
        front, so title and chapter steps can match. Paths that already contain their container
        (chapters, dispositions) are left alone.
        """
        container_of = {e.path: e.parent_path for e in self.entries if e.parent_path}
        result = []
        for entry in self.entries:
            root = entry.path.split("/", maxsplit=1)[0]
            container = container_of.get(root)
            if container and not entry.path.startswith(container + "/") and entry.path != container:
                result.append((entry, f"{container}/{entry.path}"))
            else:
                result.append((entry, entry.path))
        return result


class ProvisionDirectory(Protocol):
    """Anticorruption layer towards the legal corpus (implemented over ``legal_corpus.api``)."""

    async def norms(self, actor: Actor) -> Sequence[NormInfo]: ...

    async def edition(self, actor: Actor, instrument_id: str) -> IndexedEdition | None:
        """Every current provision of the latest APPROVED edition, in document order; or None."""
        ...


@dataclass(frozen=True, slots=True)
class Retrieval:
    """What a retrieval method returned for one text: results best first, and why it was degraded."""

    results: tuple[RankedResult, ...]
    degraded: tuple[str, ...] = ()


class Retriever(Protocol):
    """A way of finding provisions for a text (exact, words, meaning, hybrid): what gets evaluated."""

    name: str

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval: ...


class GoldenSet(Protocol):
    """The reviewed questions the retrieval is measured with (``evaluation/datasets``)."""

    def load(self) -> Sequence[GoldenQuestion]: ...


class EvaluationStore(Protocol):
    """Where the evaluation keeps its reports, its committed baseline and the baseline's changelog."""

    def read_baseline(self) -> Mapping[str, Any]: ...

    def write_baseline(
        self, reports: Iterable[MethodReport], *, dataset: str, recorded_on: date, questions: int
    ) -> Mapping[str, Any]: ...

    def append_changelog(
        self, *, recorded_on: date, reason: str, summary: Mapping[str, str]
    ) -> None: ...

    def write_report(
        self,
        directory: Path,
        label: str,
        *,
        recorded_on: date,
        payload: Mapping[str, Any],
        markdown: str,
    ) -> tuple[Path, Path]: ...


@dataclass(frozen=True, slots=True)
class Segment:
    """A piece of a snippet; ``match`` marks the words that matched the search (never HTML)."""

    text: str
    match: bool = False


@dataclass(frozen=True, slots=True)
class PassageHit:
    """A passage found by one arm of the search, with that arm's score and the matching words."""

    passage: PassageText
    score: float
    snippet: tuple[Segment, ...] = ()


@dataclass(frozen=True, slots=True)
class IndexStats:
    """What a synchronisation did: how many passages were added, changed, removed or already fine."""

    added: int = 0
    changed: int = 0
    removed: int = 0
    unchanged: int = 0

    @property
    def total(self) -> int:
        return self.added + self.changed + self.unchanged


class PassageSource(Protocol):
    """Anticorruption layer: the passages of every APPROVED edition, from the legal corpus."""

    async def passages(self, actor: Actor) -> Sequence[PassageText]: ...


class PassageIndex(Protocol):
    """The derived search index (words now, meaning in the next phase). Rebuildable from the corpus."""

    async def sync(self, passages: Sequence[PassageText]) -> IndexStats:
        """Makes the index contain EXACTLY ``passages``: adds, updates what changed, removes the rest."""
        ...

    async def count(self) -> int: ...

    async def lexical_search(
        self, text: str, *, instrument_id: str | None, limit: int
    ) -> Sequence[PassageHit]:
        """Passages that share words with ``text`` (accent- and plural-insensitive), best first."""
        ...
