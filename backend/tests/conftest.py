from datetime import UTC, datetime
from pathlib import Path

import pytest
from app.adapters.clock.frozen import FrozenClock
from app.adapters.files import LocalDiskFileStore
from app.adapters.llm.fake import FakeLLM
from app.adapters.persistence.memory.campaigns import SYSTEMS, InMemoryCampaignRepo
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.composition import UseCases, build_app, build_use_cases
from app.domain.campaigns import Campaign
from app.domain.documents import Chunk, Document, DocumentKind, DocumentStatus
from app.ports.auth import Identity, InvalidToken

FROZEN = datetime(2026, 10, 7, 14, 0, tzinfo=UTC)


GOOD_TOKEN = "good-token"
USER_ID = "user-1"


def owned_campaigns(*ids: str, owner_id: str = USER_ID) -> InMemoryCampaignRepo:
    """Campaigns the test user owns, so routes under /campaigns/{id} let them in."""
    return InMemoryCampaignRepo(
        [
            Campaign(
                id=cid,
                owner_id=owner_id,
                name=cid.title(),
                system=SYSTEMS[1],
                tint="#E8B87A",
                created_at=FROZEN,
            )
            for cid in ids
        ]
    )


class FakeVerifier:
    def verify(self, token: str) -> Identity:
        if token != GOOD_TOKEN:
            raise InvalidToken("nope")
        return Identity(user_id=USER_ID, email="gm@ashfall.table")


@pytest.fixture
def repo() -> InMemoryConversationRepo:
    return InMemoryConversationRepo()


@pytest.fixture
def document_repo() -> InMemoryDocumentRepo:
    return InMemoryDocumentRepo()


@pytest.fixture
def file_store(tmp_path: Path) -> LocalDiskFileStore:
    return LocalDiskFileStore(tmp_path / "files")


@pytest.fixture
def campaign_repo() -> InMemoryCampaignRepo:
    return owned_campaigns("ashfall", "other")


@pytest.fixture
def fake_llm() -> FakeLLM:
    return FakeLLM()


def index_document(
    documents: InMemoryDocumentRepo,
    campaign_id: str,
    filename: str,
    *chunks: str,
) -> Document:
    """An indexed document whose chunks are `chunks`, one per page."""
    document = Document(
        id=documents.next_document_id(),
        campaign_id=campaign_id,
        filename=filename,
        kind=DocumentKind.PDF,
        sha256=f"{documents.next_document_id():064d}",
        storage_key="0" * 32,
        uploaded_at=FROZEN,
    )
    documents.add(document)
    document.status = DocumentStatus.INDEXED
    documents.index(
        document,
        [Chunk(n, text, n + 1, n + 1, "Grappling") for n, text in enumerate(chunks)],
    )
    return document


@pytest.fixture
def use_cases(
    fake_llm: FakeLLM,
    campaign_repo: InMemoryCampaignRepo,
    repo: InMemoryConversationRepo,
    document_repo: InMemoryDocumentRepo,
    file_store: LocalDiskFileStore,
) -> UseCases:
    return build_use_cases(
        repo=repo,
        llm=fake_llm,
        clock=FrozenClock(FROZEN),
        verifier=FakeVerifier(),
        documents=document_repo,
        files=file_store,
        campaigns=campaign_repo,
    )


@pytest.fixture
def start(use_cases: UseCases) -> StartConversation:
    return use_cases.start_conversation


@pytest.fixture
def run_turn(use_cases: UseCases) -> RunAssistantTurn:
    return use_cases.run_turn


@pytest.fixture
def list_messages(use_cases: UseCases) -> ListMessages:
    return use_cases.list_messages


@pytest.fixture
def anonymous_client(use_cases: UseCases):
    from fastapi.testclient import TestClient

    with TestClient(build_app(use_cases)) as test_client:
        yield test_client


@pytest.fixture
def client(use_cases: UseCases):
    from fastapi.testclient import TestClient

    headers = {"Authorization": f"Bearer {GOOD_TOKEN}"}
    with TestClient(build_app(use_cases), headers=headers) as test_client:
        yield test_client
