import pytest

from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentId,
    PageRange,
    Sha256Digest,
    VerificationStatus,
    VersionId,
)
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


@pytest.mark.spec("001-FR-003")
@pytest.mark.parametrize("status", [s for s in VerificationStatus if s.value != "verified_current"])
def test_only_a_verified_text_may_be_presented_as_current(status: VerificationStatus) -> None:
    assert VerificationStatus.VERIFIED_CURRENT.may_be_presented_as_current
    assert not status.may_be_presented_as_current


def test_unknown_status_is_not_treated_as_out_of_force_either() -> None:
    assert not VerificationStatus.UNKNOWN.is_known_to_be_out_of_force
    assert VerificationStatus.REPEALED.is_known_to_be_out_of_force


@pytest.mark.parametrize("value", ["Ley 27181", "ley_27181", "", "-ley"])
def test_instrument_id_must_be_a_slug(value: str) -> None:
    with pytest.raises(InvariantViolationError):
        InstrumentId(value)


def test_version_id_accepts_edition_qualifiers() -> None:
    assert str(VersionId("tuo-ley-27444@ds-004-2019-jus-ed2021")) == (
        "tuo-ley-27444@ds-004-2019-jus-ed2021"
    )


def test_sha256_digest_is_validated() -> None:
    with pytest.raises(InvariantViolationError):
        Sha256Digest("not-a-digest")


@pytest.mark.parametrize(("first", "last"), [(0, 3), (5, 4)])
def test_page_range_rejects_invalid_bounds(first: int, last: int) -> None:
    with pytest.raises(InvariantViolationError):
        PageRange(first, last)


def test_page_range_is_inclusive() -> None:
    pages = PageRange(23, 68)
    assert pages.contains(23)
    assert pages.contains(68)
    assert not pages.contains(69)
