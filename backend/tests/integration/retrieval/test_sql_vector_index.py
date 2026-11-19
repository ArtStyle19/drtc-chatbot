"""Vectors in PostgreSQL: pending windows, storage, and the meaning search (spec 004)."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from drtc_chatbot.contexts.retrieval.application.embed_passages import EmbedPassages
from drtc_chatbot.contexts.retrieval.application.ports import StoredEmbedding
from drtc_chatbot.contexts.retrieval.domain.chunking import PassageText
from drtc_chatbot.contexts.retrieval.infrastructure.fake_embeddings import FakeEmbeddingProvider
from drtc_chatbot.contexts.retrieval.infrastructure.sql_passage_index import SqlPassageIndex

pytestmark = pytest.mark.docker

ALIASES = {"mototaxi": "menores", "mototaxis": "menores", "pasajero": "usuarios", "bus": "vehiculo"}


def passage(
    path: str,
    body: str,
    *,
    instrument: str = "renat",
    version: str = "renat@1",
    title: str | None = None,
) -> PassageText:
    return PassageText(
        instrument_id=instrument, version_id=version, path=path, unit_path=path.split("/", maxsplit=1)[0], kind="numeral",
        label=path.rsplit(":", maxsplit=1)[-1], title=title, breadcrumb=f"Norma › {path}", lead=None, body=body,
        page_start=3, page_end=3, citation=f"cita {path}",
    )  # fmt: skip


CORPUS = [
    passage("articulo:2", "El presente Reglamento no comprende el servicio de transporte en vehículos menores motorizados o no motorizados."),
    passage("articulo:77/numeral:77.1", "Los usuarios no deben abordar el vehículo en estado de ebriedad."),
    passage("articulo:25/numeral:25.1.2", "La antigüedad máxima de permanencia en el servicio será de quince años."),
    passage("articulo:218/numeral:218.2", "El término para interponer los recursos es de quince días perentorios.", instrument="tuo", version="tuo@1"),
]  # fmt: skip


@pytest.fixture
def index(db_sessions: async_sessionmaker) -> SqlPassageIndex:  # type: ignore[type-arg]
    return SqlPassageIndex(db_sessions)


async def embed_all(index: SqlPassageIndex, provider: FakeEmbeddingProvider) -> None:
    await EmbedPassages(index, provider).run()


@pytest.mark.spec("004-FR-016")
async def test_every_window_is_pending_until_it_has_a_vector_of_the_model(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)
    provider = FakeEmbeddingProvider()

    assert len(await index.missing_windows(provider.model)) == 4
    await embed_all(index, provider)

    assert await index.missing_windows(provider.model) == []
    assert await index.embedded_passages(provider.model) == 4


@pytest.mark.spec("004-FR-007")
async def test_the_meaning_search_finds_what_shares_meaning_not_words(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)
    provider = FakeEmbeddingProvider(ALIASES)
    await embed_all(index, provider)
    query = (await provider.embed(["mototaxi"])).vectors[0]

    hits = await index.vector_search(provider.model, query, instrument_id=None, limit=3)

    assert hits[0].passage.path == "articulo:2"  # "mototaxi" ~ "menores": no word in common
    assert hits[0].score > hits[-1].score
    assert [h.score for h in hits] == sorted((h.score for h in hits), reverse=True)
    # the words search cannot find it: this is exactly the gap the meaning search closes
    assert not any(
        h.passage.path == "articulo:2"
        for h in await index.lexical_search("mototaxis", instrument_id=None, limit=5)
    )


async def test_the_instrument_filter_applies_before_the_limit(index: SqlPassageIndex) -> None:
    await index.sync(CORPUS)
    provider = FakeEmbeddingProvider(ALIASES)
    await embed_all(index, provider)
    query = (await provider.embed(["recursos quince días"])).vectors[0]

    hits = await index.vector_search(provider.model, query, instrument_id="renat", limit=10)

    assert {h.passage.instrument_id for h in hits} == {"renat"}
    assert len(hits) == 3


async def test_vectors_of_other_models_are_ignored_even_with_a_different_size(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)
    small = FakeEmbeddingProvider(model="m-64")
    await embed_all(index, small)
    first = await index.missing_windows("m-wide")
    await index.store_embeddings(
        "m-wide",
        [StoredEmbedding(w.passage_id, w.window, w.content_hash, tuple([0.5] * 8)) for w in first],
    )  # another size

    query = (await small.embed(["recursos"])).vectors[0]

    hits = await index.vector_search("m-64", query, instrument_id=None, limit=10)
    assert len(hits) == 4  # the 8-dimensional vectors of the other model did not break the search
    assert await index.embedded_passages("m-wide") == 4


@pytest.mark.spec("004-FR-016")
async def test_changing_a_text_makes_only_its_windows_pending_again(index: SqlPassageIndex) -> None:
    await index.sync(CORPUS)
    provider = FakeEmbeddingProvider()
    await embed_all(index, provider)

    await index.sync(
        [
            *CORPUS[:2],
            passage("articulo:25/numeral:25.1.2", "Texto reformado sobre la antigüedad."),
            CORPUS[3],
        ]
    )

    pending = await index.missing_windows(provider.model)
    assert len(pending) == 1
    assert "Texto reformado" in pending[0].text


async def test_a_long_passage_has_several_windows_and_appears_once_in_the_results(
    index: SqlPassageIndex,
) -> None:
    sentences = " ".join(
        f"{i}. El transportista debe cumplir las condiciones técnicas del vehículo número {i}."
        for i in range(120)
    )
    await index.sync([passage("anexo:2", sentences), *CORPUS[:2]])
    provider = FakeEmbeddingProvider()

    windows = await index.missing_windows(provider.model)
    await embed_all(index, provider)
    hits = await index.vector_search(
        provider.model,
        (await provider.embed(["condiciones técnicas del vehículo"])).vectors[0],
        instrument_id=None,
        limit=10,
    )

    assert (
        sum(1 for w in windows if "anexo:2" in w.text or w.text.startswith("Norma › anexo:2")) > 2
    )
    assert [h.passage.path for h in hits].count(
        "anexo:2"
    ) == 1  # the best window represents the passage


async def test_storing_again_replaces_the_vector_instead_of_duplicating_it(
    index: SqlPassageIndex, db_sessions: async_sessionmaker
) -> None:  # type: ignore[type-arg]
    await index.sync(CORPUS[:1])
    [window] = await index.missing_windows("m")
    await index.store_embeddings(
        "m", [StoredEmbedding(window.passage_id, 0, window.content_hash, (1.0, 0.0))]
    )
    await index.store_embeddings(
        "m", [StoredEmbedding(window.passage_id, 0, window.content_hash, (0.0, 1.0))]
    )

    async with db_sessions() as session:
        rows = (
            await session.execute(text("SELECT count(*), max(dims) FROM retrieval_embeddings"))
        ).one()
    assert tuple(rows) == (1, 2)


async def test_the_snippet_is_the_beginning_of_the_text_without_marked_words(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)
    provider = FakeEmbeddingProvider()
    await embed_all(index, provider)

    [hit, *_] = await index.vector_search(
        provider.model,
        (await provider.embed(["usuarios ebriedad"])).vectors[0],
        instrument_id=None,
        limit=1,
    )

    assert [s.match for s in hit.snippet] == [False]
    assert hit.snippet[0].text.startswith("Los usuarios")


async def test_searching_a_model_with_no_vectors_gives_nothing_not_an_error(
    index: SqlPassageIndex,
) -> None:
    await index.sync(CORPUS)

    assert await index.vector_search("ninguno", (0.1, 0.2), instrument_id=None, limit=5) == []
