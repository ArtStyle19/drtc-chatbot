"""Use case: the passages of the latest approved edition that the content search indexes.

Every current text of an article, numeral, literal, disposition or annex of an APPROVED edition,
with the context that makes it findable (breadcrumb, lead of its parent) and its short citation.
Replaced texts, editorial notes and explanatory material are not provisions of the corpus and
never appear here.
"""

from drtc_chatbot.contexts.legal_corpus.application.dto import IndexablePassage, IndexablePassages
from drtc_chatbot.contexts.legal_corpus.application.ports import ReadingStore
from drtc_chatbot.contexts.legal_corpus.domain.citations import CitationSubject, short_citation
from drtc_chatbot.contexts.legal_corpus.domain.passages import (
    INDEXABLE_KINDS,
    breadcrumb,
    lead_of,
)
from drtc_chatbot.contexts.legal_corpus.domain.reading import reading_unit_path
from drtc_chatbot.shared_kernel.application import Actor


class ListIndexablePassages:
    def __init__(self, store: ReadingStore) -> None:
        self._store = store

    async def execute(self, actor: Actor, instrument_id: str) -> IndexablePassages | None:
        del actor
        edition = await self._store.get_edition(instrument_id, None)
        if edition is None:
            return None
        rows = await self._store.get_provision_texts(edition.version_id)
        by_path = {row.path: row for row in rows}
        passages = []
        for row in rows:
            body = row.text.strip()
            title = row.title.strip() if row.title else None
            if row.kind not in INDEXABLE_KINDS or not (body or title):
                continue  # containers only give context; an empty provision has nothing to find
            subject = CitationSubject(
                instrument_type=edition.instrument_type,
                number=edition.number,
                title=edition.title,
                edition_label=edition.edition_label,
                consolidated_as_of=edition.consolidated_as_of,
                verification_status=edition.verification_status,
                source_file_name=edition.source_file_name,
                page_start=row.page_start,
                page_end=row.page_end,
            )
            passages.append(
                IndexablePassage(
                    path=row.path,
                    unit_path=reading_unit_path(row.path),
                    kind=row.kind,
                    label=row.label,
                    title=title,
                    breadcrumb=breadcrumb(edition.short_name, row, by_path),
                    lead=lead_of(row, by_path),
                    body=body,
                    page_start=row.page_start,
                    page_end=row.page_end,
                    citation=short_citation(subject, row.path),
                )
            )
        return IndexablePassages(edition, tuple(passages))
