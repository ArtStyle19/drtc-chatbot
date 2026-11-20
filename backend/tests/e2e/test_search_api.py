"""GET /api/v1/search over the three real norms (spec 004)."""

from typing import Any

import httpx
import pytest
import structlog

from drtc_chatbot.bootstrap.container import Container
from drtc_chatbot.bootstrap.settings import Environment
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker

ACTOR = Actor("test", ActorKind.SERVICE)


async def prepared(container: Container) -> None:
    await container.retrieval_cli.build_index.execute(ACTOR)
    if container.retrieval_cli.embed_passages is not None:
        await container.retrieval_cli.embed_passages.run()


async def get(client: httpx.AsyncClient, **params: Any) -> httpx.Response:
    return await client.get("/api/v1/search", params=params)


@pytest.mark.spec("004-FR-011")
async def test_a_search_answers_with_units_citations_pages_snippets_and_the_edition(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)

        response = await get(client, q="plazo para interponer recursos administrativos")

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["mode"], body["degraded"], body["reference"]) == ("hybrid", [], None)
    assert body["total"] >= 10
    assert len(body["results"]) == 10
    first = body["results"][0]
    assert set(first) >= {
        "instrument_id", "instrument_short_name", "version_id", "edition_label", "verification_status",
        "may_be_presented_as_current", "unit_path", "path", "kind", "label", "citation", "page_start",
        "page_end", "snippet", "matched", "via", "score",
    }  # fmt: skip
    assert first["citation"]
    assert all(
        isinstance(s["text"], str) and isinstance(s["match"], bool) for s in first["snippet"]
    )
    assert "debug" in first
    assert first["debug"] is None  # not asked for
    assert {f["instrument_id"] for f in body["facets"]} <= {
        "ley-27181",
        "ds-017-2009-mtc",
        "tuo-ley-27444",
    }


@pytest.mark.spec("004-SC-009")
async def test_nothing_is_ever_presented_as_current_while_the_editions_are_unverified(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)

        responses = [
            await get(client, q=q, limit=30)
            for q in ("silencio positivo", "SOAT", "art. 5 Ley 27181", "multa", "mototaxi")
        ]

    results = [r for response in responses for r in response.json()["results"]]
    assert results
    assert {r["verification_status"] for r in results} == {"unverified"}
    assert {r["may_be_presented_as_current"] for r in results} == {False}


@pytest.mark.spec("004-FR-009")
async def test_a_reference_plus_words_puts_the_referenced_provision_first_and_marked(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)

        body = (await get(client, q="art. 5 Ley 27181 plazo")).json()

    first = body["results"][0]
    assert (first["instrument_id"], first["unit_path"]) == ("ley-27181", "articulo:5")
    assert first["via"][0] == "reference"
    assert body["reference"] == "art. 5"


@pytest.mark.spec("004-FR-009")
async def test_an_ambiguous_reference_lists_every_candidate(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="none") as (client, container):
        await prepared(container)

        body = (await get(client, q="art. 11")).json()

    assert [r["instrument_id"] for r in body["results"]] == [
        "ley-27181",
        "ds-017-2009-mtc",
        "tuo-ley-27444",
    ]
    assert {tuple(r["via"]) for r in body["results"]} == {("reference",)}


@pytest.mark.spec("004-FR-019")
async def test_the_norm_filter_limits_the_results_and_keeps_the_facets(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)

        body = (
            await get(client, q="sanción por infracción", instrument="tuo-ley-27444", limit=30)
        ).json()

    assert {r["instrument_id"] for r in body["results"]} == {"tuo-ley-27444"}
    assert len(body["facets"]) >= 2


@pytest.mark.spec("004-FR-014")
@pytest.mark.parametrize(
    "params",
    [
        {"q": ""},
        {"q": "x" * 301},
        {},
        {"q": "algo", "limit": 0},
        {"q": "algo", "limit": 31},
        {"q": "algo", "mode": "magic"},
        {"q": "algo", "instrument": "NO VALIDO!"},
        {"q": "algo", "debug": "quizás"},
    ],
)
async def test_invalid_requests_are_refused_with_422_before_anything_is_searched(
    full_corpus: str, params: dict[str, Any]
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, _):
        response = await get(client, **params)

    assert response.status_code == 422


