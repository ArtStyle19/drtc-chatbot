"""Use case: the unit the reader shows for a path, with citations, history, notes and warnings."""

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionContext,
    RawNode,
    RawRevision,
    ReadingNode,
    ReadingRevision,
    ReadingUnit,
    ReviewWarning,
)
from drtc_chatbot.contexts.legal_corpus.application.ports import ReadingStore
from drtc_chatbot.contexts.legal_corpus.domain.citations import CitationSubject, format_citation
from drtc_chatbot.contexts.legal_corpus.domain.provisions import REVIEW_FLAG_MESSAGES
from drtc_chatbot.contexts.legal_corpus.domain.reading import is_container_path, reading_unit_path
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import NotFoundError


def _subject(edition: EditionContext, revision: RawRevision, **replaced: object) -> CitationSubject:
    return CitationSubject(
        instrument_type=edition.instrument_type,
        number=edition.number,
        title=edition.title,
        edition_label=edition.edition_label,
        consolidated_as_of=edition.consolidated_as_of,
        verification_status=edition.verification_status,
        source_file_name=edition.source_file_name,
        page_start=revision.page_start,
        page_end=revision.page_end,
        **replaced,  # type: ignore[arg-type]
    )


def _reading_revision(
    edition: EditionContext, path: str, revision: RawRevision, **replaced: object
) -> ReadingRevision:
    return ReadingRevision(
        revision=revision.revision,
        title=revision.title,
        text=revision.text,
        page_start=revision.page_start,
        page_end=revision.page_end,
        boxes=revision.boxes,
        event=revision.event,
        citation=format_citation(_subject(edition, revision, **replaced), path),
    )


def build_node(edition: EditionContext, node: RawNode) -> ReadingNode:
    """Attach citations; a replaced text is cited as such (and by what replaced it, if known)."""
    sequence = [*node.history, node.current]
    history = []
    for position, old in enumerate(node.history):
        replacement = sequence[position + 1]
        history.append(
            _reading_revision(
                edition, node.path, old, superseded=True, superseded_by=replacement.event
            )
        )
    return ReadingNode(
        path=node.path,
        kind=node.kind,
        label=node.label,
        parent_path=node.parent_path,
        revision_count=node.revision_count,
        current=_reading_revision(edition, node.path, node.current),
        history=tuple(history),
        warnings=tuple(ReviewWarning(f.value, REVIEW_FLAG_MESSAGES[f]) for f in node.review_flags),
        notes=node.notes,
    )


class GetReadingUnit:
    """The reader opens the article, disposition or annex that contains the requested path."""

    def __init__(self, store: ReadingStore) -> None:
        self._store = store

    async def execute(
        self, actor: Actor, instrument_id: str, path: str, *, version_id: str | None = None
    ) -> ReadingUnit:
        del actor
        edition = await self._store.get_edition(instrument_id, version_id)
        if edition is None:
            raise NotFoundError(f"{instrument_id} has no approved edition")
        unit_path = reading_unit_path(path)
        nodes = await self._store.get_reading_nodes(edition.version_id, unit_path)
        if not nodes:
            raise NotFoundError(f"{path} does not exist in {edition.edition_label}")
        children = (
            tuple(await self._store.get_child_entries(edition.version_id, unit_path))
            if is_container_path(unit_path)
            else ()
        )
        return ReadingUnit(
            edition=edition,
            requested_path=path,
            unit_path=unit_path,
            nodes=tuple(build_node(edition, node) for node in nodes),
            children=children,
        )
