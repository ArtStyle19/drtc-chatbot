"""PassageSource over the legal corpus public facade (anticorruption layer)."""

from collections.abc import Sequence

from drtc_chatbot.contexts.legal_corpus.api import ListIndexablePassages, ListLegalInstruments
from drtc_chatbot.contexts.retrieval.domain.chunking import PassageText
from drtc_chatbot.shared_kernel.application import Actor


class LegalCorpusPassages:
    def __init__(self, instruments: ListLegalInstruments, passages: ListIndexablePassages) -> None:
        self._instruments = instruments
        self._passages = passages

    async def passages(self, actor: Actor) -> Sequence[PassageText]:
        result: list[PassageText] = []
        for summary in await self._instruments.execute(actor):
            indexable = await self._passages.execute(actor, summary.instrument_id)
            if indexable is None:  # no approved edition yet
                continue
            result.extend(
                PassageText(
                    instrument_id=summary.instrument_id,
                    version_id=indexable.edition.version_id,
                    path=p.path,
                    unit_path=p.unit_path,
                    kind=p.kind.value,
                    label=p.label,
                    title=p.title,
                    breadcrumb=p.breadcrumb,
                    lead=p.lead,
                    body=p.body,
                    page_start=p.page_start,
                    page_end=p.page_end,
                    citation=p.citation,
                )
                for p in indexable.passages
            )
        return result
