"""Data transfer objects of the legal-corpus use cases (plain, framework-free)."""

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from drtc_chatbot.contexts.legal_corpus.domain.approval import ApprovalMode, ApprovalStatus
from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import (
    InstrumentVersion,
    LegalInstrument,
)
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    LegalEvent,
    PageBox,
    ProvisionKind,
    ProvisionRevision,
    RevisionStatus,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    VerificationStatus,
)


@dataclass(frozen=True, slots=True)
class EditionSummary:
    version_id: str
    edition_label: str
    consolidated_as_of: date | None
    verification_status: VerificationStatus
    may_be_presented_as_current: bool
    page_count: int
    alerts: tuple[str, ...]
    approval_status: ApprovalStatus
    approval_mode: ApprovalMode | None
    provision_count: int

    @classmethod
    def from_version(cls, version: InstrumentVersion) -> EditionSummary:
        return cls(
            version_id=str(version.version_id),
            edition_label=version.edition_label,
            consolidated_as_of=version.consolidated_as_of,
            verification_status=version.verification_status,
            may_be_presented_as_current=version.verification_status.may_be_presented_as_current,
            page_count=version.source.page_count,
            alerts=version.alerts,
            approval_status=version.approval.status,
            approval_mode=version.approval.mode,
            provision_count=version.provision_count,
        )


@dataclass(frozen=True, slots=True)
class LegalInstrumentSummary:
    instrument_id: str
    instrument_type: InstrumentType
    number: str
    title: str
    short_name: str
    issuing_authority: str
    publication_date: date | None
    current_edition: EditionSummary
    version_count: int
    aliases: tuple[str, ...] = ()

    @classmethod
    def from_instrument(cls, instrument: LegalInstrument) -> LegalInstrumentSummary:
        return cls(
            instrument_id=str(instrument.id),
            instrument_type=instrument.instrument_type,
            number=instrument.number,
            title=instrument.title,
            short_name=instrument.short_name,
            issuing_authority=instrument.issuing_authority,
            publication_date=instrument.publication_date,
            current_edition=EditionSummary.from_version(instrument.latest_version),
            version_count=len(instrument.versions),
            aliases=instrument.aliases,
        )


# ----------------------------------------------------------------------------- manifest sync
@dataclass(frozen=True, slots=True)
class ManifestSource:
    source_id: str
    file: Path
    file_name: str
    sha256: str
    page_count: int


@dataclass(frozen=True, slots=True)
class ManifestVersion:
    version_id: str
    instrument_id: str
    ordinal: int
    source_id: str
    edition_label: str
    consolidated_as_of: date | None
    consolidation_note: str | None
    verification_status: VerificationStatus
    parser: str | None
    page_sections: tuple[tuple[str, int, int], ...]
    alerts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ManifestInstrument:
    instrument_id: str
    instrument_type: InstrumentType
    number: str
    title: str
    short_name: str
    issuing_authority: str
    publication_date: date | None
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ManifestSnapshot:
    sources: tuple[ManifestSource, ...]
    instruments: tuple[ManifestInstrument, ...]
    versions: tuple[ManifestVersion, ...]


@dataclass(frozen=True, slots=True)
class IngestionTarget:
    """What the ingestion needs to know to process one instrument version."""

    version_id: str
    instrument_id: str
    source_file: Path
    sha256: str
    page_count: int
    normative_pages: tuple[tuple[int, int], ...]
    parser: str | None


# ----------------------------------------------------------------------------- publishing
@dataclass(frozen=True, slots=True)
class NoteDraft:
    kind: str
    text: str
    page: int
    path: str | None = None


@dataclass(frozen=True, slots=True)
class EventRequest:
    kind: str
    source: str
    published_on: date | None = None


@dataclass(frozen=True, slots=True)
class RevisionRequest:
    """One revision of one provision, as parsed (plain values; validated by the use case)."""

    path: str
    kind: str
    label: str
    title: str | None
    parent_path: str | None
    text: str
    revision: int
    status: str
    page_start: int
    page_end: int
    ordinal: int
    boxes: tuple[tuple[int, float, float, float, float], ...] = ()
    event: EventRequest | None = None
    flags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PublishRequest:
    version_id: str
    source_sha256: str
    page_count: int
    content_digest: str
    revisions: tuple[RevisionRequest, ...]
    notes: tuple[NoteDraft, ...] = ()


@dataclass(frozen=True, slots=True)
class PublishDraft:
    """The provisions (all revisions) and notes parsed from one version's source document."""

    version_id: str
    source_sha256: str
    page_count: int
    content_digest: str
    revisions: tuple[ProvisionRevision, ...]
    notes: tuple[NoteDraft, ...] = ()


@dataclass(frozen=True, slots=True)
class PublishOutcome:
    version_id: str
    changed: bool
    revisions: int
    current: int
    superseded: int


# ----------------------------------------------------------------------------- reading
@dataclass(frozen=True, slots=True)
class ProvisionSummary:
    provision_id: str
    path: str
    kind: ProvisionKind
    label: str
    title: str | None
    parent_path: str | None
    text: str
    page_start: int
    page_end: int
    ordinal: int
    revision: int
    revision_count: int
    event: LegalEvent | None


@dataclass(frozen=True, slots=True)
class ProvisionPage:
    instrument_id: str
    version_id: str
    edition_label: str
    verification_status: VerificationStatus
    approval_mode: ApprovalMode
    total: int
    items: tuple[ProvisionSummary, ...]


@dataclass(frozen=True, slots=True)
class ProvisionRevisionDetail:
    revision: int
    status: RevisionStatus
    title: str | None
    text: str
    page_start: int
    page_end: int
    boxes: tuple[PageBox, ...] = ()
    event: LegalEvent | None = None


@dataclass(frozen=True, slots=True)
class ProvisionDetail:
    provision_id: str
    instrument_id: str
    version_id: str
    edition_label: str
    verification_status: VerificationStatus
    approval_mode: ApprovalMode
    path: str
    kind: ProvisionKind
    label: str
    parent_path: str | None
    revisions: tuple[ProvisionRevisionDetail, ...] = field(default_factory=tuple)
    notes: tuple[NoteDraft, ...] = field(default_factory=tuple)

    @property
    def current(self) -> ProvisionRevisionDetail | None:
        return next((r for r in self.revisions if r.status is RevisionStatus.CURRENT), None)


@dataclass(frozen=True, slots=True)
class ApprovalResult:
    version_id: str
    mode: ApprovalMode
    approved_by: str
    approved_at: datetime
