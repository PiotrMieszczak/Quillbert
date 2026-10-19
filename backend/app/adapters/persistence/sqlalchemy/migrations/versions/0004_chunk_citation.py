"""chunk, citation, embedding space

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "document",
        sa.Column(
            "language",
            sa.Text(),
            server_default="simple",
            nullable=False,
        ),
    )
    # 0003's name is passed through the naming convention, so the real name is doubled.
    op.execute(
        "ALTER TABLE document DROP CONSTRAINT ck_document_ck_document_status"
    )
    op.create_check_constraint(
        "status",
        "document",
        "status IN ('queued', 'processing', 'indexed', 'failed', 'awaiting_ocr')",
    )

    op.create_table(
        "embedding_space",
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("dimensions = 1024", name="dimensions"),
        sa.PrimaryKeyConstraint("model", name="pk_embedding_space"),
    )
    op.execute(
        "INSERT INTO embedding_space (model, dimensions) VALUES ('voyage-4', 1024)"
    )

    op.create_table(
        "chunk",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", sa.Text(), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("page_from", sa.Integer(), nullable=True),
        sa.Column("page_to", sa.Integer(), nullable=True),
        sa.Column("heading", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tsv", TSVECTOR(), nullable=False),
        sa.Column("embedding", Vector(1024), nullable=True),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["document.id"],
            name="fk_chunk_document_id_document",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["campaign_id"],
            ["campaign.id"],
            name="fk_chunk_campaign_id_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_chunk"),
        sa.UniqueConstraint(
            "document_id", "ordinal", name="uq_chunk_document_id_ordinal"
        ),
    )
    op.create_index("ix_chunk_document_id", "chunk", ["document_id"])
    op.create_index("ix_chunk_campaign_id", "chunk", ["campaign_id"])
    op.create_index("ix_chunk_tsv", "chunk", ["tsv"], postgresql_using="gin")
    op.create_index(
        "ix_chunk_embedding",
        "chunk",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    op.create_table(
        "citation",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("quote", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["message_id"],
            ["message.id"],
            name="fk_citation_message_id_message",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["chunk_id"],
            ["chunk.id"],
            name="fk_citation_chunk_id_chunk",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_citation"),
    )
    op.create_index("ix_citation_message_id", "citation", ["message_id"])
    op.create_index("ix_citation_chunk_id", "citation", ["chunk_id"])


def downgrade() -> None:
    op.drop_table("citation")
    op.drop_table("chunk")
    op.drop_table("embedding_space")
    op.execute("ALTER TABLE document DROP CONSTRAINT ck_document_status")
    op.create_check_constraint(
        "ck_document_status",
        "document",
        "status IN ('queued', 'processing', 'indexed', 'failed')",
    )
    op.drop_column("document", "language")
