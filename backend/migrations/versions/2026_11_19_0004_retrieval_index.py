"""Content search: passages (words search), their embeddings and the accent vocabulary.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEARCH_VECTOR = (
    "setweight(to_tsvector('spanish', coalesce(title, '')), 'A') || "
    "setweight(to_tsvector('spanish', coalesce(body, '')), 'B') || "
    "setweight(to_tsvector('spanish', coalesce(breadcrumb, '') || ' ' || coalesce(lead, '')), 'C')"
)


def upgrade() -> None:
    op.create_table(
        "retrieval_passages",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("instrument_id", sa.String(120), nullable=False),
        sa.Column("instrument_version_id", sa.String(160), nullable=False),
        sa.Column("provision_path", sa.Text(), nullable=False),
        sa.Column("unit_path", sa.Text(), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("label", sa.String(120), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("breadcrumb", sa.Text(), nullable=False),
        sa.Column("lead", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("page_start", sa.Integer(), nullable=False),
        sa.Column("page_end", sa.Integer(), nullable=False),
        sa.Column("citation", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed(SEARCH_VECTOR, persisted=True),
            nullable=False,
        ),
        sa.UniqueConstraint("instrument_version_id", "provision_path"),
    )
    op.create_index(
        "ix_retrieval_passages_search", "retrieval_passages", ["search_vector"], postgresql_using="gin"
    )
    op.create_index("ix_retrieval_passages_instrument", "retrieval_passages", ["instrument_id"])
    op.create_table(
        "retrieval_embeddings",
        sa.Column(
            "passage_id",
            sa.Uuid(),
            sa.ForeignKey("retrieval_passages.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("model", sa.String(80), primary_key=True),
        sa.Column("window", sa.Integer(), primary_key=True),
        sa.Column("dims", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("embedding", Vector(), nullable=False),
        sa.CheckConstraint("vector_dims(embedding) = dims", name="ck_retrieval_embeddings_dims"),
    )
    op.create_index("ix_retrieval_embeddings_model", "retrieval_embeddings", ["model"])
    # PostgreSQL's Spanish stemmer only recognises "-ción" WITH the accent: the search text is extended
    # with the accented form of every word typed without accent that the corpus has (domain/lexical.py).
    op.create_table(
        "retrieval_accents",
        sa.Column("plain", sa.String(80), primary_key=True),
        sa.Column("accented", sa.String(80), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("retrieval_accents")
    op.drop_table("retrieval_embeddings")
    op.drop_table("retrieval_passages")
