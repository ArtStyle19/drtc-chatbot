"""PostgreSQL adapter for the reader: edition, outline, reading units, source file and index.

Everything here reads APPROVED editions only (spec 003, FR-013). Provisions are ordered by the
document position of their FIRST revision, so a text that a later norm replaced stays where the
provision belongs in the document instead of jumping to where the replacement is quoted.
"""

from collections import defaultdict
from collections.abc import Sequence

from sqlalchemy import Subquery, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import aliased

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    EditionContext,
    IndexRow,
    NoteDraft,
    OutlineEntry,
    RawNode,
    RawRevision,
    SourceRef,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import ApprovalMode
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    PageBox,
    ProvisionKind,
    ReviewFlag,
    RevisionStatus,
)
from drtc_chatbot.contexts.legal_corpus.domain.reading import reading_unit_path
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentType,
    VerificationStatus,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.models import (
    EditorialNoteRow,
    InstrumentRow,
    ProvisionRevisionRow,
    ProvisionRow,
    SourceDocumentRow,
    VersionRow,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.sql_store import event_from_json

OUTLINE_KINDS = (
    ProvisionKind.SECTION,
    ProvisionKind.TITLE,
    ProvisionKind.CHAPTER,
    ProvisionKind.ARTICLE,
    ProvisionKind.DISPOSITION,
    ProvisionKind.ANNEX,
)
SNIPPET_LENGTH = 160


def _revision(row: ProvisionRevisionRow) -> RawRevision:
    return RawRevision(
        revision=row.revision,
        title=row.title,
        text=row.text,
        page_start=row.page_start,
        page_end=row.page_end,
        boxes=tuple(PageBox(*box) for box in row.boxes),
        event=event_from_json(row.event),
    )


class SqlReadingStore:
    """Implements the ReadingStore port."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    # ------------------------------------------------------------------ edition
    async def get_edition(
        self, instrument_id: str, version_id: str | None
    ) -> EditionContext | None:
        query = (
            select(VersionRow, InstrumentRow, SourceDocumentRow)
            .join(InstrumentRow, InstrumentRow.id == VersionRow.instrument_id)
            .join(SourceDocumentRow, SourceDocumentRow.id == VersionRow.source_document_id)
            .where(
                VersionRow.instrument_id == instrument_id, VersionRow.approval_status == "approved"
            )
            .order_by(VersionRow.ordinal.desc())
            .limit(1)
        )
        if version_id is not None:
            query = query.where(VersionRow.id == version_id)
        async with self._sessions() as session:
            row = (await session.execute(query)).first()
        if row is None:
            return None
        version, instrument, source = row
        return EditionContext(
            instrument_id=instrument.id,
            instrument_type=InstrumentType(instrument.instrument_type),
            number=instrument.number,
            title=instrument.title,
            short_name=instrument.short_name,
            version_id=version.id,
            edition_label=version.edition_label,
            consolidated_as_of=version.consolidated_as_of,
            verification_status=VerificationStatus(version.verification_status),
            approval_mode=ApprovalMode(version.approval_mode or ""),
            source_file_name=source.file_name,
            page_count=source.page_count,
            alerts=tuple(version.alerts),
        )

    # ------------------------------------------------------------------ outline
    @staticmethod
    def _first_ordinals(version_id: str) -> Subquery:
        return (
            select(
                ProvisionRevisionRow.provision_id.label("provision_id"),
                func.min(ProvisionRevisionRow.ordinal).label("first_ordinal"),
            )
            .where(ProvisionRevisionRow.instrument_version_id == version_id)
            .group_by(ProvisionRevisionRow.provision_id)
            .subquery()
        )

    async def _entries(
        self, session: AsyncSession, version_id: str, *parent_path: str
    ) -> list[OutlineEntry]:
        first = self._first_ordinals(version_id)
        parent = aliased(ProvisionRow)
        query = (
            select(ProvisionRow, ProvisionRevisionRow, parent.structural_path)
            .join(ProvisionRevisionRow, ProvisionRevisionRow.provision_id == ProvisionRow.id)
            .join(first, first.c.provision_id == ProvisionRow.id)
            .outerjoin(parent, parent.id == ProvisionRow.parent_id)
            .where(
                ProvisionRevisionRow.instrument_version_id == version_id,
                ProvisionRevisionRow.status == RevisionStatus.CURRENT.value,
            )
            .order_by(first.c.first_ordinal)
        )
        if parent_path:
            query = query.where(parent.structural_path == parent_path[0])
        else:
            query = query.where(ProvisionRow.kind.in_([k.value for k in OUTLINE_KINDS]))
        rows = (await session.execute(query)).all()
        return [
            OutlineEntry(
                path=provision.structural_path,
                kind=ProvisionKind(provision.kind),
                label=provision.label,
                title=revision.title,
                parent_path=parent_structural_path,
                page_start=revision.page_start,
                unit_path=reading_unit_path(provision.structural_path),
            )
            for provision, revision, parent_structural_path in rows
        ]

    async def get_outline_entries(self, version_id: str) -> Sequence[OutlineEntry]:
        async with self._sessions() as session:
            return await self._entries(session, version_id)

    async def get_child_entries(self, version_id: str, parent_path: str) -> Sequence[OutlineEntry]:
        async with self._sessions() as session:
            return await self._entries(session, version_id, parent_path)

    # ------------------------------------------------------------------ reading unit
    async def get_reading_nodes(self, version_id: str, unit_path: str) -> Sequence[RawNode]:
        parent = aliased(ProvisionRow)
        async with self._sessions() as session:
            rows = (
                await session.execute(
                    select(ProvisionRow, ProvisionRevisionRow, parent.structural_path)
                    .join(
                        ProvisionRevisionRow, ProvisionRevisionRow.provision_id == ProvisionRow.id
                    )
                    .outerjoin(parent, parent.id == ProvisionRow.parent_id)
                    .where(
                        ProvisionRevisionRow.instrument_version_id == version_id,
                        (ProvisionRow.structural_path == unit_path)
                        | ProvisionRow.structural_path.startswith(unit_path + "/", autoescape=True),
                    )
                )
            ).all()
            paths = {provision.structural_path for provision, _, _ in rows}
            notes = (
                (
                    await session.scalars(
                        select(EditorialNoteRow)
                        .where(
                            EditorialNoteRow.instrument_version_id == version_id,
                            EditorialNoteRow.provision_path.in_(paths),
                        )
                        .order_by(EditorialNoteRow.page, EditorialNoteRow.id)
                    )
                ).all()
                if paths
                else []
            )
        by_path: dict[str, list[tuple[ProvisionRow, ProvisionRevisionRow, str | None]]] = (
            defaultdict(list)
        )
        for provision, revision, parent_path in rows:
            by_path[provision.structural_path].append((provision, revision, parent_path))
        notes_by_path: dict[str, list[NoteDraft]] = defaultdict(list)
        for note in notes:
            notes_by_path[note.provision_path or ""].append(
                NoteDraft(note.kind, note.text, note.page, note.provision_path)
            )

        nodes: list[tuple[int, RawNode]] = []
        for path, items in by_path.items():
            ordered = sorted(items, key=lambda item: item[1].revision)
            current = next(
                (r for _, r, _ in ordered if r.status == RevisionStatus.CURRENT.value), None
            )
            if current is None:
                continue  # only replaced text: not part of the current reading
            provision, _, parent_of = ordered[0]
            first_ordinal = min(r.ordinal for _, r, _ in ordered)
            nodes.append(
                (
                    first_ordinal,
                    RawNode(
                        path=path,
                        kind=ProvisionKind(provision.kind),
                        label=provision.label,
                        parent_path=parent_of,
                        revision_count=len(ordered),
                        current=_revision(current),
                        history=tuple(
                            _revision(r)
                            for _, r, _ in ordered
                            if r.status == RevisionStatus.SUPERSEDED.value
                        ),
                        review_flags=tuple(ReviewFlag(flag) for flag in current.review_flags),
                        notes=tuple(notes_by_path.get(path, ())),
                    ),
                )
            )
        return [node for _, node in sorted(nodes, key=lambda pair: pair[0])]

    # ------------------------------------------------------------------ source and index
    async def get_source_ref(self, version_id: str) -> SourceRef | None:
        async with self._sessions() as session:
            row = (
                await session.execute(
                    select(VersionRow, SourceDocumentRow)
                    .join(SourceDocumentRow, SourceDocumentRow.id == VersionRow.source_document_id)
                    .where(VersionRow.id == version_id, VersionRow.approval_status == "approved")
                )
            ).first()
        if row is None:
            return None
        version, source = row
        return SourceRef(version.id, source.file_name, source.sha256, source.page_count)

    async def get_index_rows(self, version_id: str) -> Sequence[IndexRow]:
        first = self._first_ordinals(version_id)
        parent = aliased(ProvisionRow)
        async with self._sessions() as session:
            rows = (
                await session.execute(
                    select(
                        ProvisionRow,
                        ProvisionRevisionRow.title,
                        func.left(ProvisionRevisionRow.text, SNIPPET_LENGTH),
                        ProvisionRevisionRow.page_start,
                        parent.structural_path,
                    )
                    .join(
                        ProvisionRevisionRow, ProvisionRevisionRow.provision_id == ProvisionRow.id
                    )
                    .join(first, first.c.provision_id == ProvisionRow.id)
                    .outerjoin(parent, parent.id == ProvisionRow.parent_id)
                    .where(
                        ProvisionRevisionRow.instrument_version_id == version_id,
                        ProvisionRevisionRow.status == RevisionStatus.CURRENT.value,
                    )
                    .order_by(first.c.first_ordinal)
                )
            ).all()
        return [
            IndexRow(
                path=provision.structural_path,
                kind=ProvisionKind(provision.kind),
                label=provision.label,
                title=title,
                snippet=snippet or "",
                page_start=page_start,
                parent_path=parent_path,
            )
            for provision, title, snippet, page_start, parent_path in rows
        ]
