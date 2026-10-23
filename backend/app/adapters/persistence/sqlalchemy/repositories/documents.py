from collections.abc import Sequence

from sqlalchemy import and_, delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import ChunkRow, DocumentRow
from app.domain.documents import Chunk, Document, DocumentStatus, Shelf
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

    def get(self, shelf: Shelf, document_id: int) -> Document | None:
        query = select(DocumentRow).where(DocumentRow.id == document_id, _on(shelf))
        with self._sessions() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.document_from_row(row)

    def list_shelf(self, shelf: Shelf) -> list[Document]:
        query = select(DocumentRow).where(_on(shelf)).order_by(DocumentRow.id)
        with self._sessions() as session:
            return [mappers.document_from_row(row) for row in session.scalars(query)]

    def find_by_sha256(self, shelf: Shelf, sha256: str) -> Document | None:
        query = select(DocumentRow).where(_on(shelf), DocumentRow.sha256 == sha256)
        with self._sessions() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.document_from_row(row)

    def remove(self, shelf: Shelf, document_id: int) -> Document | None:
        query = (
            delete(DocumentRow)
            .where(DocumentRow.id == document_id, _on(shelf))
            .returning(DocumentRow)
        )
        with self._sessions.begin() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.document_from_row(row)

    def claim_queued(self) -> Document | None:
        # SKIP LOCKED: a second worker passes over the row the first is claiming.
        query = (
            select(DocumentRow)
            .where(DocumentRow.status == DocumentStatus.QUEUED.value)
            .order_by(DocumentRow.id)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        with self._sessions.begin() as session:
            row = session.scalars(query).one_or_none()
            if row is None:
                return None
            row.status = DocumentStatus.PROCESSING.value
            row.progress = 0
            row.error = None
            session.flush()
            return mappers.document_from_row(row)

    def requeue_processing(self) -> int:
        query = (
            update(DocumentRow)
            .where(DocumentRow.status == DocumentStatus.PROCESSING.value)
            .values(status=DocumentStatus.QUEUED.value, progress=0)
        )
        with self._sessions.begin() as session:
            return session.execute(query).rowcount

    def update(self, document: Document) -> None:
        with self._sessions.begin() as session:
            session.execute(
                update(DocumentRow)
                .where(DocumentRow.id == document.id)
                .values(**_progress_fields(document))
            )

    def index(self, document: Document, chunks: Sequence[Chunk]) -> None:
        with self._sessions.begin() as session:
            # Locked, so a delete cannot land between the check and the insert.
            row = session.get(DocumentRow, document.id, with_for_update=True)
            if row is None:
                return  # deleted while it was being processed
            session.execute(delete(ChunkRow).where(ChunkRow.document_id == document.id))
            if chunks:
                session.execute(
                    insert(ChunkRow),
                    [
                        {
                            "document_id": document.id,
                            "campaign_id": document.campaign_id,
                            "owner_id": document.owner_id,
                            "systems": list(document.systems),
                            "ordinal": chunk.ordinal,
                            "page_from": chunk.page_from,
                            "page_to": chunk.page_to,
                            "heading": chunk.heading,
                            "content": chunk.content,
                            "tsv": "",
                            "embedding": chunk.embedding,
                            "embedding_model": chunk.embedding_model,
                        }
                        for chunk in chunks
                    ],
                )
                # Keyword vectors in the document's own text-search config
                # (ADR-0021 IMP-011), computed by PostgreSQL in one statement.
                session.execute(
                    text(
                        "UPDATE chunk SET tsv = to_tsvector("
                        "CAST(:language AS regconfig), content) "
                        "WHERE document_id = :document_id"
                    ),
                    {"language": row.language, "document_id": document.id},
                )
            for field, value in _progress_fields(document).items():
                setattr(row, field, value)


def _on(shelf: Shelf):
    """Rows on exactly this shelf; `IS NOT DISTINCT FROM` makes None match NULL."""
    return and_(
        DocumentRow.campaign_id.is_not_distinct_from(shelf.campaign_id),
        DocumentRow.owner_id.is_not_distinct_from(shelf.owner_id),
    )


def _progress_fields(document: Document) -> dict[str, object]:
    return {
        "status": document.status.value,
        "progress": document.progress,
        "page_count": document.page_count,
        "meta": document.meta,
        "error": document.error,
    }
