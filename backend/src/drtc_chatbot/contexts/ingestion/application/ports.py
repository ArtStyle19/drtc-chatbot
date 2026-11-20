"""Ports the ingestion use cases depend on. Adapters live in infrastructure."""

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from drtc_chatbot.contexts.ingestion.domain.job import IngestionJob
from drtc_chatbot.contexts.ingestion.domain.parsing.model import ParseResult, SourceLine


@dataclass(frozen=True, slots=True)
class IngestionTarget:
    """One instrument version to ingest: its file, fingerprint, normative pages and parser."""

    version_id: str
    source_file: Path
    sha256: str
    page_count: int
    normative_pages: tuple[tuple[int, int], ...]
    parser: str | None


@dataclass(frozen=True, slots=True)
class PublicationResult:
    changed: bool
    current: int
    superseded: int


@dataclass(frozen=True, slots=True)
class ApprovalOutcome:
    mode: str
    approved_by: str


class PdfTextExtractor(Protocol):
    def extract(self, pdf_path: Path, pages: Sequence[int]) -> list[SourceLine]: ...


class CorpusGateway(Protocol):
    """The ingestion's only door into the legal corpus context."""

    async def sync_manifest(self) -> int: ...

    async def targets(self) -> list[IngestionTarget]: ...

    async def publish(
        self, target: IngestionTarget, result: ParseResult, content_digest: str
    ) -> PublicationResult: ...

    async def approve_automatically(self, version_id: str) -> ApprovalOutcome | None: ...

    async def approve(self, version_id: str, reviewer: str) -> ApprovalOutcome: ...


class IngestionJobRepository(Protocol):
    async def save(self, job: IngestionJob) -> None: ...

    async def latest(self, version_id: str) -> IngestionJob | None: ...
