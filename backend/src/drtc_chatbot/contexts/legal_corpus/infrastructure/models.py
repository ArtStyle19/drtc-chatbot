"""SQLAlchemy models of the legal corpus (persistence details, mapped explicitly to the domain)."""

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from drtc_chatbot.shared_kernel.infrastructure.persistence import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


class SourceDocumentRow(Base):
    __tablename__ = "source_documents"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    file_name: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    page_count: Mapped[int] = mapped_column(Integer)


class InstrumentRow(Base):
    __tablename__ = "legal_instruments"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    instrument_type: Mapped[str] = mapped_column(String(40))
    number: Mapped[str] = mapped_column(String(60))
    title: Mapped[str] = mapped_column(Text)
    short_name: Mapped[str] = mapped_column(Text)
    issuing_authority: Mapped[str] = mapped_column(Text)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    aliases: Mapped[list[Any]] = mapped_column(JsonType, default=list, server_default="[]")


class VersionRow(Base):
    __tablename__ = "instrument_versions"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("legal_instruments.id"))
    source_document_id: Mapped[str] = mapped_column(ForeignKey("source_documents.id"))
    ordinal: Mapped[int] = mapped_column(Integer)
    edition_label: Mapped[str] = mapped_column(Text)
    consolidated_as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    consolidation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(30))
    parser: Mapped[str | None] = mapped_column(String(40), nullable=True)
    page_sections: Mapped[list[Any]] = mapped_column(JsonType, default=list)
    alerts: Mapped[list[Any]] = mapped_column(JsonType, default=list)
    approval_status: Mapped[str] = mapped_column(String(20), default="pending")
    approval_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    content_digest: Mapped[str | None] = mapped_column(String(64), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (Index("ix_instrument_versions_instrument", "instrument_id", "ordinal"),)


class ProvisionRow(Base):
    """Stable identity of a provision inside an instrument (its structural path)."""

    __tablename__ = "provisions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[str] = mapped_column(ForeignKey("legal_instruments.id"))
    structural_path: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(120))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("provisions.id"), nullable=True)

    __table_args__ = (UniqueConstraint("instrument_id", "structural_path"),)


class ProvisionRevisionRow(Base):
    """One revision of a provision's text in one instrument version (never overwritten)."""

    __tablename__ = "provision_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provisions.id"))
    instrument_version_id: Mapped[str] = mapped_column(ForeignKey("instrument_versions.id"))
    revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    ordinal: Mapped[int] = mapped_column(Integer)
    boxes: Mapped[list[Any]] = mapped_column(JsonType, default=list)
    event: Mapped[dict[str, Any] | None] = mapped_column(JsonType, nullable=True)
    # Codes of things a person must look at (e.g. an unapplied paragraph replacement).
    review_flags: Mapped[list[Any]] = mapped_column(JsonType, default=list, server_default="[]")

    __table_args__ = (
        UniqueConstraint("provision_id", "instrument_version_id", "revision"),
        # The database itself refuses two texts in force at once for the same provision.
        Index(
            "uq_provision_versions_one_current",
            "provision_id",
            "instrument_version_id",
            unique=True,
            postgresql_where=sql_text("status = 'current'"),
        ),
        Index("ix_provision_versions_version_order", "instrument_version_id", "ordinal"),
    )


class EditorialNoteRow(Base):
    __tablename__ = "editorial_notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    instrument_version_id: Mapped[str] = mapped_column(ForeignKey("instrument_versions.id"))
    provision_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_editorial_notes_version_path", "instrument_version_id", "provision_path"),
    )
