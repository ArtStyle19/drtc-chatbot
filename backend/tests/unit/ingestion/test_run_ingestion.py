"""The ingestion use case with fakes: job states, idempotency, integrity and failures."""

import hashlib
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from drtc_chatbot.contexts.ingestion.application.commands.run_ingestion import RunIngestion
from drtc_chatbot.contexts.ingestion.application.ports import (
    ApprovalOutcome,
    IngestionTarget,
    PublicationResult,
)
from drtc_chatbot.contexts.ingestion.domain.job import IngestionJob, JobStatus
from drtc_chatbot.contexts.ingestion.domain.parsing.model import ParseResult, SourceLine
from drtc_chatbot.shared_kernel.domain import InvariantViolationError, NotFoundError

NOW = datetime(2026, 11, 18, tzinfo=UTC)
TEXT = [
    "Artículo 1.- Del ámbito",
    "1.1 La presente Ley rige en todo el territorio.",
    "Artículo 2.- De las definiciones",
    "Para efectos de la presente Ley se entiende por transporte el desplazamiento.",
]


class Clock:
    def now(self) -> datetime:
        return NOW


class FakeExtractor:
    def extract(self, pdf_path: Path, pages: Sequence[int]) -> list[SourceLine]:
        del pdf_path
        return [SourceLine(pages[0], line) for line in TEXT]


class FakeGateway:
    def __init__(self, target: IngestionTarget, *, auto: bool = False) -> None:
        self.target = target
        self.auto = auto
        self.digests: list[str] = []
        self.published: list[ParseResult] = []

    async def sync_manifest(self) -> int:
        return 1

    async def targets(self) -> list[IngestionTarget]:
        return [self.target]

    async def publish(
        self, target: IngestionTarget, result: ParseResult, content_digest: str
    ) -> PublicationResult:
        del target
        changed = content_digest not in self.digests
        self.digests.append(content_digest)
        self.published.append(result)
        return PublicationResult(changed, len(result.current()), 0)

    async def approve_automatically(self, version_id: str) -> ApprovalOutcome | None:
        del version_id
        return ApprovalOutcome("auto_dev", "system:auto_dev") if self.auto else None

    async def approve(self, version_id: str, reviewer: str) -> ApprovalOutcome:
        del version_id
        return ApprovalOutcome("human", reviewer)


class FakeJobs:
    def __init__(self) -> None:
        self.saved: list[IngestionJob] = []

    async def save(self, job: IngestionJob) -> None:
        self.saved.append(job)

    async def latest(self, version_id: str) -> IngestionJob | None:
        return next((j for j in reversed(self.saved) if j.version_id == version_id), None)


def make_target(
    tmp_path: Path, *, sha: str | None = None, parser: str | None = "ley-lgttt"
) -> IngestionTarget:
    pdf = tmp_path / "ley.pdf"
    pdf.write_bytes(b"%PDF-fake original")
    return IngestionTarget(
        "v1", pdf, sha or hashlib.sha256(pdf.read_bytes()).hexdigest(), 10, ((1, 2),), parser
    )


def use_case(gateway: FakeGateway, jobs: FakeJobs) -> RunIngestion:
    return RunIngestion(gateway, FakeExtractor(), jobs, Clock())  # type: ignore[arg-type]


@pytest.mark.spec("002-FR-001")
async def test_a_successful_run_publishes_and_records_a_published_job(tmp_path: Path) -> None:
    gateway, jobs = FakeGateway(make_target(tmp_path)), FakeJobs()

    outcome = await use_case(gateway, jobs).execute("v1")

    assert outcome.changed
    assert outcome.report.numeric_articles == 2
    assert not outcome.report.needs_attention
    assert outcome.approval is None
    assert [j.status for j in jobs.saved] == [JobStatus.RECEIVED, JobStatus.PUBLISHED]
    assert jobs.saved[-1].content_digest == outcome.content_digest


@pytest.mark.spec("002-FR-004")
async def test_running_twice_gives_the_same_digest_and_changes_nothing(tmp_path: Path) -> None:
    gateway, jobs = FakeGateway(make_target(tmp_path)), FakeJobs()
    ingest = use_case(gateway, jobs)

    first = await ingest.execute("v1")
    second = await ingest.execute("v1")

    assert first.content_digest == second.content_digest
    assert (first.changed, second.changed) == (True, False)


@pytest.mark.spec("002-FR-005")
async def test_the_policy_approval_is_reported(tmp_path: Path) -> None:
    outcome = await use_case(FakeGateway(make_target(tmp_path), auto=True), FakeJobs()).execute(
        "v1"
    )

    assert outcome.approval is not None
    assert outcome.approval.mode == "auto_dev"


@pytest.mark.spec("002-FR-004")
async def test_a_modified_original_is_rejected_and_the_job_fails(tmp_path: Path) -> None:
    jobs = FakeJobs()
    ingest = use_case(FakeGateway(make_target(tmp_path, sha="0" * 64)), jobs)

    with pytest.raises(InvariantViolationError, match="originals are immutable"):
        await ingest.execute("v1")

    assert jobs.saved[-1].status is JobStatus.FAILED
    assert "immutable" in (jobs.saved[-1].error or "")


async def test_unknown_versions_and_missing_parsers_are_reported(tmp_path: Path) -> None:
    with pytest.raises(NotFoundError):
        await use_case(FakeGateway(make_target(tmp_path)), FakeJobs()).execute("nope")
    with pytest.raises(InvariantViolationError, match="no parser profile"):
        await use_case(FakeGateway(make_target(tmp_path, parser=None)), FakeJobs()).execute("v1")
    with pytest.raises(InvariantViolationError, match="Unknown parser profile"):
        await use_case(FakeGateway(make_target(tmp_path, parser="klingon")), FakeJobs()).execute(
            "v1"
        )


def test_the_job_state_machine_only_moves_forward() -> None:
    job = IngestionJob.start("j1", "v1", NOW)

    with pytest.raises(InvariantViolationError):
        job.advance(JobStatus.PUBLISHED, at=NOW)
    parsed = job.advance(JobStatus.EXTRACTED, at=NOW).advance(JobStatus.PARSED, at=NOW)
    assert parsed.fail("boom", at=NOW).status is JobStatus.FAILED
    published = parsed.advance(JobStatus.PUBLISHED, at=NOW)
    with pytest.raises(InvariantViolationError):
        published.fail("late", at=NOW)
