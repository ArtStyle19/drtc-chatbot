"""Errors of the retrieval context."""

from drtc_chatbot.shared_kernel.domain import DomainError


class EmbeddingUnavailableError(DomainError):
    """The meaning search cannot be used right now (no key, provider error, timeout).

    The search treats it as a DEGRADATION, not a failure: it answers with the words search.
    """

    code = "embedding_unavailable"


class EmbeddingRateLimitedError(EmbeddingUnavailableError):
    """The provider answered "too many requests". Waiting a minute is the cure while indexing; an
    interactive search just degrades (it is an EmbeddingUnavailableError like the others)."""
