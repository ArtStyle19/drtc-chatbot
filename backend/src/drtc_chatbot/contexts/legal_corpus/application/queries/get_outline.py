"""Use case: the table of contents of an approved edition of a norm."""

from drtc_chatbot.contexts.legal_corpus.application.dto import Outline
from drtc_chatbot.contexts.legal_corpus.application.ports import ReadingStore
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import NotFoundError


class GetOutline:
    def __init__(self, store: ReadingStore) -> None:
        self._store = store

    async def execute(
        self, actor: Actor, instrument_id: str, *, version_id: str | None = None
    ) -> Outline:
        del actor  # readable by every actor, anonymous included (ADR-0007)
        edition = await self._store.get_edition(instrument_id, version_id)
        if edition is None:
            raise NotFoundError(f"{instrument_id} has no approved edition")
        return Outline(edition, tuple(await self._store.get_outline_entries(edition.version_id)))
