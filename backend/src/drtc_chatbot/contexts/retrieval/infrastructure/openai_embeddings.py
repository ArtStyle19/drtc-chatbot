"""EmbeddingProvider over the OpenAI API (the only place that knows the SDK; ADR-0006).

* the key comes from the settings as a ``SecretStr`` and never appears in a message or a log;
* the text of a request is NEVER put in an error message or a log line (a question may contain
  personal data: constitution VI);
* every failure becomes ``EmbeddingUnavailableError`` so the search can fall back to words;
* an interactive query has a short timeout and does not retry (it must answer in about 3 s or degrade),
  while indexing waits longer and retries with backoff (the SDK's own).
"""

from collections.abc import Sequence

import openai
from openai import AsyncOpenAI
from pydantic import SecretStr

from drtc_chatbot.contexts.retrieval.application.ports import EmbeddingBatch, EmbeddingPurpose
from drtc_chatbot.contexts.retrieval.domain.errors import (
    EmbeddingRateLimitedError,
    EmbeddingUnavailableError,
)
from drtc_chatbot.contexts.retrieval.domain.pricing import estimate_tokens

INDEXING_TIMEOUT_SECONDS = 30.0
INDEXING_RETRIES = 2
HTTP_SERVER_ERROR = 500


class OpenAIEmbeddingProvider:
    external = True
    # Something the person must read before text is sent (None = nothing special to say).
    data_notice: str | None = None

    def __init__(
        self,
        api_key: SecretStr,
        model: str,
        *,
        dimensions: int | None = None,
        client: AsyncOpenAI | None = None,
        indexing_retries: int = INDEXING_RETRIES,
        base_url: str | None = None,
    ) -> None:
        self._model_id = model
        self._dimensions = dimensions
        self._indexing_retries = indexing_retries
        self._tokens_used = 0
        self._client = client or AsyncOpenAI(
            api_key=api_key.get_secret_value(),
            base_url=base_url,
            timeout=INDEXING_TIMEOUT_SECONDS,
            max_retries=indexing_retries,
        )

    @property
    def model(self) -> str:
        """``text-embedding-3-large`` or, when shortened, ``text-embedding-3-large@1024``."""
        return (
            self._model_id if self._dimensions is None else f"{self._model_id}@{self._dimensions}"
        )

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    async def verify(self) -> None:
        """Checks that the configured model exists for this key (free: it lists, it does not embed)."""
        try:
            await self._client.models.retrieve(self._model_id)
        except openai.NotFoundError as error:
            raise EmbeddingUnavailableError(
                f"The model {self._model_id!r} does not exist for this key"
            ) from error
        except openai.OpenAIError as error:
            raise self._unavailable(error) from error

    async def embed(
        self,
        texts: Sequence[str],
        *,
        purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
        timeout_seconds: float | None = None,
    ) -> EmbeddingBatch:
        del purpose  # OpenAI's models embed a query and a document the same way
        if not texts:
            return EmbeddingBatch((), 0)
        interactive = timeout_seconds is not None
        client = self._client.with_options(
            timeout=timeout_seconds if interactive else INDEXING_TIMEOUT_SECONDS,
            max_retries=0 if interactive else self._indexing_retries,
        )
        options: dict[str, object] = {"model": self._model_id, "input": list(texts)}
        if self._dimensions is not None:
            options["dimensions"] = self._dimensions
        try:
            response = await client.embeddings.create(encoding_format="float", **options)  # type: ignore[arg-type]
        except openai.OpenAIError as error:
            raise self._unavailable(error) from error
        # Gemini's compatible endpoint omits `index` for the first item (a proto3 default of 0): a missing
        # index means 0. The sort is stable, so an answer with no indexes at all keeps its own order.
        ordered = sorted(response.data, key=lambda item: item.index or 0)
        # Providers that speak this protocol do not all report usage: then it is estimated (upper bound).
        usage = response.usage
        tokens = (
            usage.total_tokens
            if usage is not None
            else estimate_tokens(sum(len(text) for text in texts))
        )
        self._tokens_used += tokens
        return EmbeddingBatch(tuple(tuple(item.embedding) for item in ordered), tokens=tokens)

    @staticmethod
    def _unavailable(error: openai.OpenAIError) -> EmbeddingUnavailableError:
        """A fixed, safe message per kind of failure: never the body of the request or the response."""
        if isinstance(error, openai.AuthenticationError):  # HTTP 401
            return EmbeddingUnavailableError(
                "The embeddings provider says the API key is not valid (revoked, deleted or mistyped)"
            )
        if isinstance(error, openai.PermissionDeniedError):  # HTTP 403
            return EmbeddingUnavailableError(
                "The embeddings provider says this API key has no permission for this call"
            )
        if isinstance(error, openai.NotFoundError):  # HTTP 404
            return EmbeddingUnavailableError(
                "The embeddings provider does not know that model or address (HTTP 404)"
            )
        if isinstance(error, openai.RateLimitError):
            return EmbeddingRateLimitedError(
                "The embeddings provider is limiting requests (rate limit)"
            )
        if isinstance(error, openai.APITimeoutError):
            return EmbeddingUnavailableError("The embeddings provider did not answer in time")
        if isinstance(error, openai.APIConnectionError):
            return EmbeddingUnavailableError("Could not reach the embeddings provider")
        if isinstance(error, openai.APIStatusError):
            kind = "a server error" if error.status_code >= HTTP_SERVER_ERROR else "an error"
            return EmbeddingUnavailableError(
                f"The embeddings provider answered with {kind} (HTTP {error.status_code})"
            )
        return EmbeddingUnavailableError("The embeddings provider failed")
