"""Ports (interfaces) the legal-corpus use cases depend on. Adapters live in infrastructure."""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    ManifestSnapshot,
    ProvisionDetail,
    ProvisionPage,
    PublishDraft,
    PublishOutcome,
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
