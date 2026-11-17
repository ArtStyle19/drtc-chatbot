import httpx
import pytest


@pytest.mark.spec("001-FR-002")
async def test_lists_the_corpus_instruments(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/instruments")

    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == ["ley-27181", "ds-017-2009-mtc", "tuo-ley-27444"]


@pytest.mark.spec("001-FR-003")
async def test_every_edition_is_reported_as_unverified(client: httpx.AsyncClient) -> None:
    items = (await client.get("/api/v1/instruments")).json()["items"]

    for item in items:
        edition = item["current_edition"]
        assert edition["verification_status"] == "unverified"
        assert edition["may_be_presented_as_current"] is False
        assert edition["edition_label"]


async def test_the_renat_edition_carries_its_consolidation_date(client: httpx.AsyncClient) -> None:
    items = (await client.get("/api/v1/instruments")).json()["items"]
    renat = next(item for item in items if item["id"] == "ds-017-2009-mtc")

    assert renat["current_edition"]["consolidated_as_of"] == "2017-01-04"
    assert renat["current_edition"]["alerts"]
