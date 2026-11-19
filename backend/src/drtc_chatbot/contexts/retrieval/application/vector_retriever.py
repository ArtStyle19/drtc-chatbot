"""The meaning arm as a ``Retriever`` (what the evaluation measures)."""

from drtc_chatbot.contexts.retrieval.application.lexical_retriever import (
    MAX_PASSAGES,
    PASSAGES_PER_UNIT,
)
from drtc_chatbot.contexts.retrieval.application.ports import (
    EmbeddingProvider,
    EmbeddingPurpose,
    PassageIndex,
    Retrieval,
)
from drtc_chatbot.contexts.retrieval.domain.errors import EmbeddingUnavailableError
from drtc_chatbot.contexts.retrieval.domain.evaluation import RankedResult
from drtc_chatbot.contexts.retrieval.domain.query import validate_query
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class VectorRetriever:
    name = "vector"

    def __init__(self, index: PassageIndex, provider: EmbeddingProvider | None) -> None:
        self._index = index
        self._provider = provider

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval:
        del actor
        if self._provider is None:
            # An evaluation of the meaning arm without a provider would score zeros silently: refuse.
            raise EmbeddingUnavailableError(
                "No hay proveedor de significado configurado (DRTC_OPENAI_API_KEY o DRTC_GEMINI_API_KEY)"
            )
        try:
            query = validate_query(text)
        except InvariantViolationError:
            return Retrieval(())
        batch = await self._provider.embed([query], purpose=EmbeddingPurpose.QUERY)
        hits = await self._index.vector_search(
            self._provider.model,
            batch.vectors[0],
            instrument_id=None,
            limit=min(limit * PASSAGES_PER_UNIT, MAX_PASSAGES),
        )
        return Retrieval(
            tuple(
                RankedResult(h.passage.version_id, h.passage.path, h.passage.unit_path, h.score)
                for h in hits
            )
        )
