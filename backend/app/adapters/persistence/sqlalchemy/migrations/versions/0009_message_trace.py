"""Trace columns on message: prompt version, model, timings, usage and cost

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-21

Written by the Gateway turn on assistant messages (ADR-0024); all null on user messages
and, for usage, when no provider was called.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNS = [
    sa.Column("prompt_id", sa.Text()),
    sa.Column("prompt_version", sa.Text()),
    sa.Column("model", sa.Text()),
    sa.Column("ttft_ms", sa.Integer()),
    sa.Column("duration_ms", sa.Integer()),
    sa.Column("prompt_tokens", sa.Integer()),
    sa.Column("completion_tokens", sa.Integer()),
    sa.Column("cost_usd", sa.Numeric(12, 8, asdecimal=False)),
]


def upgrade() -> None:
    for column in COLUMNS:
        op.add_column("message", column)


def downgrade() -> None:
    for column in reversed(COLUMNS):
        op.drop_column("message", column.name)
