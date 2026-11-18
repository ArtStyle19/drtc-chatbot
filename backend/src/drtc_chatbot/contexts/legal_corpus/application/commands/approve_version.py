"""Use cases: approve an instrument version so it can be read and used to answer questions."""

from drtc_chatbot.contexts.legal_corpus.application.dto import ApprovalResult
from drtc_chatbot.contexts.legal_corpus.application.ports import ApprovalStore
from drtc_chatbot.contexts.legal_corpus.domain.approval import (
    Approval,
    ApprovalMode,
    ApprovalPolicy,
)
from drtc_chatbot.shared_kernel.application import Clock
from drtc_chatbot.shared_kernel.domain import InvariantViolationError, NotFoundError

AUTO_REVIEWER = "system:auto_dev"


class ApproveInstrumentVersion:
    """Records who approved a version, how and when. Approving is NOT verifying: the verification
    status (is the text in force?) is untouched."""

    def __init__(self, store: ApprovalStore, clock: Clock, policy: ApprovalPolicy) -> None:
        self._store = store
        self._clock = clock
        self._policy = policy

    async def approve(self, version_id: str, *, reviewer: str) -> ApprovalResult:
        if not reviewer.strip():
            raise InvariantViolationError("A human approval needs the reviewer's name")
        return await self._grant(version_id, ApprovalMode.HUMAN, reviewer.strip())

    async def apply_policy(self, version_id: str) -> ApprovalResult | None:
        """Approve automatically if the (development-only) policy allows it; else do nothing."""
        if not self._policy.approves_automatically:
            return None
        return await self._grant(version_id, ApprovalMode.AUTO_DEV, AUTO_REVIEWER)

    async def _grant(self, version_id: str, mode: ApprovalMode, reviewer: str) -> ApprovalResult:
        if await self._store.get_approval(version_id) is None:
            raise NotFoundError(f"Unknown instrument version: {version_id}")
        if not await self._store.has_provisions(version_id):
            raise InvariantViolationError(
                f"{version_id} has no ingested provisions: run the ingestion before approving it"
            )
        now = self._clock.now()
        await self._store.set_approval(version_id, Approval.granted(mode=mode, by=reviewer, at=now))
        return ApprovalResult(version_id, mode, reviewer, now)
