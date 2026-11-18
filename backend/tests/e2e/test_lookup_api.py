"""GET /api/v1/lookup over the three real norms (spec 003, US3), including the golden set."""

import json
from typing import Any

import httpx
import pytest

from tests.conftest import REPO_ROOT
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker


async def lookup(client: httpx.AsyncClient, query: str) -> dict[str, Any]:
    response = await client.get("/api/v1/lookup", params={"q": query})
    assert response.status_code == 200, response.text
    return dict(response.json())


@pytest.mark.spec("003-FR-007")
async def test_references_resolve_across_the_three_real_norms(full_corpus: str) -> None:
    async with open_stack(full_corpus) as (client, _):
        literal = await lookup(client, "lit. e del art. 2 de la Ley 27181")
        equivalent = [
            await lookup(client, q)
            for q in (
                "art. 5 Ley 27181",
                "artículo 5 de la LGTTT",
                "Ley 27181 art 5",
                "ART. 5° LEY N° 27181",
            )
        ]
        numeral = await lookup(client, "218.2 TUO")
        annex = await lookup(client, "anexo 2 RENAT")
        disposition = await lookup(client, "primera disposición complementaria final RENAT")
        title = await lookup(client, "título IV TUO")
        preliminary = await lookup(client, "artículo IV del Título Preliminar del TUO")
        in_title = await lookup(client, "art 229 capítulo I título IV LPAG")
        wrong_title = await lookup(client, "art 229 título II LPAG")

    assert literal["status"] == "resolved"
    assert literal["hits"][0]["path"] == "articulo:2/literal:e"
    assert literal["hits"][0]["unit_path"] == "articulo:2"
    assert literal["hits"][0]["citation"] == "Ley N.° 27181, art. 2, lit. e)"
    assert literal["hits"][0]["verification_status"] == "unverified"
    paths = {
        (r["hits"][0]["instrument_id"], r["hits"][0]["path"], r["hits"][0]["version_id"])
        for r in equivalent
    }
    assert paths == {("ley-27181", "articulo:5", "ley-27181@2020-05")}
    assert numeral["hits"][0]["path"] == "articulo:218/numeral:218.2"
    assert numeral["hits"][0]["page_start"] == 236
    assert annex["hits"][0]["path"] == "anexo:2"
    assert annex["hits"][0]["page_start"] == 170
    assert disposition["status"] == "resolved"
    assert disposition["hits"][0]["path"].endswith("disposiciones:complementarias-finales/primera")
    assert title["hits"][0]["path"] == "titulo:IV"
    assert preliminary["status"] == "resolved"
    assert preliminary["hits"][0]["path"] == "articulo:IV"
    assert in_title["hits"][0]["path"] == "articulo:229"
    assert wrong_title["status"] == "not_found"


@pytest.mark.spec("003-FR-007")
async def test_ambiguous_missing_unknown_and_free_text_cases(full_corpus: str) -> None:
    async with open_stack(full_corpus) as (client, _):
        ambiguous = await lookup(client, "art. 11")
        both = await lookup(client, "art 4-A lit a ley 27181")
        missing = await lookup(client, "art. 999 ley 27181")
        unknown = await lookup(client, "art 5 ley 99999")
        free = await lookup(client, "transporte de mercancías")
        norm = await lookup(client, "LPAG")
        too_long = await client.get("/api/v1/lookup", params={"q": "x" * 201})
        empty = await client.get("/api/v1/lookup", params={"q": ""})
        absent = await client.get("/api/v1/lookup")

    assert ambiguous["status"] == "ambiguous"
    assert [h["instrument_id"] for h in ambiguous["hits"]] == [
        "ley-27181",
        "ds-017-2009-mtc",
        "tuo-ley-27444",
    ]
    assert ambiguous["norms"] == []  # nothing was chosen for the person
    assert both["status"] == "ambiguous"
    assert len(both["hits"]) >= 2
    assert missing["status"] == "not_found"
    assert missing["reference"] == "art. 999"
    assert "no tiene «art. 999»" in missing["message"]
    assert unknown["status"] == "not_found"
    assert "No reconozco la norma" in unknown["message"]
    assert unknown["hits"] == []
    assert free["status"] == "unrecognized"
    assert "solo busco por referencia" in free["message"]
    assert (norm["status"], norm["hits"][0]["instrument_id"], norm["hits"][0]["path"]) == (
        "resolved",
        "tuo-ley-27444",
        None,
    )
    assert (too_long.status_code, empty.status_code, absent.status_code) == (422, 422, 422)


@pytest.mark.spec("003-SC-003")
async def test_every_golden_citation_is_resolved_by_reference_to_its_exact_path_and_page(
    full_corpus: str,
) -> None:
    dataset = REPO_ROOT / "evaluation" / "datasets" / "golden-v1.jsonl"
    questions = [
        json.loads(line)
        for line in dataset.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    cases = [
        (c["provision"], c["version_id"], c["path"], set(c["pdf_pages"]))
        for q in questions
        for c in q["expected"]["citations"]
        if c["path"] is not None  # null = not a provision of the ingested corpus (e.g. a preamble)
    ]
    assert len(cases) >= 8

    unresolved = []
    async with open_stack(full_corpus) as (client, _):
        for provision, version_id, path, pages in cases:
            result = await lookup(client, provision)
            hit = result["hits"][0] if result["hits"] else None
            if (
                result["status"] != "resolved"
                or hit["version_id"] != version_id
                or hit["path"] != path
                or hit["page_start"] not in pages
            ):
                unresolved.append(
                    (provision, result["status"], hit and hit["path"], hit and hit["page_start"])
                )

    assert unresolved == []
