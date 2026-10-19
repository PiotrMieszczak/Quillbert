"""chunk.embedding_model: which model produced each vector

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("chunk", sa.Column("embedding_model", sa.Text(), nullable=True))
    # Every vector so far came from the one model embedding_space records.
    op.execute(
        "UPDATE chunk SET embedding_model = (SELECT model FROM embedding_space) "
        "WHERE embedding IS NOT NULL"
    )
    op.create_foreign_key(
        "fk_chunk_embedding_model_embedding_space",
        "chunk",
        "embedding_space",
        ["embedding_model"],
        ["model"],
    )
    op.create_check_constraint(
        "embedding_model_with_embedding",
        "chunk",
        "(embedding IS NULL) = (embedding_model IS NULL)",
    )


def downgrade() -> None:
    # Raw SQL: these are the final names, not names for the convention to expand.
    op.execute(
        "ALTER TABLE chunk DROP CONSTRAINT ck_chunk_embedding_model_with_embedding"
    )
    op.execute(
        "ALTER TABLE chunk DROP CONSTRAINT fk_chunk_embedding_model_embedding_space"
    )
    op.drop_column("chunk", "embedding_model")
