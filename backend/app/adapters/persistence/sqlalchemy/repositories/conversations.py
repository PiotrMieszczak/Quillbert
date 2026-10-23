from sqlalchemy import case, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import (
    ChunkRow,
    CitationRow,
    ConversationRow,
    DocumentRow,
    MessageRow,
)
from app.domain.assistant import Citation, Conversation, Message
from app.domain.shared import NotFound

_FOREIGN_KEY_VIOLATION = "23503"


_WITH_CITATIONS = selectinload(ConversationRow.messages).selectinload(
    MessageRow.citations
)


def _is_missing_parent(exc: IntegrityError) -> bool:
    return getattr(exc.orig, "sqlstate", None) == _FOREIGN_KEY_VIOLATION


class SqlConversationRepo:
    """ConversationRepo over PostgreSQL.

    Each method is its own short transaction. A turn streams model output between
    add_message calls, and no connection is held while it does.
    """

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def next_conversation_id(self) -> int:
        return self._next_id("conversation")

    def next_message_id(self) -> int:
        return self._next_id("message")

    def save(self, conversation: Conversation) -> None:
        try:
            with self._sessions.begin() as session:
                session.merge(mappers.conversation_to_row(conversation))
        except IntegrityError as exc:
            if _is_missing_parent(exc):
                raise NotFound("campaign not found") from exc
            raise

    def get(self, conversation_id: int) -> Conversation | None:
        with self._sessions() as session:
            row = session.get(
                ConversationRow, conversation_id, options=[_WITH_CITATIONS]
            )
            if row is None:
                return None
            return mappers.conversation_from_row(row, _passages(session, [row]))

    def add_message(self, message: Message) -> None:
        try:
            with self._sessions.begin() as session:
                session.add(mappers.message_to_row(message))
        except IntegrityError as exc:
            if _is_missing_parent(exc):
                raise NotFound("conversation not found") from exc
            raise

    def list_for_campaign(self, campaign_id: str) -> list[Conversation]:
        query = (
            select(ConversationRow)
            .where(ConversationRow.campaign_id == campaign_id)
            .options(_WITH_CITATIONS)
            .order_by(ConversationRow.id.desc())
        )
        with self._sessions() as session:
            rows = list(session.scalars(query))
            passages = _passages(session, rows)
            return [mappers.conversation_from_row(row, passages) for row in rows]

    def _next_id(self, table: str) -> int:
        # The port hands out ids before insert; the identity column's sequence is
        # safe under concurrent callers.
        with self._sessions() as session:
            return session.execute(
                text("SELECT nextval(pg_get_serial_sequence(:table, 'id'))"),
                {"table": table},
            ).scalar_one()


def _passages(
    session: Session, conversations: list[ConversationRow]
) -> dict[int, Citation]:
    """Citation row id -> the passage it points at, for every citation given."""
    ids = [
        citation.id
        for conversation in conversations
        for message in conversation.messages
        for citation in message.citations
    ]
    if not ids:
        return {}
    query = (
        select(
            CitationRow.id,
            CitationRow.label,
            ChunkRow.id,
            ChunkRow.document_id,
            DocumentRow.filename,
            ChunkRow.page_from,
            ChunkRow.heading,
            # Same rule as the search's layer label.
            case(
                (DocumentRow.campaign_id.is_not(None), None),
                (DocumentRow.owner_id.is_not(None), "My library"),
                else_=func.coalesce(DocumentRow.attribution, "Vault"),
            ),
        )
        .join(ChunkRow, ChunkRow.id == CitationRow.chunk_id)
        .join(DocumentRow, DocumentRow.id == ChunkRow.document_id)
        .where(CitationRow.id.in_(ids))
    )
    return {
        row_id: Citation(label, *rest)
        for row_id, label, *rest in session.execute(query)
    }
