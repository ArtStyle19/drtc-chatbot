"""Tables of the content search (spec 004). DERIVED data: rebuilt from the approved corpus at any time.

``retrieval_passages`` holds one row per current provision of an approved edition, with a generated
``tsvector`` (title weight A, text B, breadcrumb and parent's lead C) built with PostgreSQL's ``spanish``
configuration. Typing without accents is handled on the QUERY side (see ``domain/lexical.py`` and
``retrieval_accents``): the stemmer needs the accent to recognise "-ción".
``retrieval_embeddings`` holds the vectors, one per window and per model, so several models can
coexist while they are being compared. There is deliberately no approximate (ANN) index: a few
thousand vectors are scanned exactly in milliseconds.
"""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Computed,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from drtc_chatbot.shared_kernel.infrastructure.persistence import Base

SEARCH_CONFIG = "spanish"
SEARCH_VECTOR_EXPRESSION = (
    f"setweight(to_tsvector('{SEARCH_CONFIG}', coalesce(title, '')), 'A') || "
    f"setweight(to_tsvector('{SEARCH_CONFIG}', coalesce(body, '')), 'B') || "
    f"setweight(to_tsvector('{SEARCH_CONFIG}', coalesce(breadcrumb, '') || ' ' || coalesce(lead, '')), 'C')"
)


class PassageRow(Base):
    __tablename__ = "retrieval_passages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[str] = mapped_column(String(120))
    instrument_version_id: Mapped[str] = mapped_column(String(160))
    provision_path: Mapped[str] = mapped_column(Text)
    unit_path: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(120))
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    breadcrumb: Mapped[str] = mapped_column(Text)
    lead: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    citation: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR, Computed(SEARCH_VECTOR_EXPRESSION, persisted=True)
    )

    __table_args__ = (
        UniqueConstraint("instrument_version_id", "provision_path"),
        Index("ix_retrieval_passages_search", "search_vector", postgresql_using="gin"),
        Index("ix_retrieval_passages_instrument", "instrument_id"),
    )


class EmbeddingRow(Base):
    __tablename__ = "retrieval_embeddings"

    passage_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("retrieval_passages.id", ondelete="CASCADE"), primary_key=True
    )
    model: Mapped[str] = mapped_column(String(80), primary_key=True)
    window: Mapped[int] = mapped_column(Integer, primary_key=True)
    dims: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    # No fixed dimension: several models (1536, 3072, reduced…) are stored side by side.
    embedding: Mapped[list[float]] = mapped_column(Vector())

    __table_args__ = (
        CheckConstraint("vector_dims(embedding) = dims", name="ck_retrieval_embeddings_dims"),
        Index("ix_retrieval_embeddings_model", "model"),
    )


class AccentRow(Base):
    """An accented word of the corpus and how it is typed without the accent ("apelacion" → "apelación")."""

    __tablename__ = "retrieval_accents"

    plain: Mapped[str] = mapped_column(String(80), primary_key=True)
    accented: Mapped[str] = mapped_column(String(80), primary_key=True)
