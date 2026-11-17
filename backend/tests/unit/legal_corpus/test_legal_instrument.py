import pytest

from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import LegalInstrument
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentId,
    InstrumentType,
    PageRole,
    VerificationStatus,
)
from drtc_chatbot.shared_kernel.domain import InvariantViolationError
from tests.unit.legal_corpus.factories import a_version, an_instrument, section


def test_latest_version_is_the_reference_edition() -> None:
    old = a_version("ley-27181@2020-05")
    new = a_version("ley-27181@2026-11", status=VerificationStatus.VERIFIED_CURRENT)

    instrument = an_instrument(old, new)

    assert instrument.latest_version is new
    assert instrument.may_be_presented_as_current


@pytest.mark.spec("001-FR-003")
def test_an_unverified_instrument_is_not_presented_as_current() -> None:
    assert not an_instrument(
        a_version(status=VerificationStatus.UNVERIFIED)
    ).may_be_presented_as_current


def test_an_instrument_needs_at_least_one_version() -> None:
    with pytest.raises(InvariantViolationError):
        LegalInstrument(
            InstrumentId("ley-27181"),
            instrument_type=InstrumentType.LAW,
            number="27181",
            title="Ley General de Transporte y Tránsito Terrestre",
            short_name="Ley 27181",
            issuing_authority="Congreso de la República",
            publication_date=None,
            versions=[],
        )


def test_version_ids_are_unique_within_an_instrument() -> None:
    with pytest.raises(InvariantViolationError):
        an_instrument(a_version("ley-27181@x"), a_version("ley-27181@x"))


def test_explanatory_pages_are_distinguished_from_normative_text() -> None:
    version = a_version(
        page_count=292,
        sections=(section(PageRole.EXPLANATORY, 23, 68), section(PageRole.NORMATIVE, 71, 284)),
    )

    assert version.role_of_page(30) is PageRole.EXPLANATORY
    assert version.role_of_page(100) is PageRole.NORMATIVE
    assert version.role_of_page(10) is None


def test_page_sections_cannot_exceed_the_source_document() -> None:
    with pytest.raises(InvariantViolationError):
        a_version(page_count=36, sections=(section(PageRole.NORMATIVE, 1, 40),))
