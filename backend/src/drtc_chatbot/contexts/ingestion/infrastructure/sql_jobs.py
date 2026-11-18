"""SQL repository of ingestion jobs (an audit trail of every run)."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from drtc_chatbot.contexts.ingestion.domain.job import IngestionJob, JobStatus
from drtc_chatbot.contexts.ingestion.infrastructure.models import IngestionJobRow


class SqlIngestionJobRepository:
    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def save(self, job: IngestionJob) -> None:
        async with self._sessions.begin() as session:
            await session.merge(
                IngestionJobRow(
                    id=uuid.UUID(job.job_id),
                    instrument_version_id=job.version_id,
                    status=job.status.value,
                    started_at=job.started_at,
                    finished_at=job.finished_at,
                    content_digest=job.content_digest,
                    changed=job.changed,
                    report=job.report or None,
                    error=job.error,
                )
            )

    async def latest(self, version_id: str) -> IngestionJob | None:
        async with self._sessions() as session:
            row = (
                await session.scalars(
                    select(IngestionJobRow)
                    .where(IngestionJobRow.instrument_version_id == version_id)
                    .order_by(IngestionJobRow.started_at.desc())
                    .limit(1)
                )
            ).first()
        if row is None:
            return None
        return IngestionJob(
            job_id=str(row.id),
            version_id=row.instrument_version_id,
            status=JobStatus(row.status),
            started_at=row.started_at,
            finished_at=row.finished_at,
            content_digest=row.content_digest,
            changed=row.changed,
            report=row.report or {},
            error=row.error,
        )
