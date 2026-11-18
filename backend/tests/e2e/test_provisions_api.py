"""Ingest the real Ley 27181 into PostgreSQL and read it back through the HTTP API."""

from typing import Any

import httpx
import pytest

from tests.e2e.conftest import LEY, Stack

pytestmark = pytest.mark.docker


async def provisions(client: httpx.AsyncClient, **params: Any) -> httpx.Response:
    return await client.get("/api/v1/instruments/ley-27181/provisions", params=params)


@pytest.mark.spec("002-FR-010")
async def test_nothing_is_readable_before_ingestion_and_the_catalog_shows_it(
    stack: Stack,
) -> None:
    client, container = stack
    await container.ingestion.gateway.sync_manifest()

    catalog = (await client.get("/api/v1/instruments")).json()["items"]
    response = await provisions(client)

    assert [i["current_edition"]["provision_count"] for i in catalog] == [0, 0, 0]
    assert {i["current_edition"]["approval_status"] for i in catalog} == {"pending"}
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")


@pytest.mark.spec("002-FR-010")
async def test_an_ingested_version_stays_hidden_until_a_human_approves_it(
    stack: Stack,
) -> None:
    client, container = stack
    outcome = await container.ingestion.run_ingestion.execute(LEY)
    assert outcome.approval is None  # manual policy

    assert (await provisions(client)).status_code == 404

    await container.ingestion.gateway.approve(LEY, "Ana Quispe")
    response = await provisions(client, limit=500)
    body = response.json()

    assert response.status_code == 200
    assert body["approval_mode"] == "human"
    assert body["verification_status"] == "unverified"
    assert body["may_be_presented_as_current"] is False  # approved is NOT verified
    assert body["total"] == outcome.report.current_by_kind.get("article", 0) + sum(
        n for k, n in outcome.report.current_by_kind.items() if k != "article"
    )


@pytest.mark.spec("002-FR-003")
async def test_article_2_exposes_its_history_and_the_norm_that_replaced_it(
    stack: Stack,
) -> None:
    client, container = stack
    await container.ingestion.run_ingestion.execute(LEY)
    await container.ingestion.gateway.approve(LEY, "Ana Quispe")

    articles = (await provisions(client, kind="article", limit=500)).json()
    article_2 = next(i for i in articles["items"] if i["path"] == "articulo:2")
    detail = (await client.get(f"/api/v1/provisions/{article_2['id']}")).json()

    assert article_2["revision"] == 2
    assert article_2["revision_count"] == 2
    assert article_2["event"]["kind"] == "substituted"
    assert "Decreto de Urgencia" in article_2["event"]["source"]
    assert [(r["revision"], r["status"]) for r in detail["revisions"]] == [
        (1, "superseded"),
        (2, "current"),
    ]
    assert detail["revisions"][1]["page_start"] == 3
    assert detail["may_be_presented_as_current"] is False
    assert any(n["kind"] == "amendment" for n in detail["notes"])


async def test_literals_can_be_listed_by_parent_with_their_exact_pages(
    stack: Stack,
) -> None:
    client, container = stack
    await container.ingestion.run_ingestion.execute(LEY)
    await container.ingestion.gateway.approve(LEY, "Ana Quispe")

    literals = (await provisions(client, parent="articulo:2", kind="literal")).json()["items"]

    assert [i["label"] for i in literals] == list("abcdefghi")  # the replacement a-e plus f-i
    assert all(i["page_start"] == 3 for i in literals[:5])


async def test_invalid_paging_and_unknown_ids_return_problem_details(
    stack: Stack,
) -> None:
    client, container = stack
    await container.ingestion.run_ingestion.execute(LEY)
    await container.ingestion.gateway.approve(LEY, "Ana Quispe")

    too_big = await provisions(client, limit=0)
    unknown = await client.get("/api/v1/provisions/00000000-0000-0000-0000-000000000000")
    junk = await client.get("/api/v1/provisions/not-a-uuid")
    other = await client.get("/api/v1/instruments/ley-99999/provisions")

    assert too_big.status_code == 422
    assert too_big.json()["code"] == "validation_error"
    assert (unknown.status_code, junk.status_code, other.status_code) == (404, 404, 404)


@pytest.mark.spec("002-FR-004")
async def test_ingesting_twice_changes_nothing_and_keeps_the_approval(
    stack: Stack,
) -> None:
    client, container = stack
    first = await container.ingestion.run_ingestion.execute(LEY)
    await container.ingestion.gateway.approve(LEY, "Ana Quispe")

    second = await container.ingestion.run_ingestion.execute(LEY)

    assert (first.changed, second.changed) == (True, False)
    assert first.content_digest == second.content_digest
    assert (await provisions(client)).status_code == 200  # approval survived the no-op re-run
