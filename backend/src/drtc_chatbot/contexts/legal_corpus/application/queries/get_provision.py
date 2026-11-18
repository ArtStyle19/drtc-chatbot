"""Use case: read one provision (all its revisions) of an approved version."""

from drtc_chatbot.contexts.legal_corpus.application.dto import ProvisionDetail
from drtc_chatbot.contexts.legal_corpus.application.ports import ProvisionStore
from drtc_chatbot.shared_kernel.application import Actor
from drtc_chatbot.shared_kernel.domain import NotFoundError


class GetProvision:
    def __init__(self, store: ProvisionStore) -> None:
        self._store = store

    async def execute(self, actor: Actor, provision_id: str) -> ProvisionDetail:
        del actor
        detail = await self._store.get_provision(provision_id)
        if detail is None:
            raise NotFoundError(f"Provision not found: {provision_id}")
        return detail
