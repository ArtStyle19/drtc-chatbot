"""Use case: load the manifest (instruments, versions, source documents) into the corpus."""

from drtc_chatbot.contexts.legal_corpus.application.dto import ManifestSnapshot
from drtc_chatbot.contexts.legal_corpus.application.ports import InstrumentRegistry, ManifestReader


class SyncCorpusManifest:
    """Idempotent; never touches provisions or approvals."""

    def __init__(self, reader: ManifestReader, registry: InstrumentRegistry) -> None:
        self._reader = reader
        self._registry = registry

    async def execute(self) -> ManifestSnapshot:
        snapshot = self._reader.read()
        await self._registry.sync(snapshot)
        return snapshot
