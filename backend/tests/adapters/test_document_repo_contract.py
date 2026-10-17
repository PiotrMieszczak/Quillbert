"""One suite, every DocumentRepo. If both pass, swapping them changes nothing."""

from datetime import UTC, datetime

import pytest
from app.domain.documents import Document, DocumentKind, DocumentStatus
from app.domain.shared import NotFound
from app.ports.repositories import DocumentRepo

T0 = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


def _document(
    repo: DocumentRepo, campaign_id: str = "ashfall", sha256: str = "a" * 64
) -> Document:
    document = Document(
        id=repo.next_document_id(),
        campaign_id=campaign_id,
        filename="Core Rulebook.pdf",
        kind=DocumentKind.PDF,
        sha256=sha256,
        storage_key="0" * 32,
        uploaded_at=T0,
    )
    repo.add(document)
    return document


def test_ids_are_unique(document_repo: DocumentRepo) -> None:
    assert document_repo.next_document_id() != document_repo.next_document_id()


def test_added_document_reads_back_with_its_defaults(
    document_repo: DocumentRepo,
) -> None:
    added = _document(document_repo)

    read = document_repo.get("ashfall", added.id)

    assert read == added
    assert read is not None
    assert read.status is DocumentStatus.QUEUED
    assert read.progress == 0
    assert read.page_count is None


def test_a_document_is_invisible_from_another_campaign(
    document_repo: DocumentRepo,
) -> None:
    added = _document(document_repo, campaign_id="ashfall")

    assert document_repo.get("other", added.id) is None
    assert document_repo.list_for_campaign("other") == []
    assert document_repo.find_by_sha256("other", added.sha256) is None


def test_list_is_oldest_first(document_repo: DocumentRepo) -> None:
    first = _document(document_repo, sha256="1" * 64)
    second = _document(document_repo, sha256="2" * 64)

    assert [d.id for d in document_repo.list_for_campaign("ashfall")] == [
        first.id,
        second.id,
    ]


def test_find_by_sha256_finds_the_copy_in_that_campaign(
    document_repo: DocumentRepo,
) -> None:
    added = _document(document_repo, sha256="b" * 64)

    found = document_repo.find_by_sha256("ashfall", "b" * 64)

    assert found is not None
    assert found.id == added.id
    assert document_repo.find_by_sha256("ashfall", "c" * 64) is None


def test_the_same_file_may_live_in_two_campaigns(document_repo: DocumentRepo) -> None:
    _document(document_repo, campaign_id="ashfall", sha256="d" * 64)
    _document(document_repo, campaign_id="other", sha256="d" * 64)

    assert len(document_repo.list_for_campaign("ashfall")) == 1
    assert len(document_repo.list_for_campaign("other")) == 1


def test_unknown_campaign_is_not_found(document_repo: DocumentRepo) -> None:
    with pytest.raises(NotFound):
        _document(document_repo, campaign_id="nowhere")
