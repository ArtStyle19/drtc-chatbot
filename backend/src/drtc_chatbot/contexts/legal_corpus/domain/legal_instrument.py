"""LegalInstrument aggregate (norma) and the objects inside its boundary."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date

from drtc_chatbot.contexts.legal_corpus.domain.approval import Approval
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentId,
    InstrumentType,
    PageRole,
    PageSection,
    Sha256Digest,
    VerificationStatus,
    VersionId,
)
from drtc_chatbot.shared_kernel.domain import AggregateRoot, InvariantViolationError


@dataclass(frozen=True, slots=True)
class SourceDocumentRef:
    """The immutable original file (PDF) a version was taken from."""

    source_id: str
    file_name: str
    sha256: Sha256Digest
    page_count: int

    def __post_init__(self) -> None:
        if self.page_count < 1:
            raise InvariantViolationError("A source document must have at least one page")


@dataclass(frozen=True, slots=True)
class InstrumentVersion:
    """One edition or consolidated text of an instrument (versión / edición).

    Entity inside the LegalInstrument aggregate (identity = ``version_id``), implemented as an
    immutable record: the aggregate root replaces it when its state changes.
    """

    version_id: VersionId
    edition_label: str
    verification_status: VerificationStatus
    source: SourceDocumentRef
    consolidated_as_of: date | None = None
    consolidation_note: str | None = None
    page_sections: tuple[PageSection, ...] = ()
    alerts: tuple[str, ...] = ()
    approval: Approval = field(default_factory=Approval)
    provision_count: int = 0  # current provisions ingested for this version

    def __post_init__(self) -> None:
        if not self.edition_label.strip():
            raise InvariantViolationError("An instrument version needs an edition label")
        for section in self.page_sections:
            if section.pages.last > self.source.page_count:
                raise InvariantViolationError(
                    f"Page section {section.pages.first}-{section.pages.last} exceeds the "
                    f"{self.source.page_count} pages of {self.source.file_name}"
                )

    def role_of_page(self, page: int) -> PageRole | None:
        """Return what a physical page contains, or None when it is not classified."""
        for section in self.page_sections:
            if section.pages.contains(page):
                return section.role
        return None


class LegalInstrument(AggregateRoot[InstrumentId]):
    """A law, decree, regulation or TUO, with every version known to the corpus.

    Versions are ordered from oldest to newest; the last one is the reference edition.
    """

    __slots__ = (
        "_aliases",
        "_instrument_type",
        "_issuing_authority",
        "_number",
        "_publication_date",
        "_short_name",
        "_title",
        "_versions",
    )

    def __init__(
        self,
        instrument_id: InstrumentId,
        *,
        instrument_type: InstrumentType,
        number: str,
        title: str,
        short_name: str,
        issuing_authority: str,
        publication_date: date | None,
        versions: Sequence[InstrumentVersion],
        aliases: Sequence[str] = (),
    ) -> None:
        super().__init__(instrument_id)
        if not title.strip():
            raise InvariantViolationError("A legal instrument needs a title")
        if not versions:
            raise InvariantViolationError(f"{instrument_id} must have at least one version")
        version_ids = [version.version_id for version in versions]
        if len(set(version_ids)) != len(version_ids):
            raise InvariantViolationError(f"{instrument_id} has duplicated version ids")
        self._instrument_type = instrument_type
        self._number = number
        self._title = title
        self._short_name = short_name
        self._issuing_authority = issuing_authority
        self._publication_date = publication_date
        self._versions = tuple(versions)
        self._aliases = tuple(alias.strip() for alias in aliases if alias.strip())

    @property
    def instrument_type(self) -> InstrumentType:
        return self._instrument_type

    @property
    def number(self) -> str:
        return self._number

    @property
    def title(self) -> str:
        return self._title

    @property
    def short_name(self) -> str:
        return self._short_name

    @property
    def issuing_authority(self) -> str:
        return self._issuing_authority

    @property
    def publication_date(self) -> date | None:
        return self._publication_date

    @property
    def aliases(self) -> tuple[str, ...]:
        """Names people use for this norm (acronyms, short titles); used by the reference search."""
        return self._aliases

    @property
    def versions(self) -> tuple[InstrumentVersion, ...]:
        return self._versions

    @property
    def latest_version(self) -> InstrumentVersion:
        return self._versions[-1]

    @property
    def may_be_presented_as_current(self) -> bool:
        """Only a verified latest version may be shown as the law in force."""
        return self.latest_version.verification_status.may_be_presented_as_current
