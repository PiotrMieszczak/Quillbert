"""Citation snapshot: the passage is copied onto the row, and chunk_id is optional

Revision ID: 0010
Revises: 0009
Create Date: 2026-10-23

A shared-library passage comes from Arkon and has no chunk here (ADR-0027), so the
citation keeps what the GM sees (file, page, heading, attribution) itself. Existing
rows are backfilled from their chunk.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = [
    sa.Column("document_id", sa.Integer()),
    sa.Column("filename", sa.Text()),
    sa.Column("page_from", sa.Integer()),
    sa.Column("heading", sa.Text()),
    sa.Column("attribution", sa.Text()),
]


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column("citation", column)
    op.execute(
        """
        UPDATE citation SET document_id = chunk.document_id,
                            filename = document.filename,
                            page_from = chunk.page_from,
                            heading = chunk.heading
        FROM chunk JOIN document ON document.id = chunk.document_id
        WHERE chunk.id = citation.chunk_id
        """
    )
    op.alter_column("citation", "filename", nullable=False)
    op.alter_column("citation", "chunk_id", nullable=True)


def downgrade() -> None:
    # Library citations have no chunk to point back at.
    op.execute("DELETE FROM citation WHERE chunk_id IS NULL")
    op.alter_column("citation", "chunk_id", nullable=False)
    for column in reversed(COLUMNS):
        op.drop_column("citation", column.name)
