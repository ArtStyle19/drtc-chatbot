"""The content search over the three real norms in PostgreSQL, with the offline meaning provider."""

import pytest

from drtc_chatbot.bootstrap.container import Container
from drtc_chatbot.contexts.retrieval.application.dto import SearchMode, SearchResponse
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker

ACTOR = Actor("test", ActorKind.SERVICE)


async def prepare(container: Container) -> None:
    await container.retrieval_cli.build_index.execute(ACTOR)
    if container.retrieval_cli.embed_passages is not None:
        await container.retrieval_cli.embed_passages.run()


async def search(container: Container, text: str, **kwargs: object) -> SearchResponse:
    return await container.retrieval.search_passages.execute(ACTOR, text, **kwargs)  # type: ignore[arg-type]


@pytest.mark.spec("004-FR-008")
async def test_the_hybrid_search_returns_reading_units_with_citation_page_and_edition(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await prepare(container)

        response = await search(container, "plazo para interponer recursos administrativos")

    assert response.degraded == ()
    assert response.total >= 10
    assert len(response.results) == 10
    for result in response.results:
        assert result.citation
        assert result.page_start >= 1
        assert result.edition_label
        assert result.snippet
        assert result.unit_path
        assert set(result.via) <= {"lexical", "vector"}
    assert len({(r.version_id, r.unit_path) for r in response.results}) == 10  # one result per unit
    assert any(
        "lexical" in r.via and "vector" in r.via for r in response.results
    )  # fusion happened


@pytest.mark.spec("004-FR-009")
async def test_a_reference_in_the_text_comes_first_and_is_marked(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await prepare(container)

        response = await search(container, "art. 218 TUO recursos administrativos")

    first = response.results[0]
    assert (first.instrument_id, first.unit_path) == ("tuo-ley-27444", "articulo:218")
    assert "reference" in first.via
    assert response.reference == "art. 218"
    assert [r.unit_path for r in response.results].count("articulo:218") == 1


@pytest.mark.spec("004-SC-009")
async def test_no_result_is_ever_presented_as_verified_while_the_editions_are_not(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await prepare(container)

        responses = [
            await search(container, text, limit=30)
            for text in (
                "silencio positivo",
                "mototaxi",
                "art. 5 Ley 27181",
                "multa",
                "licencia de conducir",
            )
        ]

    statuses = {r.verification_status for resp in responses for r in resp.results}
    assert statuses == {
        "unverified"
    }  # the three editions are unverified: nothing is ever "verified_current"


@pytest.mark.spec("004-SC-006")
async def test_without_a_meaning_provider_every_search_still_answers_with_words_and_a_notice(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="none") as (_, container):
        await prepare(container)

        responses = [
            await search(container, text)
            for text in (
                "plazo para apelar",
                "silencio positivo",
                "vehículos menores motorizados",
                "SOAT",
            )
        ]

    assert all(r.degraded == ("vector_unavailable",) for r in responses)
    assert all(r.total > 0 for r in responses)
    assert all(set(x.via) == {"lexical"} for r in responses for x in r.results)


@pytest.mark.spec("004-FR-013")
async def test_vectors_not_computed_yet_degrade_with_their_own_notice(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await container.retrieval_cli.build_index.execute(ACTOR)  # indexed, but `embed` was not run

        response = await search(container, "plazo para apelar")

    assert response.degraded == ("vector_not_indexed",)
    assert response.total > 0


@pytest.mark.spec("004-FR-019")
async def test_the_norm_filter_keeps_the_facets_of_the_other_norms(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await prepare(container)

        response = await search(
            container, "sanción por infracción", instrument_id="ds-017-2009-mtc", limit=30
        )

    assert {r.instrument_id for r in response.results} == {"ds-017-2009-mtc"}
    facets = {f.instrument_id: f.count for f in response.facets}
    assert "ds-017-2009-mtc" in facets
    assert len(facets) >= 2, (
        "the facets are counted WITHOUT the filter, so the person can switch norm"
    )


@pytest.mark.spec("004-FR-010")
async def test_a_literal_is_reached_through_its_article_with_the_matching_passages_listed(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="none") as (_, container):
        await prepare(container)

        response = await search(
            container,
            "servicio de transporte de personas definición",
            mode=SearchMode.LEXICAL,
            instrument_id="ley-27181",
            limit=30,
        )

    article_2 = [
        r
        for r in response.results
        if r.instrument_id == "ley-27181" and r.unit_path == "articulo:2"
    ]
    assert article_2, (
        f"the definitions article of the Ley should be found; got {[(r.instrument_id, r.unit_path) for r in response.results]}, degraded={response.degraded}"
    )
    assert any(m.path.startswith("articulo:2/literal:") for m in article_2[0].matched)


@pytest.mark.spec("004-FR-017")
async def test_the_debug_view_exposes_the_rank_of_each_arm(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await prepare(container)

        response = await search(container, "multa por no tener SOAT", debug=True)

    assert all(r.debug is not None for r in response.results)
    assert any(
        r.debug and r.debug["lexical_rank"] and r.debug["vector_rank"] for r in response.results
    )


@pytest.mark.spec("004-SC-005")
async def test_a_search_over_the_whole_corpus_answers_well_within_the_time_limit(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (_, container):
        await prepare(container)

        timings = [
            (await search(container, "plazo para interponer recursos")).latency_ms
            for _ in range(15)
        ]

    assert (
        sorted(timings)[int(len(timings) * 0.95) - 1] < 500
    )  # the offline provider costs nothing: this is the DB + fusion
