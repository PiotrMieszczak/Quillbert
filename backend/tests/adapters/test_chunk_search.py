"""Hybrid retrieval on real PostgreSQL: keyword leg, vector leg, fusion, scope."""

from datetime import UTC, datetime

import pytest
from app.adapters.persistence.sqlalchemy.repositories import (
    SqlChunkSearch,
    SqlDocumentRepo,
)
from app.domain.documents import Chunk, Document, DocumentKind, DocumentStatus
from sqlalchemy.orm import Session, sessionmaker

FLOOR = 0.5


def _vector(axis: int) -> list[float]:
    """A unit vector along one axis: cosine similarity 1 to itself, 0 to the rest."""
    vector = [0.0] * 1024
    vector[axis] = 1.0
    return vector


def _chunk(ordinal: int, content: str, axis: int | None) -> Chunk:
    chunk = Chunk(
        ordinal, content, page_from=ordinal + 1, page_to=ordinal + 1, heading="H"
    )
    if axis is not None:
        chunk.embedding = _vector(axis)
        chunk.embedding_model = "google/gemini-embedding-2"
    return chunk


def _index(
    repo: SqlDocumentRepo,
    campaign_id: str,
    filename: str,
    chunks: list[Chunk],
    status: DocumentStatus = DocumentStatus.INDEXED,
) -> Document:
    document = Document(
        id=repo.next_document_id(),
        campaign_id=campaign_id,
        filename=filename,
        kind=DocumentKind.PDF,
        sha256=f"{repo.next_document_id():064d}",
        storage_key="0" * 32,
        uploaded_at=datetime(2026, 10, 19, tzinfo=UTC),
    )
    repo.add(document)
    document.status = status
    repo.index(document, chunks)
    return document


@pytest.fixture
def repo(sessions: sessionmaker[Session]) -> SqlDocumentRepo:
    return SqlDocumentRepo(sessions)


@pytest.fixture
def search(sessions: sessionmaker[Session]) -> SqlChunkSearch:
    return SqlChunkSearch(sessions, FLOOR)


def test_a_keyword_hit_carries_its_citation_fields(
    repo: SqlDocumentRepo, search: SqlChunkSearch
) -> None:
    document = _index(
        repo,
        "ashfall",
        "Core.pdf",
        [
            _chunk(0, "Starships jump between worlds", None),
            _chunk(1, "Skill checks", None),
        ],
    )

    hits = search.search("ashfall", None, "jump", None, 6)

    assert [(h.document_id, h.filename, h.page_from, h.heading) for h in hits] == [
        (document.id, "Core.pdf", 1, "H")
    ]
    assert hits[0].content == "Starships jump between worlds"
    assert hits[0].score > 0


def test_a_vector_hit_needs_no_shared_words(
    repo: SqlDocumentRepo, search: SqlChunkSearch
) -> None:
    _index(repo, "ashfall", "Core.pdf", [_chunk(0, "alpha", 0), _chunk(1, "beta", 1)])

    hits = search.search("ashfall", None, "unrelated words", _vector(1), 6)

    assert [h.content for h in hits] == ["beta"]


def test_fusion_ranks_a_chunk_both_legs_found_above_one_leg(
    repo: SqlDocumentRepo, search: SqlChunkSearch
) -> None:
    _index(
        repo,
        "ashfall",
        "Core.pdf",
        [
            _chunk(0, "dragon lair", 0),  # keyword only (its vector is far off)
            _chunk(1, "unrelated prose", 1),  # vector only
            _chunk(2, "dragon hoard", 1),  # both
        ],
    )

    hits = search.search("ashfall", None, "dragon", _vector(1), 6)

    # lair and prose tie at 1/61, so the lower chunk id comes first.
    assert [h.content for h in hits] == [
        "dragon hoard",
        "dragon lair",
        "unrelated prose",
    ]
    assert hits[0].score > hits[1].score >= hits[2].score


def test_k_trims_the_fused_list(repo: SqlDocumentRepo, search: SqlChunkSearch) -> None:
    _index(
        repo,
        "ashfall",
        "Core.pdf",
        [_chunk(i, f"dragon {i}", None) for i in range(4)],
    )

    assert len(search.search("ashfall", None, "dragon", None, 2)) == 2


def test_nothing_above_the_floor_is_no_result(
    repo: SqlDocumentRepo, search: SqlChunkSearch
) -> None:
    _index(repo, "ashfall", "Core.pdf", [_chunk(0, "alpha", 0)])

    assert search.search("ashfall", None, "nothing matches", _vector(1), 6) == []
    assert search.search("ashfall", None, "", None, 6) == []


def test_a_higher_floor_drops_a_weaker_vector_match(
    repo: SqlDocumentRepo, sessions: sessionmaker[Session]
) -> None:
    half = [0.0] * 1024
    half[0] = half[1] = 0.5**0.5  # cosine similarity 0.707 to axis 0
    chunk = _chunk(0, "alpha", None)
    chunk.embedding = half
    chunk.embedding_model = "google/gemini-embedding-2"
    _index(repo, "ashfall", "Core.pdf", [chunk])

    assert SqlChunkSearch(sessions, 0.7).search("ashfall", None, "x", _vector(0), 6)
    assert not SqlChunkSearch(sessions, 0.8).search("ashfall", None, "x", _vector(0), 6)


def test_another_campaigns_chunks_are_never_returned(
    repo: SqlDocumentRepo, search: SqlChunkSearch
) -> None:
    _index(repo, "other", "Secret.pdf", [_chunk(0, "dragon secret", 0)])

    assert search.search("ashfall", None, "dragon", _vector(0), 6) == []
    assert len(search.search("other", None, "dragon", _vector(0), 6)) == 1


@pytest.mark.parametrize(
    "status",
    [
        DocumentStatus.QUEUED,
        DocumentStatus.PROCESSING,
        DocumentStatus.FAILED,
        DocumentStatus.AWAITING_OCR,
    ],
)
def test_documents_that_are_not_indexed_are_excluded(
    repo: SqlDocumentRepo, search: SqlChunkSearch, status: DocumentStatus
) -> None:
    _index(repo, "ashfall", "Half.pdf", [_chunk(0, "dragon", 0)], status=status)

    assert search.search("ashfall", None, "dragon", _vector(0), 6) == []


def test_a_chunk_without_an_embedding_is_still_found_by_keyword(
    repo: SqlDocumentRepo, search: SqlChunkSearch
) -> None:
    _index(repo, "ashfall", "Core.pdf", [_chunk(0, "dragon", None)])

    assert len(search.search("ashfall", None, "dragon", _vector(0), 6)) == 1
