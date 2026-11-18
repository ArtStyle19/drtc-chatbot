"""Use case: list the current provisions of an approved version of a norm."""

from drtc_chatbot.contexts.legal_corpus.application.dto import ProvisionPage
from drtc_chatbot.contexts.legal_corpus.application.ports import ProvisionStore
from drtc_chatbot.contexts.legal_corpus.domain.provisions import ProvisionKind
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import InvariantViolationError, NotFoundError

MAX_PAGE_SIZE = 500


class ListProvisions:
    """Only approved versions are readable; pending ones stay invisible (spec 002, FR-010)."""

    def __init__(self, store: ProvisionStore) -> None:
        self._store = store

    async def execute(
        self,
        actor: Actor,
        instrument_id: str,
        *,
        version_id: str | None = None,
        kind: ProvisionKind | None = None,
        parent_path: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> ProvisionPage:
        del actor  # readable by every actor, anonymous included (ADR-0007)
        if not 1 <= limit <= MAX_PAGE_SIZE or offset < 0:
            raise InvariantViolationError(f"limit must be 1-{MAX_PAGE_SIZE} and offset >= 0")
        page = await self._store.list_provisions(
            instrument_id,
            version_id=version_id,
            kind=kind,
            parent_path=parent_path,
            limit=limit,
            offset=offset,
        )
        if page is None:
            raise NotFoundError(
                f"{instrument_id} has no approved version"
                + (f" {version_id}" if version_id else "")
                + " with ingested provisions"
            )
        return page
