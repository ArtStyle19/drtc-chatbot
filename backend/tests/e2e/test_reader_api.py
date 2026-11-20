"""The reader API over the real Ley 27181 ingested into PostgreSQL (spec 003)."""

import hashlib
import shutil
from pathlib import Path

import httpx
import pytest

from tests.conftest import CORPUS_MANIFEST, REPO_ROOT
from tests.e2e.conftest import LEY, Stack, open_stack

pytestmark = pytest.mark.docker

LEY_PDF = REPO_ROOT / "corpus" / "sources" / "ley-27181-lgttt-texto-2020-06.pdf"
LEY_SHA = hashlib.sha256(LEY_PDF.read_bytes()).hexdigest()
SOURCE = f"/api/v1/versions/{LEY}/source"


async def reading(client: httpx.AsyncClient, path: str, **params: str) -> httpx.Response:
    return await client.get(
        "/api/v1/instruments/ley-27181/reading-unit", params={"path": path, **params}
    )


# ------------------------------------------------------------------ outline
@pytest.mark.spec("003-FR-013")
async def test_nothing_of_the_reader_is_visible_before_approval(stack: Stack) -> None:
    client, container = stack
    await container.ingestion.run_ingestion.execute(LEY)  # published, still pending (manual policy)

    assert (await client.get("/api/v1/instruments/ley-27181/outline")).status_code == 404
    assert (await reading(client, "articulo:2")).status_code == 404
    assert (await client.get(SOURCE)).status_code == 404


@pytest.mark.spec("003-FR-001")
async def test_the_outline_lists_the_structure_in_document_order(approved_ley: Stack) -> None:
    client, _ = approved_ley

    body = (await client.get("/api/v1/instruments/ley-27181/outline")).json()
    entries = body["entries"]
    articles = [e["label"] for e in entries if e["kind"] == "article"]

    assert body["edition"]["verification_status"] == "unverified"
    assert body["edition"]["may_be_presented_as_current"] is False
    assert body["edition"]["source_url"] == SOURCE
    assert articles[:8] == ["1", "2", "3", "4", "4-A", "5", "6", "7"]
    assert len(articles) == 40  # 36 articles + 4-A, 9-A, 16-A, 26-A
    kinds = {e["kind"] for e in entries}
    assert kinds <= {"section", "title", "chapter", "article", "disposition", "annex"}
    assert entries[0]["kind"] == "title"
    assert all(e["page_start"] >= 1 for e in entries)
    article_2 = next(e for e in entries if e["path"] == "articulo:2")
    assert article_2["unit_path"] == "articulo:2"
    assert article_2["title"] == "De las definiciones"


async def test_the_outline_of_an_unknown_norm_or_edition_is_not_found(approved_ley: Stack) -> None:
    client, _ = approved_ley

    assert (await client.get("/api/v1/instruments/ley-99999/outline")).status_code == 404
    other = await client.get("/api/v1/instruments/ley-27181/outline", params={"version_id": "nope"})
    assert other.status_code == 404


# ------------------------------------------------------------------ reading unit
@pytest.mark.spec("003-FR-002")
async def test_a_literal_opens_its_article_with_the_whole_subtree(approved_ley: Stack) -> None:
    client, _ = approved_ley

    body = (await reading(client, "articulo:2/literal:e")).json()
    paths = [n["path"] for n in body["nodes"]]

    assert body["requested_path"] == "articulo:2/literal:e"
    assert body["unit_path"] == "articulo:2"
    assert paths[0] == "articulo:2"
    assert paths[1:] == [f"articulo:2/literal:{letter}" for letter in "abcdefghi"]
    literal_e = next(n for n in body["nodes"] if n["path"] == "articulo:2/literal:e")
    assert literal_e["parent_path"] == "articulo:2"
    assert literal_e["current"]["citation"]["short"] == "Ley N.° 27181, art. 2, lit. e)"
    assert literal_e["current"]["page_start"] == 3


@pytest.mark.spec("003-FR-004")
async def test_the_replaced_text_is_only_in_history_and_cited_as_not_in_force(
    approved_ley: Stack,
) -> None:
    client, _ = approved_ley

    article = (await reading(client, "articulo:2")).json()["nodes"][0]

    assert article["revision_count"] == 2
    assert article["current"]["revision"] == 2
    assert article["current"]["event"]["kind"] == "substituted"
    assert "Decreto de Urgencia" in article["current"]["event"]["source"]
    [old] = article["history"]
    assert old["revision"] == 1
    assert old["page_start"] == 2
    assert old["citation"]["short"].endswith("(texto sustituido)")
    assert "no vigente" in old["citation"]["formal"]
    assert "Decreto de Urgencia" in old["citation"]["formal"]
    assert "no vigente" not in article["current"]["citation"]["formal"]


@pytest.mark.spec("003-FR-003")
async def test_formal_citations_state_the_edition_and_never_claim_force(
    approved_ley: Stack,
) -> None:
    client, _ = approved_ley

    nodes = (await reading(client, "articulo:15")).json()["nodes"]

    for node in nodes:
        formal = node["current"]["citation"]["formal"]
        assert "edición no verificada frente a la fuente oficial" in formal
        assert "Fuente: ley-27181-lgttt-texto-2020-06.pdf" in formal
        assert "verificado como vigente" not in formal


@pytest.mark.spec("003-FR-005")
async def test_an_unapplied_paragraph_replacement_is_a_visible_warning(approved_ley: Stack) -> None:
    client, _ = approved_ley

    article_23 = (await reading(client, "articulo:23")).json()["nodes"][0]

    [warning] = article_23["warnings"]
    assert warning["code"] == "paragraph_replacement_unapplied"
    assert "párrafo" in warning["message"]
    assert any(n["kind"] == "amendment" for n in article_23["notes"])
    plain = (await reading(client, "articulo:1")).json()["nodes"][0]
    assert plain["warnings"] == []


