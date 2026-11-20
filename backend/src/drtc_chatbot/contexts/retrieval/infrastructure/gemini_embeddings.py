"""EmbeddingProvider over Google's Gemini API through its OpenAI-compatible endpoint (spec 004).

It IS the OpenAI adapter pointed at another address, so it keeps every guarantee of that one: the key is a
``SecretStr`` and never appears in a message or a log, the text of a request is NEVER put in an error
(a question may contain personal data: constitution VI), every failure becomes
``EmbeddingUnavailableError`` (the search then answers with words), and an interactive query has a short
timeout and does not retry. What is different, from Google's own documentation:

* ``gemini-embedding-2`` takes no ``task_type``: the task is a TEXT PREFIX, one for a search query and one
  for a document being indexed. ``gemini-embedding-001`` takes none of it through this endpoint, so it
  gets the plain text.
* The vectors have 3072 dimensions (the default); asking for fewer would need normalising for ``-001``.
* The free tier has rate limits that are per project and not in the docs. Found with the real API: 100
  embed requests per minute for ``gemini-embedding-2``, and EVERY TEXT of a batch counts as one request.
  Indexing therefore sends small batches and two limiters keep the texts per minute and the estimated
  tokens per minute under configurable ceilings; if a 429 still comes, it waits a full minute and tries
  again. A run that is cut can be resumed (``EmbedPassages`` stores per batch).
"""

import asyncio
import time
from collections import deque
from collections.abc import Awaitable, Callable, Iterator, Sequence

import openai
from openai import AsyncOpenAI
from pydantic import SecretStr

from drtc_chatbot.contexts.retrieval.application.ports import EmbeddingBatch, EmbeddingPurpose
from drtc_chatbot.contexts.retrieval.domain.errors import (
    EmbeddingQuotaExhaustedError,
    EmbeddingRateLimitedError,
    EmbeddingUnavailableError,
)
from drtc_chatbot.contexts.retrieval.domain.pricing import estimate_tokens
from drtc_chatbot.contexts.retrieval.infrastructure.openai_embeddings import (
    OpenAIEmbeddingProvider,
)

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-embedding-2"
BATCH_ITEMS = 16
# The SDK retries a 429 within seconds, which only meets the per-minute limit again: the pauses of a whole
# window are ours (below). It keeps a couple of retries for the transient 5xx answers.
INDEXING_RETRIES = 2
RATE_LIMIT_PAUSES = 4  # whole minutes to wait through a 429 before giving up on a batch
RATE_LIMIT_PAUSE_SECONDS = 65.0
VERIFY_TIMEOUT_SECONDS = 15.0
WINDOW_SECONDS = 60.0

# The exact formats Google documents for gemini-embedding-2 ("title: none" when there is no title).
QUERY_PREFIX = "task: search result | query: "
DOCUMENT_PREFIX = "title: none | text: "

FREE_TIER_NOTICE = (
    "Si su proyecto de Google AI no tiene facturación activa (plan gratuito), Google puede usar y revisar lo "
    "que se envíe para mejorar sus productos: envíe solo texto de normas y preguntas de prueba, sin datos "
    "personales."
)


