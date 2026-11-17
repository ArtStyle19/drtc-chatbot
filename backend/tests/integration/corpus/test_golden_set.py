"""The golden set must point to real versions, real pages and text that is really there."""

import json
import re
import shutil
import subprocess
from functools import cache
from pathlib import Path
from typing import Any

import pytest

from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_catalog import load_manifest
from tests.conftest import CORPUS_MANIFEST, REPO_ROOT

DATASETS = sorted((REPO_ROOT / "evaluation" / "datasets").glob("*.jsonl"))
REQUIRED_KEYS = {"id", "question", "intent", "audience", "answerable", "expected", "review_status"}


def _questions() -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for dataset in DATASETS:
        for line in dataset.read_text(encoding="utf-8").splitlines():
            if line.strip():
                questions.append(json.loads(line))
    return questions


def _versions() -> dict[str, tuple[Path, int]]:
    manifest = load_manifest(CORPUS_MANIFEST)
    sources = {source.id: source for source in manifest.sources}
    return {
        version.id: (
            CORPUS_MANIFEST.parent / sources[version.source].file,
            sources[version.source].page_count,
        )
        for instrument in manifest.instruments
        for version in instrument.versions
    }


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("-\n", "")).strip()


@cache
def _page_text(pdf: Path, page: int) -> str:
    result = subprocess.run(  # noqa: S603 - fixed binary, paths from the manifest
        ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],  # noqa: S607
        capture_output=True,
        check=True,
        text=True,
    )
    return _normalize(result.stdout)


def test_golden_questions_are_well_formed_and_unique() -> None:
    questions = _questions()

    assert questions, "The golden set is empty"
    for question in questions:
        assert question.keys() >= REQUIRED_KEYS, f"{question.get('id')} lacks required keys"
        assert question["review_status"] in {"draft", "reviewed", "approved"}
        citations = question["expected"]["citations"]
        assert bool(citations) == question["answerable"], (
            f"{question['id']}: citations vs answerable"
        )
    ids = [question["id"] for question in questions]
    assert len(ids) == len(set(ids)), "Duplicated golden question ids"


def test_citations_point_to_existing_versions_and_pages() -> None:
    versions = _versions()
    for question in _questions():
        for citation in question["expected"]["citations"]:
            assert citation["version_id"] in versions, f"{question['id']}: unknown version"
            _, page_count = versions[citation["version_id"]]
            assert all(1 <= page <= page_count for page in citation["pdf_pages"]), question["id"]


@pytest.mark.skipif(shutil.which("pdftotext") is None, reason="pdftotext (poppler) not installed")
def test_supporting_text_appears_on_the_cited_pages() -> None:
    versions = _versions()
    for question in _questions():
        for citation in question["expected"]["citations"]:
            pdf, _ = versions[citation["version_id"]]
            pages_text = " ".join(_page_text(pdf, page) for page in citation["pdf_pages"])
            assert _normalize(citation["supporting_text"]) in pages_text, (
                f"{question['id']}: supporting text not found on pages {citation['pdf_pages']}"
            )