async def test_a_text_of_only_spaces_is_refused_too(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, _):
        response = await get(client, q="    ")

    assert response.status_code == 422


@pytest.mark.spec("004-FR-014")
async def test_the_longest_allowed_text_is_accepted(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)

        response = await get(client, q="plazo " * 49 + "x")  # 295 characters

    assert response.status_code == 200


@pytest.mark.spec("004-SC-006")
async def test_without_a_meaning_provider_the_api_still_answers_with_words_and_says_why(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="none") as (client, container):
        await prepared(container)

        responses = [
            await get(client, q=q)
            for q in ("plazo para apelar", "silencio positivo", "SOAT obligatorio")
        ]

    assert [r.status_code for r in responses] == [200, 200, 200]
    assert all(r.json()["degraded"] == ["vector_unavailable"] for r in responses)
    assert all(r.json()["total"] > 0 for r in responses)


async def test_the_lexical_and_vector_modes_can_be_asked_for_explicitly(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)

        lexical = (await get(client, q="silencio positivo", mode="lexical")).json()
        vector = (await get(client, q="silencio positivo", mode="vector")).json()

    assert {v for r in lexical["results"] for v in r["via"]} == {"lexical"}
    assert {v for r in vector["results"] for v in r["via"]} == {"vector"}


@pytest.mark.spec("004-FR-017")
async def test_the_debug_view_exists_in_development_and_is_ignored_in_production(
    full_corpus: str,
) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, container):
        await prepared(container)
        shown = (await get(client, q="multa", debug="true")).json()
    async with open_stack(
        full_corpus, embedding_provider="none", environment=Environment.PRODUCTION
    ) as (client, container):
        await prepared(container)
        hidden = (await get(client, q="multa", debug="true")).json()

    assert all(r["debug"] is not None for r in shown["results"])
    assert {"lexical_rank", "vector_rank", "reference_rank"} <= set(shown["results"][0]["debug"])
    assert hidden["results"]
    assert all(r["debug"] is None for r in hidden["results"])


@pytest.mark.spec("004-FR-014")
async def test_the_text_of_a_search_is_never_written_to_the_logs_only_its_size(
    full_corpus: str,
) -> None:
    secret = "mi vecino Pedro Quispe DNI 45678912 placa ABC-123 plazo"  # noqa: S105 - a made-up text
    async with open_stack(full_corpus, embedding_provider="fake", log_level="INFO") as (
        client,
        container,
    ):
        await prepared(container)
        with structlog.testing.capture_logs() as logs:
            response = await get(client, q=secret)

    assert response.status_code == 200
    assert "Quispe" not in str(logs)
    assert "45678912" not in str(logs)
    assert secret not in str(logs)
    assert "ABC-123" not in str(logs)
    [event] = [e for e in logs if e["event"] == "search"]
    assert set(event) >= {"mode", "results", "latency_ms", "degraded", "query_chars"}
    assert event["query_chars"] == len(secret)
    [request] = [e for e in logs if e["event"] == "http.request"]
    assert request["path"] == "/api/v1/search"  # the path, never the query string
    assert request["status"] == 200


@pytest.mark.spec("004-FR-014")
async def test_an_api_error_never_echoes_the_search_text(full_corpus: str) -> None:
    async with open_stack(full_corpus, embedding_provider="fake") as (client, _):
        response = await get(client, q="DNI 45678912 " + "x" * 400)

    assert response.status_code == 422
    assert "45678912" not in response.text  # pydantic's `input` is removed from the problem details
    errors = response.json()["errors"]
    assert errors
    assert all("input" not in e for e in errors)
    assert errors[0]["loc"] == ["query", "q"]  # it still says WHAT is wrong
