"""Domain rules of provisions, approvals and the approval policy (no I/O)."""

from datetime import UTC, datetime

import pytest

from drtc_chatbot.bootstrap.settings import Environment, Settings
from drtc_chatbot.contexts.legal_corpus.domain.approval import (
    Approval,
    ApprovalMode,
    ApprovalPolicy,
    ApprovalPolicyName,
    ApprovalStatus,
)
from drtc_chatbot.contexts.legal_corpus.domain.provisions import (
    ProvisionKind,
    ProvisionRevision,
    RevisionStatus,
    validate_revision_set,
)
from drtc_chatbot.shared_kernel.domain import InvariantViolationError

NOW = datetime(2026, 11, 18, tzinfo=UTC)


def rev(
    path: str,
    n: int = 1,
    status: RevisionStatus = RevisionStatus.CURRENT,
    *,
    parent: str | None = None,
    pages: tuple[int, int] = (1, 1),
    ordinal: int = 1,
) -> ProvisionRevision:
    return ProvisionRevision(
        path=path, kind=ProvisionKind.ARTICLE, label=path.rsplit(":", maxsplit=1)[-1], title=None,
        parent_path=parent, text="texto", revision=n, status=status, page_start=pages[0],
        page_end=pages[1], ordinal=ordinal,
    )  # fmt: skip


@pytest.mark.spec("002-FR-003")
def test_two_current_revisions_of_one_path_are_rejected() -> None:
    with pytest.raises(InvariantViolationError, match="more than one current"):
        validate_revision_set([rev("articulo:2", 1), rev("articulo:2", 2)], page_count=36)


@pytest.mark.spec("002-FR-003")
def test_a_superseded_revision_followed_by_a_current_one_is_valid() -> None:
    validate_revision_set(
        [rev("articulo:2", 1, RevisionStatus.SUPERSEDED), rev("articulo:2", 2)], page_count=36
    )


def test_only_the_latest_revision_may_be_current() -> None:
    with pytest.raises(InvariantViolationError, match="only the latest"):
        validate_revision_set(
            [rev("articulo:2", 1), rev("articulo:2", 2, RevisionStatus.SUPERSEDED)], page_count=36
        )


def test_revisions_must_be_numbered_without_gaps() -> None:
    with pytest.raises(InvariantViolationError, match="without gaps"):
        validate_revision_set([rev("articulo:2", 2)], page_count=36)


def test_pages_must_lie_inside_the_source_document() -> None:
    with pytest.raises(InvariantViolationError, match="outside the 36 pages"):
        validate_revision_set([rev("articulo:2", pages=(30, 40))], page_count=36)


def test_parents_must_exist() -> None:
    with pytest.raises(InvariantViolationError, match="unknown parent"):
        validate_revision_set([rev("articulo:2/numeral:2.1", parent="articulo:2")], page_count=36)


def test_an_approval_needs_mode_reviewer_and_date() -> None:
    with pytest.raises(InvariantViolationError):
        Approval(ApprovalStatus.APPROVED)
    with pytest.raises(InvariantViolationError):
        Approval(ApprovalStatus.PENDING, ApprovalMode.HUMAN, "ana", NOW)
    assert Approval.granted(mode=ApprovalMode.HUMAN, by="ana", at=NOW).is_approved
    assert not Approval().is_approved


@pytest.mark.spec("002-FR-005")
@pytest.mark.parametrize("environment", ["staging", "production"])
def test_auto_dev_policy_is_refused_in_protected_environments(environment: str) -> None:
    with pytest.raises(InvariantViolationError, match="not allowed"):
        ApprovalPolicy(ApprovalPolicyName.AUTO_DEV, environment)


def test_manual_policy_never_approves_automatically() -> None:
    assert not ApprovalPolicy(ApprovalPolicyName.MANUAL, "production").approves_automatically
    assert ApprovalPolicy(ApprovalPolicyName.AUTO_DEV, "local").approves_automatically


@pytest.mark.spec("002-FR-005")
def test_settings_default_to_auto_dev_locally_and_manual_when_protected() -> None:
    assert (
        Settings(_env_file=None, environment=Environment.LOCAL).ingestion_approval_policy
        == "auto_dev"
    )
    assert (
        Settings(_env_file=None, environment=Environment.PRODUCTION).ingestion_approval_policy
        == "manual"
    )


@pytest.mark.spec("002-FR-005")
def test_settings_refuse_auto_dev_in_production() -> None:
    with pytest.raises(ValueError, match="not allowed in staging or production"):
        Settings(
            _env_file=None, environment=Environment.PRODUCTION, ingestion_approval_policy="auto_dev"
        )
