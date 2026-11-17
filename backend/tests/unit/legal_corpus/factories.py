"""Builders for legal-corpus domain objects (keep tests short and intention-revealing)."""

from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import (
    InstrumentVersion,
    LegalInstrument,
    SourceDocumentRef,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentId,
    InstrumentType,
    PageRange,
    PageRole,
    PageSection,
    Sha256Digest,
    VerificationStatus,
    VersionId,
)


def a_version(
    version_id: str = "ley-27181@2020-05",
    *,
    status: VerificationStatus = VerificationStatus.UNVERIFIED,
    page_count: int = 36,
    sections: tuple[PageSection, ...] = (),
) -> InstrumentVersion:
    return InstrumentVersion(
        version_id=VersionId(version_id),
        edition_label="Compilación de prueba",
        verification_status=status,
        source=SourceDocumentRef(
            source_id="src-test",
            file_name="test.pdf",
            sha256=Sha256Digest("a" * 64),
            page_count=page_count,
        ),
        page_sections=sections,
    )


def an_instrument(*versions: InstrumentVersion) -> LegalInstrument:
    return LegalInstrument(
        InstrumentId("ley-27181"),
        instrument_type=InstrumentType.LAW,
        number="27181",
        title="Ley General de Transporte y Tránsito Terrestre",
        short_name="Ley 27181 (LGTTT)",
        issuing_authority="Congreso de la República",
        publication_date=None,
        versions=versions or (a_version(),),
    )


def section(role: PageRole, first: int, last: int) -> PageSection:
    return PageSection(role=role, pages=PageRange(first, last))
