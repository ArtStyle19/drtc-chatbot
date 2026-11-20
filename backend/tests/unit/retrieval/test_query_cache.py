"""The command-line query cache: a sentence is sent to the provider once, passages never are cached."""

from collections.abc import Sequence

import pytest

from drtc_chatbot.bootstrap.container import build_container
from drtc_chatbot.bootstrap.settings import Settings
from drtc_chatbot.contexts.retrieval.application.ports import EmbeddingBatch, EmbeddingPurpose
from drtc_chatbot.contexts.retrieval.domain.errors import EmbeddingUnavailableError
from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import FakeEmbeddingProvider
from drtc_chatbot.contexts.retrieval.infrastructure.query_cache import (
    QueryCachingEmbeddingProvider,
)


class Recording(FakeEmbeddingProvider):
    external = True
    data_notice: str | None = "aviso"

    def __init__(self) -> None:
        super().__init__(model="gemini-embedding-2")
        self.sent: list[tuple[EmbeddingPurpose, tuple[str, ...]]] = []

    async def embed(
        self,
        texts: Sequence[str],
        *,
        purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
        timeout_seconds: float | None = None,
    ) -> EmbeddingBatch:
        self.sent.append((purpose, tuple(texts)))
        return await super().embed(texts, purpose=purpose, timeout_seconds=timeout_seconds)

    async def verify(self) -> None:
        self.sent.append((EmbeddingPurpose.QUERY, ("verify",)))


Q = EmbeddingPurpose.QUERY
D = EmbeddingPurpose.DOCUMENT


@pytest.mark.spec("004-FR-005")
async def test_the_same_question_is_sent_to_the_provider_only_once() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)

    first = await cached.embed(["plazo para apelar"], purpose=Q)
    second = await cached.embed(["plazo para apelar"], purpose=Q)

    assert inner.sent == [(Q, ("plazo para apelar",))]
    assert second.vectors == first.vectors
    assert second.tokens == 0  # nothing new was counted
    assert first.tokens > 0


async def test_only_what_is_missing_is_sent_and_the_order_and_duplicates_are_kept() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)
    await cached.embed(["uno"], purpose=Q)

    batch = await cached.embed(["dos", "uno", "dos", "tres"], purpose=Q)

    assert inner.sent[1] == (Q, ("dos", "tres"))  # each new text once, in order
    assert len(batch.vectors) == 4
    assert batch.vectors[0] == batch.vectors[2]  # the duplicate "dos"
    assert batch.vectors[1] == (await cached.embed(["uno"], purpose=Q)).vectors[0]


async def test_passages_are_never_cached_they_always_go_to_the_provider() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)

    await cached.embed(["texto"], purpose=D)
    await cached.embed(["texto"], purpose=D)
    await cached.embed(["texto"])  # the default purpose is document

    assert [purpose for purpose, _ in inner.sent] == [D, D, D]


async def test_a_query_and_a_document_with_the_same_text_do_not_share_a_vector() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)

    await cached.embed(["texto"], purpose=D)
    await cached.embed(["texto"], purpose=Q)

    assert [purpose for purpose, _ in inner.sent] == [D, Q]


async def test_a_failure_remembers_nothing_and_is_not_swallowed() -> None:
    class Flaky(Recording):
        failing = True

        async def embed(
            self,
            texts: Sequence[str],
            *,
            purpose: EmbeddingPurpose = EmbeddingPurpose.DOCUMENT,
            timeout_seconds: float | None = None,
        ) -> EmbeddingBatch:
            if self.failing:
                raise EmbeddingUnavailableError("429")
            return await super().embed(texts, purpose=purpose, timeout_seconds=timeout_seconds)

    inner = Flaky()
    cached = QueryCachingEmbeddingProvider(inner)

    with pytest.raises(EmbeddingUnavailableError):
        await cached.embed(["algo"], purpose=Q)
    inner.failing = False
    batch = await cached.embed(["algo"], purpose=Q)

    assert len(batch.vectors) == 1
    assert len(inner.sent) == 1  # only the successful call got through


def test_it_looks_like_the_provider_it_wraps() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)

    assert cached.model == "gemini-embedding-2"
    assert cached.external is True
    assert cached.data_notice == "aviso"
    assert cached.tokens_used == 0


async def test_tokens_used_is_what_the_provider_really_counted() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)

    await cached.embed(["plazo para apelar"], purpose=Q)
    await cached.embed(["plazo para apelar"], purpose=Q)

    assert cached.tokens_used == inner.tokens_used > 0


async def test_what_only_some_providers_have_is_forwarded() -> None:
    inner = Recording()
    cached = QueryCachingEmbeddingProvider(inner)

    await cached.verify()  # type: ignore[attr-defined]

    assert inner.sent == [(Q, ("verify",))]
    with pytest.raises(AttributeError):
        cached.nothing_like_this  # noqa: B018


@pytest.mark.spec("004-FR-014")
async def test_only_the_command_line_remembers_queries_the_web_application_never_does() -> None:
    settings = Settings(_env_file=None, embedding_provider="fake")  # type: ignore[call-arg]
    web = build_container(settings)
    cli = build_container(settings, remember_queries=True)
    try:
        assert type(web.retrieval_cli.embedding) is FakeEmbeddingProvider
        assert isinstance(cli.retrieval_cli.embedding, QueryCachingEmbeddingProvider)
    finally:
        await web.aclose()
        await cli.aclose()


async def test_without_a_provider_there_is_nothing_to_wrap() -> None:
    container = build_container(Settings(_env_file=None), remember_queries=True)  # type: ignore[call-arg]
    try:
        assert container.retrieval_cli.embedding is None
    finally:
        await container.aclose()
