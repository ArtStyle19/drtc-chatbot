"""Use case: turn one instrument version's PDF into stored, reviewable provisions."""

import hashlib
import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from drtc_chatbot.contexts.ingestion.application.ports import (
    ApprovalOutcome,
    CorpusGateway,
    IngestionJobRepository,
    IngestionTarget,
    PdfTextExtractor,
)
from drtc_chatbot.contexts.ingestion.domain.flags import flags_by_path
from drtc_chatbot.contexts.ingestion.domain.job import IngestionJob, JobStatus
from drtc_chatbot.contexts.ingestion.domain.parsing.model import ParseResult, RevisionStatus
from drtc_chatbot.contexts.ingestion.domain.parsing.profiles import (
    UnknownParserProfileError,
    build_parser,
)
from drtc_chatbot.contexts.ingestion.domain.review_report import ReviewReport, build_report
from drtc_chatbot.shared_kernel.application import Clock
from drtc_chatbot.shared_kernel.domain import InvariantViolationError, NotFoundError


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    version_id: str
    changed: bool
    content_digest: str
    report: ReviewReport
    approval: ApprovalOutcome | None


def _pages(ranges: Sequence[tuple[int, int]]) -> list[int]:
    return [page for first, last in ranges for page in range(first, last + 1)]


def content_digest(result: ParseResult) -> str:
    """Fingerprint of everything that is published: texts, pages, events, review flags and the
    (rounded) text boxes the reader highlights. Same input and parser, same digest."""
    flags = flags_by_path(result)
    canonical: list[dict[str, Any]] = [
        {
            "path": p.path,
            "kind": p.kind.value,
            "label": p.label,
            "title": p.title,
            "parent": p.parent_path,
            "text": p.text,
            "revision": p.revision,
            "status": p.status.value,
            "pages": [p.page_start, p.page_end],
            "event": (p.event.kind.value, p.event.source, str(p.event.published_on))
            if p.event
            else None,
            "flags": list(flags.get(p.path, ())) if p.status is RevisionStatus.CURRENT else [],
            "boxes": [
                [b.page, round(b.x0, 1), round(b.y0, 1), round(b.x1, 1), round(b.y1, 1)]
                for b in p.boxes
            ],
        }
        for p in result.provisions
    ]
    blob = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class ParsedTarget:
    result: ParseResult
    digest: str
    report: ReviewReport


def parse_target(target: IngestionTarget, extractor: PdfTextExtractor) -> ParsedTarget:
    """Verify the source, extract the normative pages and parse them (no side effects)."""
    verify_source(target)
    if not target.parser:
        raise InvariantViolationError(f"{target.version_id} has no parser profile in the manifest")
    if not target.normative_pages:
        raise InvariantViolationError(f"{target.version_id} has no normative pages in the manifest")
    try:
        parser = build_parser(target.parser)
    except UnknownParserProfileError as error:
        raise InvariantViolationError(f"Unknown parser profile: {target.parser}") from error
    result = parser.parse(extractor.extract(target.source_file, _pages(target.normative_pages)))
    return ParsedTarget(
        result,
        content_digest(result),
        build_report(target.version_id, result, target.normative_pages),
    )


def verify_source(target: IngestionTarget) -> None:
    if not target.source_file.is_file():
        raise InvariantViolationError(f"Source file not found: {target.source_file}")
    digest = hashlib.sha256()
    with target.source_file.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    if digest.hexdigest() != target.sha256:
        raise InvariantViolationError(
            f"{target.source_file.name} does not match the SHA-256 in the manifest: "
            "originals are immutable"
        )


class RunIngestion:
    """Extract → parse → publish (→ approve when the dev-only policy allows) with an audit job.

    Idempotent: the same source and parser produce the same digest, and publishing it again changes
    nothing. The original PDF is only read, and its SHA-256 must match the manifest.
    """

    def __init__(
        self,
        gateway: CorpusGateway,
        extractor: PdfTextExtractor,
        jobs: IngestionJobRepository,
        clock: Clock,
    ) -> None:
        self._gateway = gateway
        self._extractor = extractor
        self._jobs = jobs
        self._clock = clock

    async def execute(self, version_id: str) -> IngestionOutcome:
        target = next(
            (t for t in await self._gateway.targets() if t.version_id == version_id), None
        )
        if target is None:
            raise NotFoundError(f"Unknown instrument version: {version_id}")
        job = IngestionJob.start(str(uuid.uuid4()), version_id, self._clock.now())
        await self._jobs.save(job)
        try:
            return await self._run(target, job)
        except Exception as error:
            await self._jobs.save(
                job.fail(f"{type(error).__name__}: {error}", at=self._clock.now())
            )
            raise

    async def _run(self, target: IngestionTarget, job: IngestionJob) -> IngestionOutcome:
        parsed = parse_target(target, self._extractor)
        job = job.advance(JobStatus.EXTRACTED, at=self._clock.now())
        job = job.advance(
            JobStatus.PARSED,
            at=self._clock.now(),
            content_digest=parsed.digest,
            report=parsed.report.to_dict(),
        )
        publication = await self._gateway.publish(target, parsed.result, parsed.digest)
        job = job.advance(JobStatus.PUBLISHED, at=self._clock.now(), changed=publication.changed)
        await self._jobs.save(job)
        approval = await self._gateway.approve_automatically(target.version_id)
        return IngestionOutcome(
            target.version_id, publication.changed, parsed.digest, parsed.report, approval
        )
