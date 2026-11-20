"""SQLAlchemy models of the ingestion context."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from drtc_chatbot.shared_kernel.infrastructure.persistence import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


class IngestionJobRow(Base):
    """One run of the ingestion over one instrument version (kept as an audit trail)."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    instrument_version_id: Mapped[str] = mapped_column(ForeignKey("instrument_versions.id"))
    status: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    changed: Mapped[bool | None] = mapped_column(nullable=True)
    report: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_ingestion_jobs_version_started", "instrument_version_id", "started_at"),
    )
