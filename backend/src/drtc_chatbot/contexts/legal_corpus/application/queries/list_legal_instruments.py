"""Use case: list the norms of the corpus with the status of their latest edition."""

from drtc_chatbot.contexts.legal_corpus.application.dto import LegalInstrumentSummary
from drtc_chatbot.contexts.legal_corpus.application.ports import LegalInstrumentCatalog
from drtc_chatbot.shared_kernel.application import Actor


class ListLegalInstruments:
    """Query use case (spec 001, FR-001..FR-003)."""

    def __init__(self, catalog: LegalInstrumentCatalog) -> None:
        self._catalog = catalog

    async def execute(self, actor: Actor) -> list[LegalInstrumentSummary]:
        # Authorization hook: the catalog is readable by every actor, anonymous included (ADR-0007).
        del actor
        instruments = await self._catalog.list_instruments()
        return [LegalInstrumentSummary.from_instrument(instrument) for instrument in instruments]
