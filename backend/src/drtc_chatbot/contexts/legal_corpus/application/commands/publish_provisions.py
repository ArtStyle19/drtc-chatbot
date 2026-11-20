"""Use case: store the provisions parsed from a source document as an instrument version."""

from drtc_chatbot.contexts.legal_corpus.application.dto import (
    PublishDraft,
    PublishOutcome,
    PublishRequest,
    RevisionRequest,
)
from drtc_chatbot.contexts.legal_corpus.application.ports import ProvisionStore
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    EventKind,
    LegalEvent,
    PageBox,
    ProvisionKind,
    ProvisionRevision,
    RevisionStatus,
    validate_revision_set,
)
from drtc_chatbot.shared_kernel.application import Clock
from drtc_chatbot.shared_kernel.domain import InvariantViolationError


def _to_domain(request: RevisionRequest) -> ProvisionRevision:
    try:
        return ProvisionRevision(
            path=request.path,
            kind=ProvisionKind(request.kind),
            label=request.label,
            title=request.title,
            parent_path=request.parent_path,
            text=request.text,
            revision=request.revision,
            status=RevisionStatus(request.status),
            page_start=request.page_start,
            page_end=request.page_end,
            ordinal=request.ordinal,
            boxes=tuple(PageBox(*box) for box in request.boxes),
            event=(
                LegalEvent(
                    EventKind(request.event.kind), request.event.source, request.event.published_on
                )
                if request.event
                else None
            ),
        )
    except ValueError as error:
        raise InvariantViolationError(f"{request.path}: {error}") from error


class PublishProvisions:
    """Validates the invariants (one current text per path, pages in range) and stores.

    Publishing the same ``content_digest`` again is a no-op. Publishing never approves: the
    version stays pending until ``ApproveInstrumentVersion`` runs.
    """

    def __init__(self, store: ProvisionStore, clock: Clock) -> None:
        self._store = store
        self._clock = clock

    async def execute(self, request: PublishRequest) -> PublishOutcome:
        revisions = tuple(_to_domain(item) for item in request.revisions)
        validate_revision_set(revisions, page_count=request.page_count)
        draft = PublishDraft(
            version_id=request.version_id,
            source_sha256=request.source_sha256,
            page_count=request.page_count,
            content_digest=request.content_digest,
            revisions=revisions,
            notes=request.notes,
        )
        return await self._store.publish(draft, at=self._clock.now())
