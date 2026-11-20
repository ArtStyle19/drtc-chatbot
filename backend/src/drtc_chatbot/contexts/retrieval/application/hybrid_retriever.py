"""The whole content search (reference, words and meaning fused) as a ``Retriever``."""

from drtc_chatbot.contexts.retrieval.application.dto import SearchMode
from drtc_chatbot.contexts.retrieval.application.ports import Retrieval
from drtc_chatbot.contexts.retrieval.application.search_passages import SearchPassages
from drtc_chatbot.contexts.retrieval.domain.evaluation import RankedResult
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class HybridRetriever:
    name = "hybrid"

    def __init__(self, search: SearchPassages) -> None:
        self._search = search

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval:
        try:
            response = await self._search.execute(actor, text, limit=limit, mode=SearchMode.HYBRID)
        except InvariantViolationError:
            return Retrieval(())
        results: list[RankedResult] = []
        for unit in response.results:
            # every passage of the unit that matched, best first (the same shape the words arm gives)
            paths = [m.path for m in unit.matched] or [unit.path]
            results.extend(
                RankedResult(unit.version_id, path, unit.unit_path, unit.score) for path in paths
            )
        return Retrieval(tuple(results), degraded=response.degraded)
