"""Errors of the retrieval context."""

from drtc_chatbot.shared_kernel.domain import DomainError


class EmbeddingUnavailableError(DomainError):
    """The meaning search cannot be used right now (no key, provider error, timeout).

    The search treats it as a DEGRADATION, not a failure: it answers with the words search.
    """

    code = "embedding_unavailable"
