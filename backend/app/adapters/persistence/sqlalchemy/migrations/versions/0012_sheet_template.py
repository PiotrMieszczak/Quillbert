"""Sheet templates: one character sheet per system (ADR-0030, #126)

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-17

The sheet is JSONB because it is always read and written whole, and its shape is
checked by the Sheet model, not by columns.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sheet_template",
        sa.Column("system_id", sa.Text(), nullable=False),
        sa.Column("sheet", postgresql.JSONB(), nullable=False),
        sa.Column("saved_by", sa.Text(), nullable=False),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["system_id"],
            ["system.id"],
            name=op.f("fk_sheet_template_system_id_system"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("system_id", name=op.f("pk_sheet_template")),
    )
    # Closed to the Supabase Data API, like every public table (0008).
    op.execute("ALTER TABLE sheet_template ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.drop_table("sheet_template")
