"""What index() writes to PostgreSQL: rows, keyword vectors, embeddings."""

from datetime import UTC, datetime

import pytest
from app.adapters.persistence.sqlalchemy.repositories import SqlDocumentRepo
from app.domain.documents import Chunk, Document, DocumentKind, DocumentStatus
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def _chunk(ordinal: int, content: str) -> Chunk:
    chunk = Chunk(
        ordinal, content, page_from=ordinal + 1, page_to=ordinal + 1, heading="H"
    )
    chunk.embedding = [0.0] * 1024
    chunk.embedding_model = "google/gemini-embedding-2"
    chunk.embedding[ordinal] = 1.0
    return chunk


def test_index_replaces_chunks_with_keyword_and_vector_rows(
    sessions: sessionmaker[Session],
) -> None:
    repo = SqlDocumentRepo(sessions)
    document = Document(
        id=repo.next_document_id(),
        campaign_id="ashfall",
        filename="Core.pdf",
        kind=DocumentKind.PDF,
        sha256="c" * 64,
        storage_key="0" * 32,
        uploaded_at=datetime(2026, 10, 19, tzinfo=UTC),
    )
    repo.add(document)
    document.status = DocumentStatus.INDEXED

    repo.index(document, [_chunk(0, "old text")])
    repo.index(document, [_chunk(0, "Starships jump"), _chunk(1, "Skill checks")])

    with sessions() as session:
        rows = session.execute(
            text(
                "SELECT ordinal, campaign_id, tsv @@ plainto_tsquery('simple', 'jump'),"
                " embedding <=> CAST(:probe AS vector), embedding_model FROM chunk"
                " WHERE document_id = :id ORDER BY ordinal"
            ),
            {"id": document.id, "probe": str([1.0] + [0.0] * 1023)},
        ).all()
    assert [(r[0], r[1], r[2]) for r in rows] == [
        (0, "ashfall", True),
        (1, "ashfall", False),
    ]
    assert rows[0][3] < rows[1][3]  # the vector search finds the matching chunk first
    assert {row[4] for row in rows} == {"google/gemini-embedding-2"}


def test_a_vector_from_an_unknown_model_is_rejected(
    sessions: sessionmaker[Session],
) -> None:
    """The foreign key to embedding_space keeps fake or stray vectors out (#64)."""
    repo = SqlDocumentRepo(sessions)
    document = Document(
        id=repo.next_document_id(),
        campaign_id="ashfall",
        filename="Core.pdf",
        kind=DocumentKind.PDF,
        sha256="d" * 64,
        storage_key="0" * 32,
        uploaded_at=datetime(2026, 10, 19, tzinfo=UTC),
    )
    repo.add(document)
    chunk = _chunk(0, "text")
    chunk.embedding_model = "fake"

    with pytest.raises(IntegrityError):
        repo.index(document, [chunk])
