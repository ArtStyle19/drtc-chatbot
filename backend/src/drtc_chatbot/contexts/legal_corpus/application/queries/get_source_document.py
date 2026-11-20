"""Use case: the original PDF of an approved edition, verified against its SHA-256."""

from drtc_chatbot.contexts.legal_corpus.application.dto import SourceDocument
from drtc_chatbot.contexts.legal_corpus.application.ports import DocumentStorage, ReadingStore
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import NotFoundError


class GetSourceDocument:
    """Only editions that are approved can be downloaded (pending ones stay invisible, FR-013)."""

    def __init__(self, store: ReadingStore, storage: DocumentStorage) -> None:
        self._store = store
        self._storage = storage

    async def execute(self, actor: Actor, version_id: str) -> SourceDocument:
        del actor
        ref = await self._store.get_source_ref(version_id)
        if ref is None:
            raise NotFoundError(f"No approved edition {version_id}")
        path, size = self._storage.locate(ref.file_name, ref.sha256)
        return SourceDocument(ref.version_id, ref.file_name, ref.sha256, path, size)
