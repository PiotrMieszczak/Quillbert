from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import ConversationRow, MessageRow
from app.domain.assistant import Conversation, Message
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
            return mappers.conversation_from_row(row)

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
            return [
                mappers.conversation_from_row(row) for row in session.scalars(query)
            ]

    def _next_id(self, table: str) -> int:
        # The port hands out ids before insert; the identity column's sequence is
        # safe under concurrent callers.
        with self._sessions() as session:
            return session.execute(
                text("SELECT nextval(pg_get_serial_sequence(:table, 'id'))"),
                {"table": table},
            ).scalar_one()
