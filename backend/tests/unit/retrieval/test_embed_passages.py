"""Embedding run: estimate first, send only what is missing, resume, never mix models."""

from collections.abc import Sequence

import pytest

from drtc_chatbot.contexts.retrieval.application.embed_passages import (
    BATCH_SIZE,
    EmbedPassages,
)
from drtc_chatbot.contexts.retrieval.application.ports import (
    EmbeddingBatch,
    StoredEmbedding,
    WindowToEmbed,
)
from drtc_chatbot.contexts.retrieval.domain.errors import EmbeddingUnavailableError
from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import FakeEmbeddingProvider
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class MemoryIndex:
    """Only what the use case needs: windows without a vector, and a place to store vectors."""

    def __init__(self, windows: Sequence[WindowToEmbed]) -> None:
        self.windows = list(windows)
        self.stored: dict[tuple[str, str, int], tuple[str, tuple[float, ...]]] = {}

    async def missing_windows(self, model: str) -> Sequence[WindowToEmbed]:
        return [
            w
            for w in self.windows
            if self.stored.get((model, w.passage_id, w.window), ("",))[0] != w.content_hash
        ]

    async def store_embeddings(self, model: str, items: Sequence[StoredEmbedding]) -> None:
        for item in items:
            self.stored[(model, item.passage_id, item.window)] = (item.content_hash, item.vector)


def windows(n: int, text: str = "x" * 300) -> list[WindowToEmbed]:
    return [WindowToEmbed(f"p{i:04}", 0, f"{text} {i}", f"h{i}") for i in range(n)]


def use_case(index: MemoryIndex, provider: object | None = None, **kwargs: object) -> EmbedPassages:
    return EmbedPassages(index, provider or FakeEmbeddingProvider(), **kwargs)  # type: ignore[arg-type]


class Paid(FakeEmbeddingProvider):
    external = True

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        super().__init__(model=model)


@pytest.mark.spec("004-FR-005")
async def test_the_plan_counts_and_estimates_without_calling_the_provider() -> None:
    provider = Paid()

    plan = await use_case(MemoryIndex(windows(10)), provider).plan()

    assert (plan.windows, plan.model, plan.external) == (10, "text-embedding-3-small", True)
    assert plan.characters == sum(len(w.text) for w in windows(10))
    assert plan.tokens == -(-plan.characters // 3)  # ceiling of characters / 3
    assert plan.cost_usd == pytest.approx(plan.tokens / 1_000_000 * 0.02)
    assert provider.calls == []  # NOTHING was sent


@pytest.mark.spec("004-FR-005")
async def test_a_model_without_a_known_price_has_no_estimate_rather_than_a_wrong_one() -> None:
    plan = await use_case(MemoryIndex(windows(2)), Paid("modelo-raro")).plan()

    assert plan.cost_usd is None


@pytest.mark.spec("004-FR-016")
async def test_a_run_sends_in_batches_stores_everything_and_reports_the_real_usage() -> None:
    provider = Paid()
    index = MemoryIndex(windows(BATCH_SIZE * 2 + 5))

    outcome = await use_case(index, provider).run()

    assert provider.calls == [BATCH_SIZE, BATCH_SIZE, 5]
    assert (outcome.windows, outcome.batches) == (BATCH_SIZE * 2 + 5, 3)
    assert len(index.stored) == BATCH_SIZE * 2 + 5
    assert outcome.tokens > 0
    assert outcome.cost_usd == pytest.approx(outcome.tokens / 1_000_000 * 0.02)


@pytest.mark.spec("004-FR-016")
async def test_a_second_run_sends_nothing_because_every_window_has_its_vector() -> None:
    provider = Paid()
    index = MemoryIndex(windows(30))
    await use_case(index, provider).run()
    calls_after_first = list(provider.calls)

    second = await use_case(index, provider).run()

    assert (second.windows, second.batches, second.tokens) == (0, 0, 0)
    assert provider.calls == calls_after_first


@pytest.mark.spec("004-FR-016")
async def test_only_a_window_whose_text_changed_is_sent_again() -> None:
    provider = Paid()
    index = MemoryIndex(windows(10))
    await use_case(index, provider).run()
    index.windows[3] = WindowToEmbed("p0003", 0, "texto reformado", "h3-new")

    outcome = await use_case(index, provider).run()

    assert outcome.windows == 1
    assert provider.calls[-1] == 1


async def test_a_limit_embeds_only_the_first_windows_in_a_stable_order() -> None:
    index = MemoryIndex(list(reversed(windows(10))))

    outcome = await use_case(index).run(limit=3)

    assert outcome.windows == 3
    assert sorted(p for (_, p, _) in index.stored) == ["p0000", "p0001", "p0002"]


async def test_vectors_of_different_models_never_mix() -> None:
    index = MemoryIndex(windows(4))
    await use_case(index, FakeEmbeddingProvider(model="m-a")).run()

    other = await use_case(index, FakeEmbeddingProvider(model="m-b")).plan()

    assert other.windows == 4  # the second model has none yet


@pytest.mark.spec("004-FR-013")
async def test_when_the_provider_fails_halfway_what_was_done_is_kept_and_the_run_can_resume() -> (
    None
):
    class Flaky(FakeEmbeddingProvider):
        async def embed(
            self, texts: Sequence[str], *, timeout_seconds: float | None = None
        ) -> EmbeddingBatch:
            if len(self.calls) == 1:
                self.calls.append(-1)
                raise EmbeddingUnavailableError("503 from the provider")
            return await super().embed(texts, timeout_seconds=timeout_seconds)

    provider = Flaky()
    index = MemoryIndex(windows(BATCH_SIZE + 20))

    with pytest.raises(EmbeddingUnavailableError):
        await use_case(index, provider).run()
    assert len(index.stored) == BATCH_SIZE  # the first batch was kept
    resumed = await use_case(index, provider).run()

    assert resumed.windows == 20  # only what was missing
    assert len(index.stored) == BATCH_SIZE + 20


async def test_a_provider_answering_with_the_wrong_number_of_vectors_is_refused() -> None:
    class Short(FakeEmbeddingProvider):
        async def embed(
            self, texts: Sequence[str], *, timeout_seconds: float | None = None
        ) -> EmbeddingBatch:
            return EmbeddingBatch(((0.0,),), tokens=1)

    with pytest.raises(InvariantViolationError, match="1 vectors for 3 texts"):
        await use_case(MemoryIndex(windows(3)), Short()).run()


async def test_progress_is_reported_after_each_batch() -> None:
    seen: list[tuple[int, int]] = []

    await use_case(MemoryIndex(windows(BATCH_SIZE + 1))).run(
        progress=lambda done, total: seen.append((done, total))
    )

    assert seen == [(BATCH_SIZE, BATCH_SIZE + 1), (BATCH_SIZE + 1, BATCH_SIZE + 1)]
