"""Document layers: a campaign, a GM's library, or the vault (ADR-0027)

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-23

campaign_id becomes optional; owner_id marks a GM-library document and neither marks the
vault. systems scopes library and vault documents to game systems. Chunks copy all three
so search filters chunks alone. The file-dedupe unique constraint becomes one partial
index per shelf.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _systems() -> sa.Column:
    return sa.Column(
        "systems", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"
    )


def upgrade() -> None:
    for table in ("document", "chunk"):
        op.add_column(table, sa.Column("owner_id", sa.Text(), nullable=True))
        op.create_index(f"ix_{table}_owner_id", table, ["owner_id"])
        op.add_column(table, _systems())
        op.alter_column(table, "campaign_id", nullable=True)
    op.add_column("document", sa.Column("attribution", sa.Text(), nullable=True))
    op.create_check_constraint(
        "one_shelf", "document", "campaign_id IS NULL OR owner_id IS NULL"
    )
    op.drop_constraint("uq_document_campaign_id_sha256", "document", type_="unique")
    op.create_index(
        "uq_document_campaign_sha256",
        "document",
        ["campaign_id", "sha256"],
        unique=True,
        postgresql_where=sa.text("campaign_id IS NOT NULL"),
    )
    op.create_index(
        "uq_document_owner_sha256",
        "document",
        ["owner_id", "sha256"],
        unique=True,
        postgresql_where=sa.text("owner_id IS NOT NULL"),
    )
    op.create_index(
        "uq_document_vault_sha256",
        "document",
        ["sha256"],
        unique=True,
        postgresql_where=sa.text("campaign_id IS NULL AND owner_id IS NULL"),
    )


def downgrade() -> None:
    # Library and vault documents have no campaign to fall back to; their chunks and
    # citations cascade with them.
    op.execute("DELETE FROM document WHERE campaign_id IS NULL")
    for name in (
        "uq_document_vault_sha256",
        "uq_document_owner_sha256",
        "uq_document_campaign_sha256",
    ):
        op.drop_index(name, table_name="document")
    op.create_unique_constraint(
        "uq_document_campaign_id_sha256", "document", ["campaign_id", "sha256"]
    )
    op.drop_constraint("one_shelf", "document", type_="check")
    op.drop_column("document", "attribution")
    for table in ("chunk", "document"):
        op.alter_column(table, "campaign_id", nullable=False)
        op.drop_column(table, "systems")
        op.drop_index(f"ix_{table}_owner_id", table_name=table)
        op.drop_column(table, "owner_id")
