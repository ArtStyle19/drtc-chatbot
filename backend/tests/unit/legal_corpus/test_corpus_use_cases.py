"""Use cases of the legal corpus against in-memory fakes of their ports."""

from datetime import UTC, datetime

import pytest

from drtc_chatbot.contexts.legal_corpus.application.commands.approve_version import (
    ApproveInstrumentVersion,
)
from drtc_chatbot.contexts.legal_corpus.application.commands.publish_provisions import (
    PublishProvisions,
)
from drtc_chatbot.contexts.legal_corpus.application.dto import (
    ProvisionPage,
    PublishDraft,
    PublishOutcome,
    PublishRequest,
    RevisionRequest,
)
from drtc_chatbot.contexts.legal_corpus.application.queries.list_provisions import ListProvisions
from drtc_chatbot.contexts.legal_corpus.domain.approval import (
    Approval,
    ApprovalMode,
    ApprovalPolicy,
    ApprovalPolicyName,
)
from drtc_chatbot.shared_kernel.application import Actor, ActorKind
from drtc_chatbot.shared_kernel.domain import InvariantViolationError, NotFoundError

NOW = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)
ANONYMOUS = Actor("anonymous", ActorKind.ANONYMOUS)


class FixedClock:
    def now(self) -> datetime:
        return NOW


class FakeStore:
    def __init__(self, *, has_version: bool = True, has_provisions: bool = True) -> None:
        self.approvals: dict[str, Approval] = {"v1": Approval()} if has_version else {}
        self._has_provisions = has_provisions
        self.published: list[PublishDraft] = []
        self.page: ProvisionPage | None = None

    async def publish(self, draft: PublishDraft, *, at: datetime) -> PublishOutcome:
        del at
        self.published.append(draft)
        return PublishOutcome(
            draft.version_id, changed=True, revisions=len(draft.revisions), current=1, superseded=0
        )

    async def get_approval(self, version_id: str) -> Approval | None:
        return self.approvals.get(version_id)

    async def set_approval(self, version_id: str, approval: Approval) -> None:
        self.approvals[version_id] = approval

    async def has_provisions(self, version_id: str) -> bool:
        del version_id
        return self._has_provisions

    async def list_provisions(self, instrument_id: str, **_: object) -> ProvisionPage | None:
        del instrument_id
        return self.page

    async def get_provision(self, provision_id: str) -> None:
        del provision_id


def request(*revisions: RevisionRequest, pages: int = 36) -> PublishRequest:
    return PublishRequest("v1", "a" * 64, pages, "digest", tuple(revisions))


def article(
    path: str, n: int = 1, status: str = "current", page: int = 1, kind: str = "article"
) -> RevisionRequest:
    return RevisionRequest(
        path, kind, path.rsplit(":", maxsplit=1)[-1], None, None, "texto", n, status, page, page, n
    )


async def test_publish_validates_before_storing() -> None:
    store = FakeStore()
    use_case = PublishProvisions(store, FixedClock())  # type: ignore[arg-type]

    await use_case.execute(request(article("articulo:1")))
    with pytest.raises(InvariantViolationError):
        await use_case.execute(request(article("articulo:1", page=99)))
    with pytest.raises(InvariantViolationError, match="ProvisionKind"):
        await use_case.execute(request(article("articulo:1", kind="chapter-of-nothing")))

    assert len(store.published) == 1


@pytest.mark.spec("002-FR-005")
async def test_manual_policy_leaves_a_published_version_pending() -> None:
    store = FakeStore()
    approve = ApproveInstrumentVersion(
        store, FixedClock(), ApprovalPolicy(ApprovalPolicyName.MANUAL, "local")
    )  # type: ignore[arg-type]

    assert await approve.apply_policy("v1") is None
    assert not store.approvals["v1"].is_approved


@pytest.mark.spec("002-FR-005")
async def test_auto_dev_policy_records_who_and_how() -> None:
    store = FakeStore()
    approve = ApproveInstrumentVersion(
        store, FixedClock(), ApprovalPolicy(ApprovalPolicyName.AUTO_DEV, "local")
    )  # type: ignore[arg-type]

    result = await approve.apply_policy("v1")

    assert result is not None
    assert result.mode is ApprovalMode.AUTO_DEV
    assert store.approvals["v1"].approved_by == "system:auto_dev"
    assert store.approvals["v1"].approved_at == NOW


@pytest.mark.spec("002-FR-005")
async def test_a_human_approval_needs_a_reviewer_and_ingested_provisions() -> None:
    policy = ApprovalPolicy(ApprovalPolicyName.MANUAL, "production")
    approve = ApproveInstrumentVersion(FakeStore(), FixedClock(), policy)  # type: ignore[arg-type]
    with pytest.raises(InvariantViolationError, match="reviewer"):
        await approve.approve("v1", reviewer="  ")
    with pytest.raises(NotFoundError):
        await ApproveInstrumentVersion(FakeStore(has_version=False), FixedClock(), policy).approve(
            "v1", reviewer="Ana"
        )  # type: ignore[arg-type]
    with pytest.raises(InvariantViolationError, match="no ingested provisions"):
        await ApproveInstrumentVersion(
            FakeStore(has_provisions=False), FixedClock(), policy
        ).approve("v1", reviewer="Ana")  # type: ignore[arg-type]

    store = FakeStore()
    result = await ApproveInstrumentVersion(store, FixedClock(), policy).approve(
        "v1", reviewer=" Ana Quispe "
    )  # type: ignore[arg-type]
    assert (result.mode, result.approved_by) == (ApprovalMode.HUMAN, "Ana Quispe")


@pytest.mark.spec("002-FR-010")
async def test_listing_provisions_of_an_instrument_without_approved_version_is_not_found() -> None:
    with pytest.raises(NotFoundError, match="no approved version"):
        await ListProvisions(FakeStore()).execute(ANONYMOUS, "ley-27181")  # type: ignore[arg-type]


@pytest.mark.parametrize(("limit", "offset"), [(0, 0), (501, 0), (10, -1)])
async def test_paging_arguments_are_validated(limit: int, offset: int) -> None:
    with pytest.raises(InvariantViolationError):
        await ListProvisions(FakeStore()).execute(
            ANONYMOUS, "ley-27181", limit=limit, offset=offset
        )  # type: ignore[arg-type]
