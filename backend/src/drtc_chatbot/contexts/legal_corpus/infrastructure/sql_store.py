"""PostgreSQL adapter of the legal corpus: catalog, registry, provisions and approvals."""

import uuid
from collections.abc import Sequence
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    ManifestSnapshot,
    NoteDraft,
    ProvisionDetail,
    ProvisionPage,
    ProvisionRevisionDetail,
    ProvisionSummary,
    PublishDraft,
    PublishOutcome,
)
from drtc_chatbot.contexts.legal_corpus.domain.approval import (
    Approval,
    ApprovalMode,
    ApprovalStatus,
)
from drtc_chatbot.contexts.legal_corpus.domain.legal_instrument import (
    InstrumentVersion,
    LegalInstrument,
    SourceDocumentRef,
)
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    EventKind,
    LegalEvent,
    PageBox,
    ProvisionKind,
    ProvisionRevision,
    RevisionStatus,
)
from drtc_chatbot.contexts.legal_corpus.domain.value_objects import (
    InstrumentId,
    InstrumentType,
    PageRange,
    PageRole,
    PageSection,
    Sha256Digest,
    VerificationStatus,
    VersionId,
)
from drtc_chatbot.contexts.legal_corpus.infrastructure.models import (
    EditorialNoteRow,
    InstrumentRow,
    ProvisionRevisionRow,
    ProvisionRow,
    SourceDocumentRow,
    VersionRow,
)
from drtc_chatbot.shared_kernel.domain import InvariantViolationError, NotFoundError


def _event_to_json(event: LegalEvent | None) -> dict[str, Any] | None:
    if event is None:
        return None
    return {
        "kind": event.kind.value,
        "source": event.source,
        "published_on": event.published_on.isoformat() if event.published_on else None,
    }


def _event_from_json(data: dict[str, Any] | None) -> LegalEvent | None:
    if not data:
        return None
    published = data.get("published_on")
    return LegalEvent(
        EventKind(data["kind"]),
        data["source"],
        date.fromisoformat(published) if published else None,
    )


def _approval_from_row(row: VersionRow) -> Approval:
    if row.approval_status != ApprovalStatus.APPROVED.value:
        return Approval()
    return Approval.granted(
        mode=ApprovalMode(row.approval_mode or ""),
        by=row.approved_by or "",
        at=row.approved_at or datetime.min.replace(tzinfo=UTC),
    )


