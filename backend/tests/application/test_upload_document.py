import io
from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.adapters.clock.frozen import FrozenClock
from app.adapters.files import LocalDiskFileStore
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.application.documents import GetDocument, ListDocuments, UploadDocument
from app.domain.documents import DocumentKind, DocumentStatus
from app.domain.shared import (
    FileTooLarge,
    NotFound,
    UnsupportedFileType,
    ValidationFailed,
)

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
PDF = b"%PDF-1.7\nfirst book"
MB = 1024 * 1024


def _stored(root: Path) -> list[Path]:
    return [path for path in root.rglob("*") if path.is_file()]


@pytest.fixture
def repo() -> InMemoryDocumentRepo:
    return InMemoryDocumentRepo(campaigns={"ashfall", "other"})


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path / "files"


@pytest.fixture
def upload(repo: InMemoryDocumentRepo, root: Path) -> UploadDocument:
    return UploadDocument(
        LocalDiskFileStore(root), repo, FrozenClock(NOW), max_bytes=MB
    )


def _put(
    upload: UploadDocument, name: str = "Core.pdf", data: bytes = PDF, cid="ashfall"
):
    return upload.execute(campaign_id=cid, filename=name, content=io.BytesIO(data))


def test_a_new_upload_is_queued_with_no_progress(
    upload: UploadDocument, root: Path
) -> None:
    result = _put(upload)

    assert result.created is True
    assert result.document.filename == "Core.pdf"
    assert result.document.kind is DocumentKind.PDF
    assert result.document.status is DocumentStatus.QUEUED
    assert result.document.progress == 0
    assert len(_stored(root)) == 1


def test_the_stored_file_sits_under_the_documents_storage_key(
    upload: UploadDocument, repo: InMemoryDocumentRepo, root: Path
) -> None:
    result = _put(upload)

    document = repo.get("ashfall", result.document.id)

    assert document is not None
    assert (root / document.storage_key[:2] / document.storage_key).read_bytes() == PDF


def test_the_same_bytes_again_return_the_existing_document_and_store_nothing(
    upload: UploadDocument, root: Path
) -> None:
    first = _put(upload, name="Core.pdf")
    again = _put(upload, name="Renamed copy.pdf")

    assert again.created is False
    assert again.document.id == first.document.id
    assert again.document.filename == "Core.pdf"
    assert len(_stored(root)) == 1


def test_the_same_bytes_in_another_campaign_are_a_new_document(
    upload: UploadDocument, root: Path
) -> None:
    first = _put(upload, cid="ashfall")
    second = _put(upload, cid="other")

    assert second.created is True
    assert second.document.id != first.document.id
    assert len(_stored(root)) == 2


@pytest.mark.parametrize(
    ("name", "data", "error"),
    [
        ("old.doc", PDF, UnsupportedFileType),
        ("fake.pdf", b"not a pdf", UnsupportedFileType),
        ("empty.txt", b"", ValidationFailed),
        ("", PDF, ValidationFailed),
        ("x" * 256 + ".pdf", PDF, ValidationFailed),
    ],
)
def test_a_rejected_file_stores_nothing(
    upload: UploadDocument, root: Path, name: str, data: bytes, error: type[Exception]
) -> None:
    with pytest.raises(error):
        _put(upload, name=name, data=data)
    assert _stored(root) == []


def test_an_oversize_file_is_rejected_and_stores_nothing(
    upload: UploadDocument, root: Path
) -> None:
    with pytest.raises(FileTooLarge):
        _put(upload, data=PDF + b"x" * MB)
    assert _stored(root) == []


def test_an_unknown_campaign_is_not_found_and_the_file_is_removed(
    upload: UploadDocument, root: Path
) -> None:
    with pytest.raises(NotFound):
        _put(upload, cid="nowhere")
    assert _stored(root) == []


def test_a_client_path_is_reduced_to_the_file_name(upload: UploadDocument) -> None:
    result = _put(upload, name=r"C:\Users\gm\Desktop\Core.pdf")
    assert result.document.filename == "Core.pdf"


def test_campaigns_do_not_see_each_others_documents(
    upload: UploadDocument, repo: InMemoryDocumentRepo
) -> None:
    mine = _put(upload, cid="ashfall").document
    listing = ListDocuments(repo)
    getting = GetDocument(repo)

    assert [d.id for d in listing.execute(campaign_id="ashfall")] == [mine.id]
    assert listing.execute(campaign_id="other") == []
    assert getting.execute(campaign_id="ashfall", document_id=mine.id).id == mine.id
    with pytest.raises(NotFound):
        getting.execute(campaign_id="other", document_id=mine.id)
