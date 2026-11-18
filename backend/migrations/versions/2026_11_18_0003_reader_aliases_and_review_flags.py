"""Reader: instrument aliases (reference search) and per-revision review flags.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

JSON_TYPE = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def upgrade() -> None:
    op.add_column(
        "legal_instruments",
        sa.Column("aliases", JSON_TYPE, server_default="[]", nullable=False),
    )
    op.add_column(
        "provision_versions",
        sa.Column("review_flags", JSON_TYPE, server_default="[]", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("provision_versions", "review_flags")
    op.drop_column("legal_instruments", "aliases")
