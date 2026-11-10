"""Characters: NPCs and player characters of a campaign (#107)

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-10

One table split by is_player (docs/data-model.md). stats and player_profile are JSONB:
stats takes its shape from the system's sheet (ADR-0030), and the profile is always
read with its character. name sorts by code point (COLLATE "C") so SQL paging
agrees with the in-memory repo. pg_trgm backs part-of-a-name search over many NPCs.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Supabase keeps extensions out of public (its advisor flags them there); plain
    # Postgres gets the same schema, so the qualified opclass below works in both.
    op.execute("CREATE SCHEMA IF NOT EXISTS extensions")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm SCHEMA extensions")
    op.create_table(
        "character",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("campaign_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(collation="C"), nullable=False),
        sa.Column("is_player", sa.Boolean(), nullable=False),
        sa.Column("relationship", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("disposition", sa.Text(), nullable=True),
        sa.Column("last_seen", sa.Text(), nullable=True),
        sa.Column(
            "stats",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="{}",
            nullable=False,
        ),
        sa.Column(
            "tags", postgresql.ARRAY(sa.Text()), server_default="{}", nullable=False
        ),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("portrait_path", sa.Text(), nullable=True),
        sa.Column(
            "player_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaign.id"],
            name="fk_character_campaign_id_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_character"),
        sa.CheckConstraint(
            "relationship IN ('ally', 'enemy', 'family', 'professional', 'neutral')",
            name="ck_character_relationship",
        ),
    )
    op.create_index(
        "ix_character_list",
        "character",
        ["campaign_id", "is_player", sa.text("lower(name)"), "id"],
    )
    op.create_index(
        "ix_character_name_trgm",
        "character",
        [sa.text("lower(name) extensions.gin_trgm_ops")],
        postgresql_using="gin",
    )
    # Closed to the Supabase Data API, like every public table (0008).
    op.execute("ALTER TABLE character ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("character")
    # pg_trgm stays: other objects may come to depend on it.
