"""CorpusGateway adapter: the ingestion talks to the legal corpus only through its public facade."""

from drtc_chatbot.contexts.ingestion.application.ports import (
    ApprovalOutcome,
    IngestionTarget,
    PublicationResult,
)
from drtc_chatbot.contexts.ingestion.domain.parsing.model import ParseResult
from drtc_chatbot.contexts.legal_corpus.api import (
    ApproveInstrumentVersion,
    EventRequest,
    ManifestSnapshot,
    NoteDraft,
    PublishProvisions,
    PublishRequest,
    RevisionRequest,
    SyncCorpusManifest,
    ingestion_targets,
)


class LegalCorpusGateway:
    def __init__(
        self,
        sync: SyncCorpusManifest,
        publish: PublishProvisions,
        approve: ApproveInstrumentVersion,
    ) -> None:
        self._sync = sync
        self._publish = publish
        self._approve = approve
        self._snapshot: ManifestSnapshot | None = None

    async def sync_manifest(self) -> int:
        self._snapshot = await self._sync.execute()
        return len(self._snapshot.versions)

    async def targets(self) -> list[IngestionTarget]:
        if self._snapshot is None:
            await self.sync_manifest()
        assert self._snapshot is not None  # noqa: S101
        return [
            IngestionTarget(
                version_id=t.version_id,
                source_file=t.source_file,
                sha256=t.sha256,
                page_count=t.page_count,
                normative_pages=t.normative_pages,
                parser=t.parser,
            )
            for t in ingestion_targets(self._snapshot)
        ]

    async def publish(
        self, target: IngestionTarget, result: ParseResult, content_digest: str
    ) -> PublicationResult:
        request = PublishRequest(
            version_id=target.version_id,
            source_sha256=target.sha256,
            page_count=target.page_count,
            content_digest=content_digest,
            revisions=tuple(
                RevisionRequest(
                    path=p.path,
                    kind=p.kind.value,
                    label=p.label,
                    title=p.title,
                    parent_path=p.parent_path,
                    text=p.text,
                    revision=p.revision,
                    status=p.status.value,
                    page_start=p.page_start,
                    page_end=p.page_end,
                    ordinal=p.ordinal,
                    boxes=tuple((b.page, b.x0, b.y0, b.x1, b.y1) for b in p.boxes),
                    event=(
                        EventRequest(p.event.kind.value, p.event.source, p.event.published_on)
                        if p.event
                        else None
                    ),
                )
                for p in result.provisions
            ),
            notes=tuple(NoteDraft(n.kind.value, n.text, n.page, n.path) for n in result.notes),
        )
        outcome = await self._publish.execute(request)
        return PublicationResult(outcome.changed, outcome.current, outcome.superseded)

    async def approve_automatically(self, version_id: str) -> ApprovalOutcome | None:
        granted = await self._approve.apply_policy(version_id)
        return None if granted is None else ApprovalOutcome(granted.mode.value, granted.approved_by)

    async def approve(self, version_id: str, reviewer: str) -> ApprovalOutcome:
        granted = await self._approve.approve(version_id, reviewer=reviewer)
        return ApprovalOutcome(granted.mode.value, granted.approved_by)
