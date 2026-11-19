"""Use case: the approved edition of every norm (name, edition and verification status).

A light read model for what must show next to a search result: which edition it comes from and how
much is known about its validity. It is the LATEST APPROVED edition, which is not always the latest
registered one (a newer edition may still be waiting for approval).
"""

from drtc_chatbot.contexts.legal_corpus.application.dto import EditionContext
from drtc_chatbot.contexts.legal_corpus.application.ports import (
    LegalInstrumentCatalog,
    ReadingStore,
)
from drtc_chatbot.shared_kernel.application import Actor


class ListApprovedEditions:
    def __init__(self, catalog: LegalInstrumentCatalog, store: ReadingStore) -> None:
        self._catalog = catalog
        self._store = store

    async def execute(self, actor: Actor) -> list[EditionContext]:
        del actor
        editions = []
        for instrument in await self._catalog.list_instruments():
            edition = await self._store.get_edition(str(instrument.id), None)
            if edition is not None:  # no approved edition yet: nothing to read or search
                editions.append(edition)
        return editions