class PerMinuteLimit:
    """Keeps what is sent in any 60 seconds (tokens, or texts) under ``limit``: it waits, never fails."""

    def __init__(
        self,
        limit: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        self._limit = limit
        self._clock = clock
        self._sleep = sleep
        self._spent: deque[tuple[float, int]] = deque()

    async def acquire(self, amount: int) -> None:
        amount = min(amount, self._limit)  # one request bigger than the ceiling would never fit
        while True:
            now = self._clock()
            while self._spent and now - self._spent[0][0] >= WINDOW_SECONDS:
                self._spent.popleft()
            if sum(spent for _, spent in self._spent) + amount <= self._limit:
                self._spent.append((now, amount))
                return
            await self._sleep(max(WINDOW_SECONDS - (now - self._spent[0][0]), 0.05))


def _is_daily_quota(error: openai.RateLimitError) -> bool:
    """Google names the quota in the 429 body ("... per day limit exceeded on Free Tier"). Only a fixed
    marker is looked for; nothing of the body is ever copied into a message."""
    return "per day" in str(error.body).lower()


class GeminiEmbeddingProvider(OpenAIEmbeddingProvider):
    data_notice = FREE_TIER_NOTICE

    def __init__(
        self,
        api_key: SecretStr,
        model: str = DEFAULT_MODEL,
        *,
        max_tokens_per_minute: int = 25_000,
        max_requests_per_minute: int = 80,
        client: AsyncOpenAI | None = None,
        indexing_retries: int = INDEXING_RETRIES,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ) -> None:
        super().__init__(
            api_key,
            model,
            dimensions=None,
            client=client,
            indexing_retries=indexing_retries,
            base_url=GEMINI_BASE_URL,
        )
        self._takes_prefix = model.startswith("gemini-embedding-2")
        self._max_batch_tokens = max(max_tokens_per_minute // 2, 1)
        self._sleep = sleep
        self._token_limit = PerMinuteLimit(max_tokens_per_minute, clock=clock, sleep=sleep)
        self._text_limit = PerMinuteLimit(max_requests_per_minute, clock=clock, sleep=sleep)

    @staticmethod
    def _unavailable(error: openai.OpenAIError) -> EmbeddingUnavailableError:
        """A daily quota is told apart from a per-minute limit: only the second is cured by waiting."""
        if isinstance(error, openai.RateLimitError) and _is_daily_quota(error):
            return EmbeddingQuotaExhaustedError(
                "The embeddings provider's daily free quota is used up: it resets at midnight "
                "Pacific time (03:00 in Lima); wait for it or enable billing on the Google project"
            )
        return OpenAIEmbeddingProvider._unavailable(error)

    async def verify(self) -> None:
        """One tiny real embedding: proves the key, the model and the address together."""
        await self.embed(
            ["prueba"], purpose=EmbeddingPurpose.QUERY, timeout_seconds=VERIFY_TIMEOUT_SECONDS
        )

    async def embed(
        self,
        texts: Sequence[str],
        *,
        purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
        timeout_seconds: float | None = None,
    ) -> EmbeddingBatch:
        if not texts:
            return EmbeddingBatch((), 0)
        formatted = [self._format(text, purpose) for text in texts]
        if (
            timeout_seconds is not None
        ):  # a person is waiting: one request, never wait for the limiter
            return await super().embed(formatted, purpose=purpose, timeout_seconds=timeout_seconds)
        vectors: list[tuple[float, ...]] = []
        tokens = 0
        for batch in self._batches(formatted):
            await self._token_limit.acquire(estimate_tokens(sum(len(text) for text in batch)))
            await self._text_limit.acquire(len(batch))  # Google counts every text as a request
            result = await self._embed_waiting_out_rate_limits(batch, purpose)
            vectors.extend(result.vectors)
            tokens += result.tokens
        return EmbeddingBatch(tuple(vectors), tokens)

    async def _embed_waiting_out_rate_limits(
        self, batch: list[str], purpose: EmbeddingPurpose
    ) -> EmbeddingBatch:
        """Indexing can wait: on a 429 it pauses a whole window and tries the same batch again."""
        for pause in range(RATE_LIMIT_PAUSES + 1):
            try:
                return await super().embed(batch, purpose=purpose)
            except EmbeddingRateLimitedError:
                if pause == RATE_LIMIT_PAUSES:
                    raise
                await self._sleep(RATE_LIMIT_PAUSE_SECONDS)
        raise AssertionError("unreachable")  # pragma: no cover

    def _format(self, text: str, purpose: EmbeddingPurpose) -> str:
        if not self._takes_prefix:
            return text
        return (QUERY_PREFIX if purpose is EmbeddingPurpose.QUERY else DOCUMENT_PREFIX) + text

    def _batches(self, texts: Sequence[str]) -> Iterator[list[str]]:
        batch: list[str] = []
        size = 0
        for text in texts:
            cost = estimate_tokens(len(text))
            if batch and (len(batch) >= BATCH_ITEMS or size + cost > self._max_batch_tokens):
                yield batch
                batch, size = [], 0
            batch.append(text)
            size += cost
        if batch:
            yield batch
