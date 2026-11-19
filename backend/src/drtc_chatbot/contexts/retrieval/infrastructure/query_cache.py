"""Remembers the vector of each QUERY text for the life of one process (command line only).

An evaluation embeds the same golden question once per method (meaning, hybrid) and once more for every
setting an ablation tries: without this, a provider with a daily quota or a price per request pays for the
same sentence again and again. Only queries are remembered, in memory, and only the command line builds
this wrapper: the web application never does, because keeping what people search for (even in memory) is
exactly what constitution VI says not to do. Passages (documents) always go to the provider.
"""

from collections.abc import Sequence
from typing import Any

from drtc_chatbot.contexts.retrieval.application.ports import (
    EmbeddingBatch,
    EmbeddingProvider,
    EmbeddingPurpose,
)


class QueryCachingEmbeddingProvider:
    def __init__(self, inner: EmbeddingProvider) -> None:
        self._inner = inner
        self._queries: dict[str, tuple[float, ...]] = {}

    @property
    def model(self) -> str:
        return self._inner.model

    @property
    def external(self) -> bool:
        return self._inner.external

    @property
    def tokens_used(self) -> int:
        """What the provider really counted: a remembered query adds nothing."""
        return self._inner.tokens_used

    @property
    def data_notice(self) -> str | None:
        return self._inner.data_notice

    def __getattr__(self, name: str) -> Any:
        # Everything else (e.g. `verify`, which only some providers have) is the provider's own.
        return getattr(self._inner, name)

    async def embed(
        self,
        texts: Sequence[str],
        *,
        purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
        timeout_seconds: float | None = None,
    ) -> EmbeddingBatch:
        if purpose is not EmbeddingPurpose.QUERY:
            return await self._inner.embed(texts, purpose=purpose, timeout_seconds=timeout_seconds)
        missing = [text for text in dict.fromkeys(texts) if text not in self._queries]
        tokens = 0
        if missing:  # a failure propagates before anything is remembered
            batch = await self._inner.embed(
                missing, purpose=purpose, timeout_seconds=timeout_seconds
            )
            self._queries.update(zip(missing, batch.vectors, strict=True))
            tokens = batch.tokens
        return EmbeddingBatch(tuple(self._queries[text] for text in texts), tokens=tokens)
