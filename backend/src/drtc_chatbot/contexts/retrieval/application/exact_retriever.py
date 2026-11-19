"""The exact arm as a ``Retriever``: provisions that a legal reference in the text identifies.

It reuses ``LookupReference`` (spec 003), so what is measured is exactly what the person gets. A text
without a reference yields nothing; an ambiguous reference yields every candidate (we never choose).
"""

from drtc_chatbot.contexts.retrieval.application.lookup_reference import LookupReference
from drtc_chatbot.contexts.retrieval.application.ports import Retrieval
from drtc_chatbot.contexts.retrieval.domain.evaluation import RankedResult
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class ExactRetriever:
    name = "exact"

    def __init__(self, lookup: LookupReference) -> None:
        self._lookup = lookup

    async def retrieve(self, actor: Actor, text: str, limit: int) -> Retrieval:
        try:
            found = await self._lookup.execute(actor, text)
        except InvariantViolationError:  # empty or too long: not a reference
            return Retrieval(())
        results = tuple(
            RankedResult(hit.version_id, hit.path, hit.unit_path or hit.path)
            for hit in found.hits
            if hit.path is not None and hit.version_id is not None
        )
        return Retrieval(results[:limit])
