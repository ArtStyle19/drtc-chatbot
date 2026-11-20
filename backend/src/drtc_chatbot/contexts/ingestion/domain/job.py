"""Ingestion job: the state machine of one run over one instrument version."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from typing import Any

from drtc_chatbot.shared_kernel.domain import InvariantViolationError


class JobStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTED = "extracted"
    PARSED = "parsed"
    PUBLISHED = "published"
    FAILED = "failed"


_NEXT = {
    JobStatus.RECEIVED: {JobStatus.EXTRACTED},
    JobStatus.EXTRACTED: {JobStatus.PARSED},
    JobStatus.PARSED: {JobStatus.PUBLISHED},
}


@dataclass(frozen=True, slots=True)
class IngestionJob:
    """Immutable snapshot; every transition returns a new one (``advance``/``fail``)."""

    job_id: str
    version_id: str
    status: JobStatus
    started_at: datetime
    finished_at: datetime | None = None
    content_digest: str | None = None
    changed: bool | None = None
    report: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @classmethod
    def start(cls, job_id: str, version_id: str, at: datetime) -> IngestionJob:
        return cls(job_id, version_id, JobStatus.RECEIVED, at)

    def advance(self, status: JobStatus, *, at: datetime, **changes: Any) -> IngestionJob:
        if status not in _NEXT.get(self.status, set()):
            raise InvariantViolationError(f"Illegal ingestion transition {self.status} -> {status}")
        finished = at if status is JobStatus.PUBLISHED else None
        return replace(self, status=status, finished_at=finished, **changes)

    def fail(self, error: str, *, at: datetime) -> IngestionJob:
        if self.status in {JobStatus.PUBLISHED, JobStatus.FAILED}:
            raise InvariantViolationError(f"A {self.status} job cannot fail")
        return replace(self, status=JobStatus.FAILED, finished_at=at, error=error)
