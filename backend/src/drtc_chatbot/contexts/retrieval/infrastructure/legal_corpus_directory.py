"""ProvisionDirectory over the legal corpus public facade (anticorruption layer)."""

from collections.abc import Sequence

from drtc_chatbot.contexts.legal_corpus.api import ListLegalInstruments, ListProvisionIndex
from drtc_chatbot.contexts.retrieval.application.ports import IndexedEdition, IndexedProvision
from drtc_chatbot.contexts.retrieval.domain.norms import NormInfo
from drtc_chatbot.shared_kernel.application import Actor


class LegalCorpusDirectory:
    def __init__(self, instruments: ListLegalInstruments, index: ListProvisionIndex) -> None:
        self._instruments = instruments
        self._index = index

    async def norms(self, actor: Actor) -> Sequence[NormInfo]:
        return [
            NormInfo(
                instrument_id=summary.instrument_id,
                instrument_type=summary.instrument_type.value,
                number=summary.number,
                title=summary.title,
                short_name=summary.short_name,
                aliases=summary.aliases,
            )
            for summary in await self._instruments.execute(actor)
        ]

    async def edition(self, actor: Actor, instrument_id: str) -> IndexedEdition | None:
        index = await self._index.execute(actor, instrument_id)
        if index is None:
            return None
        return IndexedEdition(
            version_id=index.edition.version_id,
            edition_label=index.edition.edition_label,
            verification_status=index.edition.verification_status.value,
            entries=tuple(
                IndexedProvision(
                    path=e.path,
                    unit_path=e.unit_path,
                    kind=e.kind.value,
                    label=e.label,
                    title=e.title,
                    snippet=e.snippet,
                    page_start=e.page_start,
                    citation=e.citation,
                    parent_path=e.parent_path,
                )
                for e in index.entries
            ),
        )
