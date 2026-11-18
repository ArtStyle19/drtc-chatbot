"""DocumentStorage adapter: the original PDFs in a local directory (``corpus/sources``).

Security and integrity:

* callers pass a registered file NAME, never a path; the name must be a bare file name;
* the resolved file must live inside the storage root (no symlink escapes);
* the SHA-256 recorded in the manifest is verified before a file is served (constitution I.4);
  the verification is cached per ``(path, mtime, size)`` so a 14 MB file is hashed once.
"""

import hashlib
from pathlib import Path

from drtc_chatbot.shared_kernel.domain import (
    IntegrityViolationError,
    InvariantViolationError,
    NotFoundError,
)

_BLOCK = 1 << 20


class LocalDocumentStorage:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._verified: dict[tuple[str, int, int], str] = {}

    def locate(self, file_name: str, sha256: str) -> tuple[Path, int]:
        if not file_name or Path(file_name).name != file_name or file_name.startswith("."):
            raise InvariantViolationError("Invalid source file name")
        path = (self._root / file_name).resolve()
        if path.parent != self._root:
            raise InvariantViolationError("The source file is outside the corpus storage")
        try:
            stat = path.stat()
        except FileNotFoundError as error:
            raise NotFoundError("The original document is not available on this server") from error
        key = (str(path), stat.st_mtime_ns, stat.st_size)
        if self._verified.get(key) != sha256:
            if self._digest(path) != sha256:
                raise IntegrityViolationError(
                    "The original document does not match its registered SHA-256; not served"
                )
            self._verified[key] = sha256
        return path, stat.st_size

    @staticmethod
    def _digest(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(_BLOCK), b""):
                digest.update(block)
        return digest.hexdigest()
