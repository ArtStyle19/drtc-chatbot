"""The offline provider: deterministic, normalised, and able to simulate synonyms."""

import math

import pytest

from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import (
    DIMENSIONS,
    FakeEmbeddingProvider,
)


def cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


async def vec(provider: FakeEmbeddingProvider, text: str) -> tuple[float, ...]:
    return (await provider.embed([text])).vectors[0]


async def test_the_same_text_always_gives_the_same_vector_even_across_instances() -> None:
    assert await vec(FakeEmbeddingProvider(), "plazo para apelar") == await vec(
        FakeEmbeddingProvider(), "plazo para apelar"
    )


async def test_vectors_have_a_fixed_size_and_unit_length() -> None:
    v = await vec(FakeEmbeddingProvider(), "El Estado incentiva la libre competencia")

    assert len(v) == DIMENSIONS
    assert math.sqrt(sum(x * x for x in v)) == pytest.approx(1.0)


async def test_texts_that_share_words_are_closer_than_texts_that_do_not() -> None:
    p = FakeEmbeddingProvider()
    base = await vec(p, "recurso de apelación contra la resolución")

    near = cosine(base, await vec(p, "plazo del recurso de apelación"))
    far = cosine(base, await vec(p, "vehículos automotores y seguro obligatorio"))

    assert near > far


async def test_case_and_accents_do_not_change_the_vector() -> None:
    p = FakeEmbeddingProvider()

    assert await vec(p, "APELACIÓN Tránsito") == await vec(p, "apelacion transito")


async def test_aliases_simulate_synonyms_without_a_network() -> None:
    p = FakeEmbeddingProvider({"mototaxi": "menores", "moto": "menores"})

    close = cosine(await vec(p, "mototaxi"), await vec(p, "vehículos menores"))
    plain = cosine(
        await vec(FakeEmbeddingProvider(), "mototaxi"),
        await vec(FakeEmbeddingProvider(), "vehículos menores"),
    )

    assert close > plain


async def test_a_batch_keeps_the_order_and_reports_tokens_and_calls() -> None:
    p = FakeEmbeddingProvider()

    batch = await p.embed(["uno dos", "tres"])

    assert [
        v == await vec(p, t) for v, t in zip(batch.vectors, ["uno dos", "tres"], strict=True)
    ] == [True, True]
    assert batch.tokens == 3
    assert p.calls == [2, 1, 1]  # the batch, then the two checks above (each is a call of one text)


async def test_an_empty_text_gives_a_valid_zero_free_vector_without_crashing() -> None:
    v = await vec(FakeEmbeddingProvider(), "")

    assert len(v) == DIMENSIONS
    assert not any(math.isnan(x) for x in v)


def test_it_is_never_an_external_provider() -> None:
    assert FakeEmbeddingProvider().external is False
    assert FakeEmbeddingProvider(model="otro").model == "otro"
