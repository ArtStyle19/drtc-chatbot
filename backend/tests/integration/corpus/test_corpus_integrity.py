"""The original PDFs are immutable: their bytes must match the manifest (spec 001, FR-004)."""

import hashlib
from pathlib import Path

import pytest

from drtc_chatbot.contexts.legal_corpus.infrastructure.manifest_catalog import load_manifest
from tests.conftest import CORPUS_MANIFEST

CORPUS_ROOT = CORPUS_MANIFEST.parent


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


@pytest.mark.spec("001-FR-004")
def test_every_source_file_matches_its_recorded_sha256() -> None:
    for source in load_manifest(CORPUS_MANIFEST).sources:
        path = CORPUS_ROOT / source.file
        assert path.is_file(), f"Missing source file {source.file}"
        assert _sha256(path) == source.sha256, f"{source.file} changed: originals are immutable"


@pytest.mark.spec("001-FR-004")
def test_every_file_in_sources_is_registered_in_the_manifest() -> None:
    registered = {Path(source.file).name for source in load_manifest(CORPUS_MANIFEST).sources}
    on_disk = {path.name for path in (CORPUS_ROOT / "sources").glob("*.pdf")}

    assert on_disk == registered
