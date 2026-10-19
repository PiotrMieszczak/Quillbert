"""document table

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("campaign_id", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("meta", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("progress", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_ref", sa.Text(), nullable=True),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaign.id"],
            name="fk_document_campaign_id_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_document"),
        sa.UniqueConstraint(
            "campaign_id", "sha256", name="uq_document_campaign_id_sha256"
        ),
        sa.CheckConstraint(
            "progress BETWEEN 0 AND 100", name="ck_document_progress_range"
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'processing', 'indexed', 'failed')",
            name="ck_document_status",
        ),
    )
    op.create_index("ix_document_campaign_id", "document", ["campaign_id"])


def downgrade() -> None:
    op.drop_table("document")
