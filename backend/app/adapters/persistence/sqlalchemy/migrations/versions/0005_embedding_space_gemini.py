"""embedding space: voyage-4 -> google/gemini-embedding-2

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# No chunk is embedded yet, so renaming the model orphans no vectors. Once chunks
# exist, a model change must re-embed them instead (ADR-0021).
def upgrade() -> None:
    op.execute(
        "UPDATE embedding_space SET model = 'google/gemini-embedding-2' "
        "WHERE model = 'voyage-4'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE embedding_space SET model = 'voyage-4' "
        "WHERE model = 'google/gemini-embedding-2'"
    )
