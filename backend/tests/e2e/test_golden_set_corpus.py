"""The golden set must point at provisions that REALLY exist in the ingested corpus (spec 004).

Complements ``tests/integration/corpus/test_golden_set.py`` (which checks the PDF pages): here every
expected ``path`` must exist in its edition, include the cited pages, and contain the supporting text
(itself or one of its descendants: an article's text may live in its numerals).
"""

import json
import re
from typing import Any

import httpx
import pytest

from tests.conftest import REPO_ROOT
from tests.e2e.conftest import open_stack

pytestmark = pytest.mark.docker

DATASET = REPO_ROOT / "evaluation" / "datasets" / "golden-v1.jsonl"


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _citations() -> list[tuple[str, dict[str, Any]]]:
    questions = [
        json.loads(line)
        for line in DATASET.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [
        (q["id"], c) for q in questions for c in q["expected"]["citations"] if c["path"] is not None
    ]


async def _unit(client: httpx.AsyncClient, instrument: str, citation: dict[str, Any]) -> Any:
    response = await client.get(
        f"/api/v1/instruments/{instrument}/reading-unit",
        params={"path": citation["path"], "version_id": citation["version_id"]},
    )
    assert response.status_code == 200, (citation["path"], response.text)
    return response.json()


@pytest.mark.spec("004-FR-002")
async def test_every_expected_path_exists_with_its_pages_and_supporting_text(
    full_corpus: str,
) -> None:
    problems: list[str] = []
    async with open_stack(full_corpus) as (client, _):
        for question_id, citation in _citations():
            instrument = citation["version_id"].split("@")[0]
            unit = await _unit(client, instrument, citation)
            nodes = [
                n
                for n in unit["nodes"]
                if n["path"] == citation["path"] or n["path"].startswith(citation["path"] + "/")
            ]
            if not any(n["path"] == citation["path"] for n in nodes):
                problems.append(f"{question_id}: {citation['path']} does not exist")
                continue
            own = next(n for n in nodes if n["path"] == citation["path"])
            pages = set(citation["pdf_pages"])
            covered = set(range(own["current"]["page_start"], own["current"]["page_end"] + 1))
            if not pages & covered:
                problems.append(f"{question_id}: pages {sorted(pages)} not in {sorted(covered)}")
            wanted = _normalize(citation["supporting_text"])
            if not any(wanted in _normalize(n["current"]["text"]) for n in nodes):
                problems.append(
                    f"{question_id}: supporting text not found under {citation['path']}"
                )

    assert problems == []
