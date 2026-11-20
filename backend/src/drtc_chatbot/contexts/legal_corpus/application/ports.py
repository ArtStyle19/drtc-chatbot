"""Ports (interfaces) the legal-corpus use cases depend on. Adapters live in infrastructure."""

from collections.abc import Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionContext,
    IndexRow,
    ManifestSnapshot,
    OutlineEntry,
    ProvisionDetail,
    ProvisionPage,
    PublishDraft,
    PublishOutcome,
    RawNode,
    SourceRef,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import Approval
from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import LegalInstrument
from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind


class LegalInstrumentCatalog(Protocol):
    """Read port: every legal instrument known to the corpus, in a stable order."""

    async def list_instruments(self) -> Sequence[LegalInstrument]: ...


class ManifestReader(Protocol):
    """Reads the corpus manifest (the seed of instruments, versions and source documents)."""

    def read(self) -> ManifestSnapshot: ...


class InstrumentRegistry(Protocol):
    """Write port: upserts instruments, versions and sources from the manifest (idempotent)."""

    async def sync(self, snapshot: ManifestSnapshot) -> None: ...


class ProvisionStore(Protocol):
    """Stores the provisions of an instrument version and serves them to readers."""

    async def publish(self, draft: PublishDraft, *, at: datetime) -> PublishOutcome: ...

    async def list_provisions(
        self,
        instrument_id: str,
        *,
        version_id: str | None,
        kind: ProvisionKind | None,
        parent_path: str | None,
        limit: int,
        offset: int,
    ) -> ProvisionPage | None:
        """Current provisions of an APPROVED version; None if there is no approved version."""
        ...

    async def get_provision(self, provision_id: str) -> ProvisionDetail | None:
        """A provision of an approved version with its revision history, or None."""
        ...


class ApprovalStore(Protocol):
    async def get_approval(self, version_id: str) -> Approval | None: ...

    async def set_approval(self, version_id: str, approval: Approval) -> None: ...

    async def has_provisions(self, version_id: str) -> bool: ...


class ReadingStore(Protocol):
    """Read-only access to the approved editions for the reader (outline, units, source, index)."""

    async def get_edition(
        self, instrument_id: str, version_id: str | None
    ) -> EditionContext | None:
        """The approved edition (the latest one when ``version_id`` is None), or None."""
        ...

    async def get_outline_entries(self, version_id: str) -> Sequence[OutlineEntry]: ...

    async def get_reading_nodes(self, version_id: str, unit_path: str) -> Sequence[RawNode]:
        """Current provisions at/below ``unit_path`` with history, notes, flags (document order)."""
        ...

    async def get_child_entries(
        self, version_id: str, parent_path: str
    ) -> Sequence[OutlineEntry]: ...

    async def get_source_ref(self, version_id: str) -> SourceRef | None:
        """The source file of an APPROVED edition, or None."""
        ...

    async def get_index_rows(self, version_id: str) -> Sequence[IndexRow]: ...


class DocumentStorage(Protocol):
    """Where the original PDFs live. Implementations must verify the SHA-256 before returning."""

    def locate(self, file_name: str, sha256: str) -> tuple[Path, int]:
        """Path and size of the verified file. Raises InvariantViolationError if it was altered
        and NotFoundError if it is missing."""
        ...
