"""EditionCatalog over the legal corpus public facade (anticorruption layer)."""

from collections.abc import Mapping

from drtc_chatbot.contexts.legal_corpus.api import ListApprovedEditions
from drtc_chatbot.contexts.retrieval.application.ports import EditionInfo
from drtc_chatbot.shared_kernel.application import Actor


class LegalCorpusEditions:
    def __init__(self, approved: ListApprovedEditions) -> None:
        self._approved = approved

    async def editions(self, actor: Actor) -> Mapping[str, EditionInfo]:
        return {
            e.version_id: EditionInfo(
                instrument_id=e.instrument_id,
                instrument_short_name=e.short_name,
                instrument_title=e.title,
                version_id=e.version_id,
                edition_label=e.edition_label,
                verification_status=e.verification_status.value,
            )
            for e in await self._approved.execute(actor)
        }
