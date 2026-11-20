"""Use case: make the search index reflect the approved corpus (spec 004, FR-016).

Idempotent and cheap to repeat: a passage is only rewritten when what is indexed for it changed, and
what is no longer in an approved edition (a replaced text, a withdrawn edition) disappears.
"""

from drtc_chatbot.contexts.retrieval.application.ports import (
    IndexStats,
    PassageIndex,
    PassageSource,
)
from drtc_chatbot.shared_kernel.application import Actor


class BuildIndex:
    def __init__(self, source: PassageSource, index: PassageIndex) -> None:
        self._source = source
        self._index = index

    async def execute(self, actor: Actor) -> IndexStats:
        passages = await self._source.passages(actor)
        return await self._index.sync(passages)
