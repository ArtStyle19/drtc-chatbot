from collections.abc import Sequence

import pytest

from drtc_chatbot.contexts.legal_corpus.application.queries.list_legal_instruments import (
    ListLegalInstruments,
)
from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import LegalInstrument
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import VerificationStatus
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.unit.legal_corpus.factories import a_version, an_instrument

ANONYMOUS = Actor(actor_id="anonymous", kind=ActorKind.ANONYMOUS)


class InMemoryCatalog:
    """Fake adapter for the LegalInstrumentCatalog port."""

    def __init__(self, *instruments: LegalInstrument) -> None:
        self._instruments = instruments

    async def list_instruments(self) -> Sequence[LegalInstrument]:
        return self._instruments


@pytest.mark.spec("001-FR-001")
async def test_lists_every_instrument_with_its_reference_edition() -> None:
    instrument = an_instrument(a_version("ley-27181@2020-05"), a_version("ley-27181@2026-11"))
    use_case = ListLegalInstruments(InMemoryCatalog(instrument))

    [summary] = await use_case.execute(ANONYMOUS)

    assert summary.instrument_id == "ley-27181"
    assert summary.current_edition.version_id == "ley-27181@2026-11"
    assert summary.version_count == 2


@pytest.mark.spec("001-FR-003")
async def test_summaries_never_mark_an_unverified_edition_as_current() -> None:
    use_case = ListLegalInstruments(
        InMemoryCatalog(an_instrument(a_version(status=VerificationStatus.UNVERIFIED)))
    )

    [summary] = await use_case.execute(ANONYMOUS)

    assert summary.current_edition.verification_status is VerificationStatus.UNVERIFIED
    assert summary.current_edition.may_be_presented_as_current is False


async def test_an_empty_catalog_returns_an_empty_list() -> None:
    assert await ListLegalInstruments(InMemoryCatalog()).execute(ANONYMOUS) == []
