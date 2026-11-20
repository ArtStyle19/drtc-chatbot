"""corpus provisions and ingestion jobs

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-18 11:30:37.306290+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('legal_instruments',
    sa.Column('id', sa.String(length=120), nullable=False),
    sa.Column('ordinal', sa.Integer(), nullable=False),
    sa.Column('instrument_type', sa.String(length=40), nullable=False),
    sa.Column('number', sa.String(length=60), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('short_name', sa.Text(), nullable=False),
    sa.Column('issuing_authority', sa.Text(), nullable=False),
    sa.Column('publication_date', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_legal_instruments'))
    )
    op.create_table('source_documents',
    sa.Column('id', sa.String(length=120), nullable=False),
    sa.Column('file_name', sa.Text(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('page_count', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_source_documents')),
    sa.UniqueConstraint('sha256', name=op.f('uq_source_documents_sha256'))
    )
    op.create_table('instrument_versions',
    sa.Column('id', sa.String(length=160), nullable=False),
    sa.Column('instrument_id', sa.String(length=120), nullable=False),
    sa.Column('source_document_id', sa.String(length=120), nullable=False),
    sa.Column('ordinal', sa.Integer(), nullable=False),
    sa.Column('edition_label', sa.Text(), nullable=False),
    sa.Column('consolidated_as_of', sa.Date(), nullable=True),
    sa.Column('consolidation_note', sa.Text(), nullable=True),
    sa.Column('verification_status', sa.String(length=30), nullable=False),
    sa.Column('parser', sa.String(length=40), nullable=True),
    sa.Column('page_sections', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('alerts', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('approval_status', sa.String(length=20), nullable=False),
    sa.Column('approval_mode', sa.String(length=20), nullable=True),
    sa.Column('approved_by', sa.Text(), nullable=True),
    sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('content_digest', sa.String(length=64), nullable=True),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['instrument_id'], ['legal_instruments.id'], name=op.f('fk_instrument_versions_instrument_id_legal_instruments')),
    sa.ForeignKeyConstraint(['source_document_id'], ['source_documents.id'], name=op.f('fk_instrument_versions_source_document_id_source_documents')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_instrument_versions'))
    )
    op.create_index('ix_instrument_versions_instrument', 'instrument_versions', ['instrument_id', 'ordinal'], unique=False)
    op.create_table('provisions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('instrument_id', sa.String(length=120), nullable=False),
    sa.Column('structural_path', sa.Text(), nullable=False),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('label', sa.String(length=120), nullable=False),
    sa.Column('parent_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['instrument_id'], ['legal_instruments.id'], name=op.f('fk_provisions_instrument_id_legal_instruments')),
    sa.ForeignKeyConstraint(['parent_id'], ['provisions.id'], name=op.f('fk_provisions_parent_id_provisions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_provisions')),
    sa.UniqueConstraint('instrument_id', 'structural_path', name=op.f('uq_provisions_instrument_id'))
    )
    op.create_table('editorial_notes',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('instrument_version_id', sa.String(length=160), nullable=False),
    sa.Column('provision_path', sa.Text(), nullable=True),
    sa.Column('kind', sa.String(length=20), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('page', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['instrument_version_id'], ['instrument_versions.id'], name=op.f('fk_editorial_notes_instrument_version_id_instrument_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_editorial_notes'))
    )
    op.create_index('ix_editorial_notes_version_path', 'editorial_notes', ['instrument_version_id', 'provision_path'], unique=False)
    op.create_table('ingestion_jobs',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('instrument_version_id', sa.String(length=160), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('content_digest', sa.String(length=64), nullable=True),
    sa.Column('changed', sa.Boolean(), nullable=True),
    sa.Column('report', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['instrument_version_id'], ['instrument_versions.id'], name=op.f('fk_ingestion_jobs_instrument_version_id_instrument_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ingestion_jobs'))
    )
    op.create_index('ix_ingestion_jobs_version_started', 'ingestion_jobs', ['instrument_version_id', 'started_at'], unique=False)
    op.create_table('provision_versions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('provision_id', sa.Uuid(), nullable=False),
    sa.Column('instrument_version_id', sa.String(length=160), nullable=False),
    sa.Column('revision', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('title', sa.Text(), nullable=True),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('page_start', sa.Integer(), nullable=False),
    sa.Column('page_end', sa.Integer(), nullable=False),
    sa.Column('ordinal', sa.Integer(), nullable=False),
    sa.Column('boxes', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=False),
    sa.Column('event', sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'), nullable=True),
    sa.ForeignKeyConstraint(['instrument_version_id'], ['instrument_versions.id'], name=op.f('fk_provision_versions_instrument_version_id_instrument_versions')),
    sa.ForeignKeyConstraint(['provision_id'], ['provisions.id'], name=op.f('fk_provision_versions_provision_id_provisions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_provision_versions')),
    sa.UniqueConstraint('provision_id', 'instrument_version_id', 'revision', name=op.f('uq_provision_versions_provision_id'))
    )
    op.create_index('ix_provision_versions_version_order', 'provision_versions', ['instrument_version_id', 'ordinal'], unique=False)
    op.create_index('uq_provision_versions_one_current', 'provision_versions', ['provision_id', 'instrument_version_id'], unique=True, postgresql_where=sa.text("status = 'current'"))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_provision_versions_one_current', table_name='provision_versions', postgresql_where=sa.text("status = 'current'"))
    op.drop_index('ix_provision_versions_version_order', table_name='provision_versions')
    op.drop_table('provision_versions')
    op.drop_index('ix_ingestion_jobs_version_started', table_name='ingestion_jobs')
    op.drop_table('ingestion_jobs')
    op.drop_index('ix_editorial_notes_version_path', table_name='editorial_notes')
    op.drop_table('editorial_notes')
    op.drop_table('provisions')
    op.drop_index('ix_instrument_versions_instrument', table_name='instrument_versions')
    op.drop_table('instrument_versions')
    op.drop_table('source_documents')
    op.drop_table('legal_instruments')
