"""The PDF storage refuses anything that is not exactly the registered original."""

import hashlib
from pathlib import Path

import pytest

from drtc_chatbot.contexts.legal_corpus.infrastructure.local_document_storage import (
    LocalDocumentStorage,
)
from drtc_chatbot.shared_kernel.domain import (
    IntegrityViolationError,
    InvariantViolationError,
    NotFoundError,
)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "ley.pdf").write_bytes(b"%PDF-original")
    return sources


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.mark.spec("003-FR-006")
def test_a_registered_original_with_the_right_hash_is_served(root: Path) -> None:
    path, size = LocalDocumentStorage(root).locate("ley.pdf", sha(b"%PDF-original"))

    assert path == (root / "ley.pdf").resolve()
    assert size == len(b"%PDF-original")


@pytest.mark.spec("003-FR-006")
def test_an_altered_original_is_refused_even_after_it_was_verified_once(root: Path) -> None:
    storage = LocalDocumentStorage(root)
    storage.locate("ley.pdf", sha(b"%PDF-original"))

    (root / "ley.pdf").write_bytes(b"%PDF-original + tampering")  # size changes: the cache key too

    with pytest.raises(IntegrityViolationError):
        storage.locate("ley.pdf", sha(b"%PDF-original"))


@pytest.mark.spec("003-FR-006")
@pytest.mark.parametrize(
    "name", ["../secret.pdf", "/etc/passwd", "sub/ley.pdf", "..", ".hidden", ""]
)
def test_only_bare_file_names_are_accepted(root: Path, name: str) -> None:
    with pytest.raises(InvariantViolationError):
        LocalDocumentStorage(root).locate(name, "0" * 64)


def test_a_symlink_that_escapes_the_storage_is_refused(root: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(b"%PDF-outside")
    (root / "link.pdf").symlink_to(outside)

    with pytest.raises(InvariantViolationError, match="outside"):
        LocalDocumentStorage(root).locate("link.pdf", sha(b"%PDF-outside"))


def test_a_missing_file_is_reported_as_not_available(root: Path) -> None:
    with pytest.raises(NotFoundError, match="not available"):
        LocalDocumentStorage(root).locate("missing.pdf", "0" * 64)
