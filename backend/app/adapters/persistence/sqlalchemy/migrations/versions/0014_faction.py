"""Factions: the powers of a campaign (#107)

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-17

Only name and relationship are required. name sorts by code point (COLLATE "C") so
the SQL list order agrees with the in-memory repo, as on character.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "faction",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("campaign_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(collation="C"), nullable=False),
        sa.Column("relationship", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=True),
        sa.Column("influence", sa.Text(), nullable=True),
        sa.Column("reach", sa.Text(), nullable=True),
        sa.Column("motto", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "relationship IN ('ally', 'enemy', 'family', 'professional', 'neutral')",
            name=op.f("ck_faction_relationship"),
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaign.id"],
            name=op.f("fk_faction_campaign_id_campaign"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_faction")),
    )
    op.create_index(
        op.f("ix_faction_campaign_id"), "faction", ["campaign_id"], unique=False
    )
    # Closed to the Supabase Data API, like every public table (0008).
    op.execute("ALTER TABLE faction ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("faction")
