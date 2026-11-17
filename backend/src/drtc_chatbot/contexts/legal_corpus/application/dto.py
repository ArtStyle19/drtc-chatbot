"""Data transfer objects returned by the legal-corpus use cases (plain, framework-free)."""

from dataclasses import dataclass
from datetime import date

from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import (
    InstrumentVersion,
    LegalInstrument,
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
        )
