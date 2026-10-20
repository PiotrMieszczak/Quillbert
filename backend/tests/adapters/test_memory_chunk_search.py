from datetime import UTC, datetime

from app.adapters.persistence.memory.chunk_search import InMemoryChunkSearch
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.domain.documents import Chunk, Document, DocumentKind, DocumentStatus


def _repo(campaign_id: str = "ashfall", status=DocumentStatus.INDEXED):
    repo = InMemoryDocumentRepo()
    document = Document(
        id=repo.next_document_id(),
        campaign_id=campaign_id,
        filename="Core.pdf",
        kind=DocumentKind.PDF,
        sha256="a" * 64,
        storage_key="0" * 32,
        uploaded_at=datetime(2026, 10, 19, tzinfo=UTC),
    )
    repo.add(document)
    document.status = status
    repo.index(
        document,
        [Chunk(0, "Starships jump", 1, 1, "H"), Chunk(1, "Skill checks", 2, 2, None)],
    )
    return repo


def test_ranks_chunks_by_keyword_overlap() -> None:
    hits = InMemoryChunkSearch(_repo()).search(
        "ashfall", None, "starships jump", None, 6
    )

    assert [h.content for h in hits] == ["Starships jump"]
    assert (hits[0].filename, hits[0].page_from, hits[0].heading) == (
        "Core.pdf",
        1,
        "H",
    )


def test_scopes_to_the_campaign_and_to_indexed_documents() -> None:
    assert InMemoryChunkSearch(_repo()).search("other", None, "jump", None, 6) == []
    queued = _repo(status=DocumentStatus.QUEUED)
    assert InMemoryChunkSearch(queued).search("ashfall", None, "jump", None, 6) == []