@pytest.mark.spec("003-FR-011")
async def test_notes_are_separate_from_the_text(approved_ley: Stack) -> None:
    client, _ = approved_ley

    article_3 = (await reading(client, "articulo:3")).json()["nodes"][0]

    assert any(
        n["kind"] == "concordance" and "035-2006-MTC" in n["text"] for n in article_3["notes"]
    )
    assert "035-2006" not in article_3["current"]["text"]


@pytest.mark.spec("003-FR-009")
async def test_nodes_carry_boxes_inside_their_pages(approved_ley: Stack) -> None:
    client, _ = approved_ley

    for node in (await reading(client, "articulo:2")).json()["nodes"]:
        boxes = node["current"]["boxes"]
        assert boxes, node["path"]
        for box in boxes:
            assert node["current"]["page_start"] <= box["page"] <= node["current"]["page_end"]
            assert 0 <= box["x0"] < box["x1"] <= 600
            assert 0 <= box["y0"] < box["y1"] <= 850


async def test_a_container_opens_itself_and_lists_its_children(approved_ley: Stack) -> None:
    client, _ = approved_ley

    body = (await reading(client, "titulo:I")).json()

    assert body["unit_path"] == "titulo:I"
    assert [n["path"] for n in body["nodes"]] == ["titulo:I"]
    assert [c["label"] for c in body["children"]][:3] == ["1", "2", "3"]


async def test_a_disposition_opens_with_its_literals(approved_ley: Stack) -> None:
    client, _ = approved_ley

    body = (await reading(client, "disposiciones:finales/tercera")).json()

    assert body["unit_path"] == "disposiciones:finales/tercera"
    assert body["nodes"][0]["current"]["title"].startswith("Ámbito de aplicación")


async def test_unknown_paths_and_editions_are_not_found(approved_ley: Stack) -> None:
    client, _ = approved_ley

    assert (await reading(client, "articulo:999")).status_code == 404
    assert (await reading(client, "articulo:2", version_id="nope")).status_code == 404
    assert (await client.get("/api/v1/instruments/ley-27181/reading-unit")).status_code == 422
    assert (await reading(client, "")).status_code == 422


# ------------------------------------------------------------------ source PDF
@pytest.mark.spec("003-FR-006")
async def test_the_original_pdf_is_served_with_its_hash_as_etag(approved_ley: Stack) -> None:
    client, _ = approved_ley

    response = await client.get(SOURCE)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.headers["etag"] == f'"{LEY_SHA}"'
    assert response.headers["accept-ranges"] == "bytes"
    assert response.headers["content-disposition"].startswith("inline")
    assert response.content == LEY_PDF.read_bytes()


@pytest.mark.spec("003-FR-006")
async def test_the_pdf_supports_range_requests_so_the_viewer_loads_only_what_it_shows(
    approved_ley: Stack,
) -> None:
    client, _ = approved_ley

    response = await client.get(SOURCE, headers={"Range": "bytes=0-99"})

    assert response.status_code == 206
    assert response.headers["content-range"] == f"bytes 0-99/{LEY_PDF.stat().st_size}"
    assert response.content == LEY_PDF.read_bytes()[:100]


async def test_a_conditional_request_gets_not_modified(approved_ley: Stack) -> None:
    client, _ = approved_ley

    response = await client.get(SOURCE, headers={"If-None-Match": f'"{LEY_SHA}"'})

    assert response.status_code == 304


@pytest.mark.spec("003-FR-006")
async def test_the_client_cannot_choose_a_file(approved_ley: Stack) -> None:
    client, _ = approved_ley

    for attempt in (
        "../manifest.yaml",
        "..%2F..%2Fetc%2Fpasswd",
        "tuo-ley-27444@ds-004-2019-jus-ed2021",
    ):
        assert (await client.get(f"/api/v1/versions/{attempt}/source")).status_code == 404


@pytest.mark.spec("003-FR-006")
async def test_an_altered_original_is_never_served(clean_database: str, tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    (corpus / "sources").mkdir(parents=True)
    shutil.copy(CORPUS_MANIFEST, corpus / "manifest.yaml")
    copy = corpus / "sources" / LEY_PDF.name
    shutil.copy(LEY_PDF, copy)

    async with open_stack(clean_database, corpus_manifest_path=corpus / "manifest.yaml") as (
        client,
        container,
    ):
        await container.ingestion.run_ingestion.execute(LEY)
        await container.ingestion.gateway.approve(LEY, "Ana Quispe")
        assert (await client.get(SOURCE)).status_code == 200

        with copy.open("ab") as stream:
            stream.write(b"\n%tampered")
        response = await client.get(SOURCE)

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "integrity_violation"
    assert "SHA-256" not in body["detail"]  # no internal details for the client
    assert body["request_id"]


@pytest.mark.parametrize(
    "header",
    [f'W/"{LEY_SHA}"', f'"other", "{LEY_SHA}"', "*"],
    ids=["weak", "list", "star"],
)
async def test_conditional_request_variants(approved_ley: Stack, header: str) -> None:
    client, _ = approved_ley

    assert (await client.get(SOURCE, headers={"If-None-Match": header})).status_code == 304


async def test_a_different_etag_gets_the_file(approved_ley: Stack) -> None:
    client, _ = approved_ley

    response = await client.get(SOURCE, headers={"If-None-Match": '"stale"'})

    assert response.status_code == 200
