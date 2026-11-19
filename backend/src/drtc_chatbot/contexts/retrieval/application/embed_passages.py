"""Use case: compute the vectors of the passages that do not have one (spec 004, FR-005, FR-016).

Two steps on purpose: ``plan`` only COUNTS and estimates (nothing leaves the server), ``run`` sends.
Only the pieces without a vector, or whose text changed, are sent, so repeating a run costs nothing;
every batch is stored as soon as it arrives, so an interrupted run resumes where it stopped.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from drtc_chatbot.contexts.retrieval.application.ports import (
    EmbeddingProvider,
    PassageIndex,
    StoredEmbedding,
    WindowToEmbed,
)
from drtc_chatbot.contexts.retrieval.domain.pricing import (
    PRICE_PER_MILLION_TOKENS,
    estimate_cost_usd,
    estimate_tokens,
)
from drtc_chatbot.shared_kernel.domain import InvariantViolationError

BATCH_SIZE = 100  # inputs per request (the provider's limit is 2,048)


@dataclass(frozen=True, slots=True)
class EmbedPlan:
    model: str
    external: bool  # the text would leave the server
    windows: int
    characters: int
    tokens: int  # estimated (an upper bound)
    cost_usd: float | None  # estimated; None when the model has no known price


@dataclass(frozen=True, slots=True)
class EmbedOutcome:
    model: str
    windows: int
    batches: int
    tokens: int  # as REPORTED by the provider
    cost_usd: float | None


class EmbedPassages:
    def __init__(
        self,
        index: PassageIndex,
        provider: EmbeddingProvider,
        *,
        prices: Mapping[str, float] = PRICE_PER_MILLION_TOKENS,
    ) -> None:
        self._index = index
        self._provider = provider
        self._prices = prices

    async def _pending(self, limit: int | None) -> list[WindowToEmbed]:
        pending = sorted(
            await self._index.missing_windows(self._provider.model),
            key=lambda w: (w.passage_id, w.window),
        )
        return pending if limit is None else pending[:limit]

    async def plan(self, *, limit: int | None = None) -> EmbedPlan:
        pending = await self._pending(limit)
        characters = sum(len(w.text) for w in pending)
        tokens = estimate_tokens(characters)
        return EmbedPlan(
            model=self._provider.model,
            external=self._provider.external,
            windows=len(pending),
            characters=characters,
            tokens=tokens,
            cost_usd=estimate_cost_usd(tokens, self._provider.model, self._prices),
        )

    async def run(
        self,
        *,
        limit: int | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> EmbedOutcome:
        pending = await self._pending(limit)
        tokens = 0
        batches = 0
        for start in range(0, len(pending), BATCH_SIZE):
            batch = pending[start : start + BATCH_SIZE]
            result = await self._provider.embed([w.text for w in batch])
            if len(result.vectors) != len(batch):
                raise InvariantViolationError(
                    f"The provider returned {len(result.vectors)} vectors for {len(batch)} texts"
                )
            await self._index.store_embeddings(
                self._provider.model,
                [
                    StoredEmbedding(w.passage_id, w.window, w.content_hash, vector)
                    for w, vector in zip(batch, result.vectors, strict=True)
                ],
            )
            tokens += result.tokens
            batches += 1
            if progress is not None:
                progress(min(start + BATCH_SIZE, len(pending)), len(pending))
        return EmbedOutcome(
            model=self._provider.model,
            windows=len(pending),
            batches=batches,
            tokens=tokens,
            cost_usd=estimate_cost_usd(tokens, self._provider.model, self._prices),
        )
