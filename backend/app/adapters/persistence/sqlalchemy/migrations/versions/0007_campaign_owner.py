"""campaign.owner_id (DEC-005); D&D 2014 joins the systems

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable: campaigns made before ownership have no owner, and no user can see
    # them until one is claimed (docs/data-model.md, DEC-005).
    op.add_column("campaign", sa.Column("owner_id", sa.Text(), nullable=True))
    op.create_index("ix_campaign_owner_id", "campaign", ["owner_id"])
    # ON CONFLICT: another migration may add the same reference row.
    op.execute(
        "INSERT INTO system (id, name) VALUES ('dnd-2014', 'D&D 2014') "
        "ON CONFLICT DO NOTHING"
    )


def downgrade() -> None:
    # Fails, by design, while a campaign is still played in D&D 2014.
    op.execute("DELETE FROM system WHERE id = 'dnd-2014'")
    op.drop_index("ix_campaign_owner_id", table_name="campaign")
    op.drop_column("campaign", "owner_id")