class SqlLegalCorpusStore:
    """Implements LegalInstrumentCatalog, InstrumentRegistry, ProvisionStore and ApprovalStore."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    # ------------------------------------------------------------------ catalog
    async def list_instruments(self) -> Sequence[LegalInstrument]:
        async with self._sessions() as session:
            instruments = (
                await session.scalars(select(InstrumentRow).order_by(InstrumentRow.ordinal))
            ).all()
            versions = (
                await session.scalars(
                    select(VersionRow).order_by(VersionRow.instrument_id, VersionRow.ordinal)
                )
            ).all()
            sources = {s.id: s for s in (await session.scalars(select(SourceDocumentRow))).all()}
            counts = dict(
                (
                    await session.execute(
                        select(ProvisionRevisionRow.instrument_version_id, func.count())
                        .where(ProvisionRevisionRow.status == RevisionStatus.CURRENT.value)
                        .group_by(ProvisionRevisionRow.instrument_version_id)
                    )
                ).all()
            )
        result = []
        for instrument in instruments:
            owned = [v for v in versions if v.instrument_id == instrument.id]
            if not owned:
                continue  # an instrument without versions cannot be shown yet
            result.append(
                LegalInstrument(
                    InstrumentId(instrument.id),
                    instrument_type=InstrumentType(instrument.instrument_type),
                    number=instrument.number,
                    title=instrument.title,
                    short_name=instrument.short_name,
                    issuing_authority=instrument.issuing_authority,
                    publication_date=instrument.publication_date,
                    aliases=tuple(instrument.aliases),
                    versions=[
                        self._version(v, sources[v.source_document_id], counts) for v in owned
                    ],
                )
            )
        return result

    @staticmethod
    def _version(
        row: VersionRow, source: SourceDocumentRow, counts: dict[str, int]
    ) -> InstrumentVersion:
        return InstrumentVersion(
            version_id=VersionId(row.id),
            edition_label=row.edition_label,
            verification_status=VerificationStatus(row.verification_status),
            source=SourceDocumentRef(
                source_id=source.id,
                file_name=source.file_name,
                sha256=Sha256Digest(source.sha256),
                page_count=source.page_count,
            ),
            consolidated_as_of=row.consolidated_as_of,
            consolidation_note=row.consolidation_note,
            page_sections=tuple(
                PageSection(PageRole(role), PageRange(first, last))
                for role, first, last in row.page_sections
            ),
            alerts=tuple(row.alerts),
            approval=_approval_from_row(row),
            provision_count=counts.get(row.id, 0),
        )

    # ------------------------------------------------------------------ registry (manifest sync)
    async def sync(self, snapshot: ManifestSnapshot) -> None:
        async with self._sessions.begin() as session:
            for source in snapshot.sources:
                existing = await session.get(SourceDocumentRow, source.source_id)
                if existing is not None and existing.sha256 != source.sha256:
                    raise InvariantViolationError(
                        f"Source document {source.source_id} changed: originals are immutable "
                        "(register a new document and a new version instead)"
                    )
                await session.execute(
                    pg_insert(SourceDocumentRow)
                    .values(
                        id=source.source_id,
                        file_name=source.file_name,
                        sha256=source.sha256,
                        page_count=source.page_count,
                    )
                    .on_conflict_do_nothing(index_elements=["id"])
                )
            for position, instrument in enumerate(snapshot.instruments, start=1):
                values = {
                    "ordinal": position,
                    "instrument_type": instrument.instrument_type.value,
                    "number": instrument.number,
                    "title": instrument.title,
                    "short_name": instrument.short_name,
                    "issuing_authority": instrument.issuing_authority,
                    "publication_date": instrument.publication_date,
                    "aliases": list(instrument.aliases),
                }
                await session.execute(
                    pg_insert(InstrumentRow)
                    .values(id=instrument.instrument_id, **values)
                    .on_conflict_do_update(index_elements=["id"], set_=values)
                )
            for version in snapshot.versions:
                owned = {
                    "instrument_id": version.instrument_id,
                    "source_document_id": version.source_id,
                    "ordinal": version.ordinal,
                    "edition_label": version.edition_label,
                    "consolidated_as_of": version.consolidated_as_of,
                    "consolidation_note": version.consolidation_note,
                    "verification_status": version.verification_status.value,
                    "parser": version.parser,
                    "page_sections": [list(section) for section in version.page_sections],
                    "alerts": list(version.alerts),
                }
                await session.execute(
                    pg_insert(VersionRow)
                    .values(id=version.version_id, approval_status="pending", **owned)
                    .on_conflict_do_update(
                        index_elements=["id"], set_=owned
                    )  # keeps approval + content
                )

    # ------------------------------------------------------------------ provisions: publish
    async def publish(self, draft: PublishDraft, *, at: datetime) -> PublishOutcome:
        async with self._sessions.begin() as session:
            version = await session.get(VersionRow, draft.version_id)
            if version is None:
                raise NotFoundError(f"Unknown instrument version: {draft.version_id}")
            source = await session.get(SourceDocumentRow, version.source_document_id)
            if source is None or source.sha256 != draft.source_sha256:
                raise InvariantViolationError(
                    f"{draft.version_id}: the parsed file does not match the registered "
                    "source (SHA-256)"
                )
            current = sum(r.status is RevisionStatus.CURRENT for r in draft.revisions)
            outcome = PublishOutcome(
                draft.version_id,
                changed=True,
                revisions=len(draft.revisions),
                current=current,
                superseded=len(draft.revisions) - current,
            )
            stored = await session.scalar(
                select(func.count())
                .select_from(ProvisionRevisionRow)
                .where(ProvisionRevisionRow.instrument_version_id == draft.version_id)
            )
            if version.content_digest == draft.content_digest and stored:
                return PublishOutcome(
                    draft.version_id,
                    changed=False,
                    revisions=outcome.revisions,
                    current=current,
                    superseded=outcome.superseded,
                )

            await session.execute(
                delete(ProvisionRevisionRow).where(
                    ProvisionRevisionRow.instrument_version_id == draft.version_id
                )
            )
            await session.execute(
                delete(EditorialNoteRow).where(
                    EditorialNoteRow.instrument_version_id == draft.version_id
                )
            )
            ids = await self._upsert_provisions(session, version.instrument_id, draft)
            session.add_all(
                ProvisionRevisionRow(
                    provision_id=ids[r.path],
                    instrument_version_id=draft.version_id,
                    revision=r.revision,
                    status=r.status.value,
                    title=r.title,
                    text=r.text,
                    page_start=r.page_start,
                    page_end=r.page_end,
                    ordinal=r.ordinal,
                    boxes=[[b.page, b.x0, b.y0, b.x1, b.y1] for b in r.boxes],
                    event=_event_to_json(r.event),
                    review_flags=[flag.value for flag in r.review_flags],
                )
                for r in draft.revisions
            )
            session.add_all(
                EditorialNoteRow(
                    instrument_version_id=draft.version_id,
                    provision_path=n.path,
                    kind=n.kind,
                    text=n.text,
                    page=n.page,
                )
                for n in draft.notes
            )
            # New content must be approved again; the verification status is never touched here.
            await session.execute(
                update(VersionRow)
                .where(VersionRow.id == draft.version_id)
                .values(
                    content_digest=draft.content_digest,
                    published_at=at,
                    approval_status="pending",
                    approval_mode=None,
                    approved_by=None,
                    approved_at=None,
                )
            )
            return outcome

    @staticmethod
    async def _upsert_provisions(
        session: AsyncSession, instrument_id: str, draft: PublishDraft
    ) -> dict[str, uuid.UUID]:
        existing = {
            row.structural_path: row.id
            for row in (
                await session.scalars(
                    select(ProvisionRow).where(ProvisionRow.instrument_id == instrument_id)
                )
            ).all()
        }
        first_seen: dict[str, ProvisionRevision] = {}
        for revision in sorted(draft.revisions, key=lambda r: r.ordinal):
            first_seen.setdefault(revision.path, revision)
        for path, revision in first_seen.items():
            if path in existing:
                continue
            parent_id = existing.get(revision.parent_path) if revision.parent_path else None
            row = ProvisionRow(
                instrument_id=instrument_id,
                structural_path=path,
                kind=revision.kind.value,
                label=revision.label,
                parent_id=parent_id,
            )
            session.add(row)
            await session.flush()
            existing[path] = row.id
        return existing

    # ------------------------------------------------------------------ provisions: read
    async def _readable_version(
        self, session: AsyncSession, instrument_id: str, version_id: str | None
    ) -> VersionRow | None:
        query = (
            select(VersionRow)
            .where(
                VersionRow.instrument_id == instrument_id, VersionRow.approval_status == "approved"
            )
            .order_by(VersionRow.ordinal.desc())
        )
        if version_id is not None:
            query = query.where(VersionRow.id == version_id)
        return (await session.scalars(query.limit(1))).first()

    async def list_provisions(
        self,
        instrument_id: str,
        *,
        version_id: str | None,
        kind: ProvisionKind | None,
        parent_path: str | None,
        limit: int,
        offset: int,
    ) -> ProvisionPage | None:
        async with self._sessions() as session:
            version = await self._readable_version(session, instrument_id, version_id)
            if version is None:
                return None
            parent = ProvisionRow.__table__.alias("parent")
            filters = [
                ProvisionRevisionRow.instrument_version_id == version.id,
                ProvisionRevisionRow.status == RevisionStatus.CURRENT.value,
            ]
            if kind is not None:
                filters.append(ProvisionRow.kind == kind.value)
            base = (
                select(ProvisionRevisionRow, ProvisionRow, parent.c.structural_path)
                .join(ProvisionRow, ProvisionRow.id == ProvisionRevisionRow.provision_id)
                .outerjoin(parent, parent.c.id == ProvisionRow.parent_id)
                .where(*filters)
            )
            if parent_path is not None:
                base = base.where(parent.c.structural_path == parent_path)
            total = await session.scalar(select(func.count()).select_from(base.subquery())) or 0
            rows = (
                await session.execute(
                    base.order_by(ProvisionRevisionRow.ordinal).limit(limit).offset(offset)
                )
            ).all()
            ids = [revision.provision_id for revision, _, _ in rows]
            history = dict(
                (
                    await session.execute(
                        select(ProvisionRevisionRow.provision_id, func.count())
                        .where(
                            ProvisionRevisionRow.instrument_version_id == version.id,
                            ProvisionRevisionRow.provision_id.in_(ids),
                        )
                        .group_by(ProvisionRevisionRow.provision_id)
                    )
                ).all()
            )
            items = tuple(
                ProvisionSummary(
                    provision_id=str(provision.id),
                    path=provision.structural_path,
                    kind=ProvisionKind(provision.kind),
                    label=provision.label,
                    title=revision.title,
                    parent_path=parent_structural_path,
                    text=revision.text,
                    page_start=revision.page_start,
                    page_end=revision.page_end,
                    ordinal=revision.ordinal,
                    revision=revision.revision,
                    revision_count=history.get(provision.id, 1),
                    event=_event_from_json(revision.event),
                )
                for revision, provision, parent_structural_path in rows
            )
            return ProvisionPage(
                instrument_id=instrument_id,
                version_id=version.id,
                edition_label=version.edition_label,
                verification_status=VerificationStatus(version.verification_status),
                approval_mode=ApprovalMode(version.approval_mode or ""),
                total=total,
                items=items,
            )

    async def get_provision(self, provision_id: str) -> ProvisionDetail | None:
        try:
            key = uuid.UUID(provision_id)
        except ValueError:
            return None
        async with self._sessions() as session:
            provision = await session.get(ProvisionRow, key)
            if provision is None:
                return None
            version = await self._readable_version(session, provision.instrument_id, None)
            version_key: str = version.id if version else ""
            revisions = (
                (
                    await session.scalars(
                        select(ProvisionRevisionRow)
                        .where(
                            ProvisionRevisionRow.provision_id == key,
                            ProvisionRevisionRow.instrument_version_id == version_key,
                        )
                        .order_by(ProvisionRevisionRow.revision)
                    )
                ).all()
                if version
                else []
            )
            if version is None or not revisions:
                return None
            parent_path = (
                await session.scalar(
                    select(ProvisionRow.structural_path).where(
                        ProvisionRow.id == provision.parent_id
                    )
                )
                if provision.parent_id
                else None
            )
            notes = (
                await session.scalars(
                    select(EditorialNoteRow).where(
                        EditorialNoteRow.instrument_version_id == version.id,
                        EditorialNoteRow.provision_path == provision.structural_path,
                    )
                )
            ).all()
            return ProvisionDetail(
                provision_id=str(provision.id),
                instrument_id=provision.instrument_id,
                version_id=version.id,
                edition_label=version.edition_label,
                verification_status=VerificationStatus(version.verification_status),
                approval_mode=ApprovalMode(version.approval_mode or ""),
                path=provision.structural_path,
                kind=ProvisionKind(provision.kind),
                label=provision.label,
                parent_path=parent_path,
                revisions=tuple(
                    ProvisionRevisionDetail(
                        revision=r.revision,
                        status=RevisionStatus(r.status),
                        title=r.title,
                        text=r.text,
                        page_start=r.page_start,
                        page_end=r.page_end,
                        boxes=tuple(PageBox(*box) for box in r.boxes),
                        event=_event_from_json(r.event),
                    )
                    for r in revisions
                ),
                notes=tuple(NoteDraft(n.kind, n.text, n.page, n.provision_path) for n in notes),
            )

    # ------------------------------------------------------------------ approvals
    async def get_approval(self, version_id: str) -> Approval | None:
        async with self._sessions() as session:
            row = await session.get(VersionRow, version_id)
            return None if row is None else _approval_from_row(row)

    async def set_approval(self, version_id: str, approval: Approval) -> None:
        async with self._sessions.begin() as session:
            await session.execute(
                update(VersionRow)
                .where(VersionRow.id == version_id)
                .values(
                    approval_status=approval.status.value,
                    approval_mode=approval.mode.value if approval.mode else None,
                    approved_by=approval.approved_by,
                    approved_at=approval.approved_at,
                )
            )

    async def has_provisions(self, version_id: str) -> bool:
        async with self._sessions() as session:
            found = await session.scalar(
                select(func.count())
                .select_from(ProvisionRevisionRow)
                .where(ProvisionRevisionRow.instrument_version_id == version_id)
            )
            return bool(found)
