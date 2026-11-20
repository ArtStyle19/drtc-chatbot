"""The words arm as a ``Retriever`` (what the evaluation measures; the search builds on the same index)."""

from drtc_chatbot.contexts.retrieval.application.ports import PassageIndex, Retrieval
from drtc_chatbot.contexts.retrieval.domain.evaluation import RankedResult
from drtc_chatbot.contexts.retrieval.domain.query import validate_query
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError

# Several passages of one article are common: ask for more passages than units are needed.
PASSAGES_PER_UNIT = 5
MAX_PASSAGES = 100


class LexicalRetriever:
    name = "lexical"

    def __init__(self, index: PassageIndex) -> None:
        self._index = index

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval:
        del actor
        try:
            query = validate_query(text)
        except InvariantViolationError:
            return Retrieval(())
        hits = await self._index.lexical_search(
            query, instrument_id=None, limit=min(limit * PASSAGES_PER_UNIT, MAX_PASSAGES)
        )
        return Retrieval(
            tuple(
                RankedResult(h.passage.version_id, h.passage.path, h.passage.unit_path, h.score)
                for h in hits
            )
        )
