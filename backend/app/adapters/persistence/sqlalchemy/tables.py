"""PostgreSQL schema. Mapped to the domain by mappers.py, not equal to it."""

from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Integer,
    MetaData,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Stable constraint names, so migrations can refer to them.
NAMING = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING)


class SystemRow(Base):
    """A game system campaigns are played in (DEC-013). Reference data."""

    __tablename__ = "system"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True)


class CampaignRow(Base):
    """owner_id arrives with auth (ADR-0008, DEC-005). No owner scope until then."""

    __tablename__ = "campaign"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    # Exactly one system per campaign; a system in use cannot be deleted.
    system_id: Mapped[str] = mapped_column(
        ForeignKey("system.id", ondelete="RESTRICT"), index=True
    )
    tint: Mapped[str] = mapped_column(Text)
    image_path: Mapped[str | None] = mapped_column(Text)
    last_played_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ConversationRow(Base):
    __tablename__ = "conversation"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    mode: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    messages: Mapped[list["MessageRow"]] = relationship(
        order_by="MessageRow.id", cascade="all, delete-orphan"
    )


class MessageRow(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    mode: Mapped[str] = mapped_column(Text)
    tool_label: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DocumentRow(Base):
    """An uploaded or imported file. See docs/data-model.md `document`."""

    __tablename__ = "document"
    __table_args__ = (
        # One copy of a file per campaign (ADR-0021 IMP-003).
        UniqueConstraint(
            "campaign_id", "sha256", name="uq_document_campaign_id_sha256"
        ),
        CheckConstraint("progress BETWEEN 0 AND 100", name="progress_range"),
        CheckConstraint(
            "status IN ('queued', 'processing', 'indexed', 'failed', 'awaiting_ocr')",
            name="status",
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    filename: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    meta: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(Integer, server_default="0")
    error: Mapped[str | None] = mapped_column(Text)
    storage_key: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str | None] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(Text)
    # tsvector config. 'simple' stems nothing (ADR-0021 IMP-011).
    language: Mapped[str] = mapped_column(
        Text, server_default="simple", default="simple"
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EmbeddingSpaceRow(Base):
    """The one model that produced every stored vector (ADR-0021)."""

    __tablename__ = "embedding_space"
    __table_args__ = (CheckConstraint("dimensions = 1024", name="dimensions"),)

    model: Mapped[str] = mapped_column(Text, primary_key=True)
    dimensions: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ChunkRow(Base):
    """Indexed passage. Text, keyword index, and vector are one row (DEC-012)."""

    __tablename__ = "chunk"
    __table_args__ = (
        UniqueConstraint(
            "document_id", "ordinal", name="uq_chunk_document_id_ordinal"
        ),
        Index("ix_chunk_tsv", "tsv", postgresql_using="gin"),
        Index(
            "ix_chunk_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("document.id", ondelete="CASCADE"), index=True
    )
    # Copied from the document. A document does not move between campaigns.
    campaign_id: Mapped[str] = mapped_column(
        ForeignKey("campaign.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    page_from: Mapped[int | None] = mapped_column(Integer)
    page_to: Mapped[int | None] = mapped_column(Integer)
    heading: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text)
    tsv: Mapped[str] = mapped_column(TSVECTOR)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024))


class CitationRow(Base):
    """An assistant message's source. The chunk is the source of truth."""

    __tablename__ = "citation"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("message.id", ondelete="CASCADE"), index=True
    )
    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("chunk.id", ondelete="CASCADE"), index=True
    )
    # The label the model was shown, such as S1.
    label: Mapped[str] = mapped_column(Text)
    quote: Mapped[str | None] = mapped_column(Text)
