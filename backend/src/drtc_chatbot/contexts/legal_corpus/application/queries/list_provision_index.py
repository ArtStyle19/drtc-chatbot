"""Use case: every current provision of the latest approved edition, for the reference search."""

from drtc_chatbot.contexts.legal_corpus.application.dto import ProvisionIndex, ProvisionIndexEntry
from drtc_chatbot.contexts.legal_corpus.application.ports import ReadingStore
from drtc_chatbot.contexts.legal_corpus.domain.citations import CitationSubject, short_citation
from drtc_chatbot.contexts.legal_corpus.domain.reading import reading_unit_path
from drtc_chatbot.shared_kernel.application import Actor


class ListProvisionIndex:
    def __init__(self, store: ReadingStore) -> None:
        self._store = store

    async def execute(self, actor: Actor, instrument_id: str) -> ProvisionIndex | None:
        del actor
        edition = await self._store.get_edition(instrument_id, None)
        if edition is None:
            return None
        rows = await self._store.get_index_rows(edition.version_id)
        entries = []
        for row in rows:
            subject = CitationSubject(
                instrument_type=edition.instrument_type,
                number=edition.number,
                title=edition.title,
                edition_label=edition.edition_label,
                consolidated_as_of=edition.consolidated_as_of,
                verification_status=edition.verification_status,
                source_file_name=edition.source_file_name,
                page_start=row.page_start,
                page_end=row.page_start,
            )
            entries.append(
                ProvisionIndexEntry(
                    path=row.path,
                    unit_path=reading_unit_path(row.path),
                    kind=row.kind,
                    label=row.label,
                    title=row.title,
                    snippet=row.snippet,
                    page_start=row.page_start,
                    citation=short_citation(subject, row.path),
                    parent_path=row.parent_path,
                )
            )
        return ProvisionIndex(edition, tuple(entries))
