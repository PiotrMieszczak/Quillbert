import io
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.adapters.clock.frozen import FrozenClock
from app.adapters.extraction import FileExtractor
from app.adapters.files import LocalDiskFileStore
from app.adapters.llm.fake_embedder import FakeEmbedder
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.application.documents import IngestDocument, IngestOutcome, UploadDocument
from app.domain.documents import Block, DocumentStatus, Page, Shelf
from app.ports.embeddings import EmbeddingUnavailable, Purpose
from app.ports.extraction import Extraction, ExtractionFailed, NeedsOcr

NOW = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
NOTES = b"# Skills\n\n" + b"Roll two dice and add the modifier. " * 120


class _DownEmbedder(FakeEmbedder):
    def embed(self, texts: Sequence[str], purpose: Purpose) -> list[list[float]]:
        raise EmbeddingUnavailable("503")


class _Extractor:
    def __init__(self, failure: Exception | None = None, pages=()) -> None:
        self._failure = failure
        self._pages = pages

    def extract(self, data: bytes, filename: str) -> Extraction:
        def pages():
            yield from self._pages
            if self._failure:
                raise self._failure

        return Extraction(page_count=max(len(self._pages), 1), pages=pages())


@pytest.fixture
def repo() -> InMemoryDocumentRepo:
    return InMemoryDocumentRepo()


@pytest.fixture
def files(tmp_path: Path) -> LocalDiskFileStore:
    return LocalDiskFileStore(tmp_path / "files")


def _upload(repo, files, name: str = "notes.md", data: bytes = NOTES) -> int:
    upload = UploadDocument(files, repo, FrozenClock(NOW), max_bytes=10**7)
    result = upload.execute(
        shelf=Shelf.campaign("ashfall"), filename=name, content=io.BytesIO(data)
    )
    return result.document.id


def _ingest(repo, files, extractor=None, embedder=None) -> IngestDocument:
    return IngestDocument(
        files, repo, extractor or FileExtractor(ocr=None), embedder or FakeEmbedder()
    )


def test_a_queued_document_is_extracted_chunked_embedded_and_indexed(
    repo, files
) -> None:
    document_id = _upload(repo, files)

    assert _ingest(repo, files).execute() is IngestOutcome.DONE

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert document is not None
    assert document.status is DocumentStatus.INDEXED
    assert document.progress == 100
    assert document.page_count is None  # Markdown has no pages
    chunks = repo.chunks[document_id]
    assert len(chunks) > 1
    assert document.meta == f"{len(chunks)} passages"
    assert all(len(c.embedding or []) == 1024 for c in chunks)
    assert {c.embedding_model for c in chunks} == {"fake"}
    assert chunks[0].heading == "Skills"


def test_nothing_queued_is_idle(repo, files) -> None:
    assert _ingest(repo, files).execute() is IngestOutcome.IDLE


def test_an_unreadable_file_fails_with_its_reason(repo, files) -> None:
    document_id = _upload(repo, files)
    extractor = _Extractor(ExtractionFailed("the PDF is password-protected"))

    _ingest(repo, files, extractor).execute()

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert document is not None
    assert document.status is DocumentStatus.FAILED
    assert document.error == "the PDF is password-protected"


def test_a_scan_without_ocr_waits_for_ocr(repo, files) -> None:
    document_id = _upload(repo, files)

    _ingest(repo, files, _Extractor(NeedsOcr("page 1"))).execute()

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert document is not None and document.status is DocumentStatus.AWAITING_OCR


def test_no_readable_text_fails(repo, files) -> None:
    document_id = _upload(repo, files)

    _ingest(repo, files, _Extractor(pages=[Page(1, (), ocr=True)])).execute()

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert document is not None
    assert (document.status, document.error) == (
        DocumentStatus.FAILED,
        "no readable text",
    )


def test_an_embedder_outage_requeues_instead_of_failing(repo, files) -> None:
    document_id = _upload(repo, files)

    outcome = _ingest(repo, files, embedder=_DownEmbedder()).execute()

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert outcome is IngestOutcome.DEFERRED
    assert document is not None
    assert (document.status, document.progress) == (DocumentStatus.QUEUED, 0)
    assert document_id not in repo.chunks


def test_scanned_and_unreadable_pages_are_reported(repo, files) -> None:
    document_id = _upload(repo, files, "scan.pdf", b"%PDF-1.7\n")
    pages = [
        Page(1, (Block("Readable page " * 20),)),
        Page(2, (Block("Scanned page " * 20),), ocr=True),
        Page(3, (), ocr=True),
    ]

    _ingest(repo, files, _Extractor(pages=pages)).execute()

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert document is not None
    assert document.page_count == 3
    assert document.meta == "1 passages · 2 scanned pages · 1 unreadable"


def test_an_unexpected_error_fails_the_document_instead_of_sticking(
    repo, files
) -> None:
    document_id = _upload(repo, files)

    _ingest(repo, files, _Extractor(RuntimeError("bug"))).execute()

    document = repo.get(Shelf.campaign("ashfall"), document_id)
    assert document is not None
    assert (document.status, document.error) == (
        DocumentStatus.FAILED,
        "internal error",
    )
