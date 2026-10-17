from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import DocumentRow
from app.domain.documents import Document
from app.domain.shared import NotFound

_FOREIGN_KEY_VIOLATION = "23503"


class SqlDocumentRepo:
    """DocumentRepo over PostgreSQL. Each method is its own short transaction."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def next_document_id(self) -> int:
        # The port hands out ids before insert; the identity column's sequence is
        # safe under concurrent callers.
        with self._sessions() as session:
            return session.execute(
                text("SELECT nextval(pg_get_serial_sequence('document', 'id'))")
            ).scalar_one()

    def add(self, document: Document) -> None:
        try:
            with self._sessions.begin() as session:
                session.add(mappers.document_to_row(document))
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == _FOREIGN_KEY_VIOLATION:
                raise NotFound("campaign not found") from exc
            raise

    def get(self, campaign_id: str, document_id: int) -> Document | None:
        query = select(DocumentRow).where(
            DocumentRow.id == document_id, DocumentRow.campaign_id == campaign_id
        )
        with self._sessions() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.document_from_row(row)

    def list_for_campaign(self, campaign_id: str) -> list[Document]:
        query = (
            select(DocumentRow)
            .where(DocumentRow.campaign_id == campaign_id)
            .order_by(DocumentRow.id)
        )
        with self._sessions() as session:
            return [mappers.document_from_row(row) for row in session.scalars(query)]

    def find_by_sha256(self, campaign_id: str, sha256: str) -> Document | None:
        query = select(DocumentRow).where(
            DocumentRow.campaign_id == campaign_id, DocumentRow.sha256 == sha256
        )
        with self._sessions() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.document_from_row(row)
