"""Approval of an instrument version: may it be used to answer questions? (not: is it in force)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import ClassVar

from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"


class ApprovalMode(StrEnum):
    HUMAN = "human"
    AUTO_DEV = "auto_dev"  # development convenience only (ADR-0011); never in staging/production


class ApprovalPolicyName(StrEnum):
    MANUAL = "manual"
    AUTO_DEV = "auto_dev"


@dataclass(frozen=True, slots=True)
class Approval:
    """Who approved a version, how and when. Approving never changes the verification status."""

    status: ApprovalStatus = ApprovalStatus.PENDING
    mode: ApprovalMode | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None

    def __post_init__(self) -> None:
        approved = self.status is ApprovalStatus.APPROVED
        if approved and (self.mode is None or not self.approved_by or self.approved_at is None):
            raise InvariantViolationError("An approval needs its mode, reviewer and date")
        if not approved and (self.mode or self.approved_by or self.approved_at):
            raise InvariantViolationError("A pending version cannot carry approval data")

    @property
    def is_approved(self) -> bool:
        return self.status is ApprovalStatus.APPROVED

    @classmethod
    def granted(cls, *, mode: ApprovalMode, by: str, at: datetime) -> Approval:
        return cls(ApprovalStatus.APPROVED, mode, by, at)


@dataclass(frozen=True, slots=True)
class ApprovalPolicy:
    """Decides whether a freshly ingested version is approved automatically."""

    name: ApprovalPolicyName
    environment: str

    _PROTECTED: ClassVar[frozenset[str]] = frozenset({"staging", "production"})

    def __post_init__(self) -> None:
        if self.name is ApprovalPolicyName.AUTO_DEV and self.environment in self._PROTECTED:
            raise InvariantViolationError(
                f"The auto_dev approval policy is not allowed in {self.environment}"
            )

    @property
    def approves_automatically(self) -> bool:
        return self.name is ApprovalPolicyName.AUTO_DEV
