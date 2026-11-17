"""Character bio: a story field every system has

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-17

Separate from notes, which are GM-private (DEC-004).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("character", sa.Column("bio", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("character", "bio")
