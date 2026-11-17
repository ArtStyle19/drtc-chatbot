"""Enable the PostgreSQL extensions the retrieval pipeline relies on.

- vector: pgvector embeddings (semantic search).
- unaccent: accent-insensitive Spanish full-text search.
- pg_trgm: fuzzy matching of article titles and legal references.

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXTENSIONS = ("vector", "unaccent", "pg_trgm")


def upgrade() -> None:
    for extension in EXTENSIONS:
        op.execute(f'CREATE EXTENSION IF NOT EXISTS "{extension}"')


def downgrade() -> None:
    for extension in reversed(EXTENSIONS):
        op.execute(f'DROP EXTENSION IF EXISTS "{extension}"')
