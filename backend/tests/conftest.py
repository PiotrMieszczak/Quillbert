from datetime import UTC, datetime

import pytest
from app.adapters.clock.frozen import FrozenClock
from app.adapters.llm.fake import FakeLLM
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.composition import UseCases, build_app, build_use_cases
from app.ports.auth import Identity, InvalidToken

FROZEN = datetime(2026, 10, 7, 14, 0, tzinfo=UTC)


GOOD_TOKEN = "good-token"


class FakeVerifier:
    def verify(self, token: str) -> Identity:
        if token != GOOD_TOKEN:
            raise InvalidToken("nope")
        return Identity(user_id="user-1", email="gm@ashfall.table")


@pytest.fixture
def repo() -> InMemoryConversationRepo:
    return InMemoryConversationRepo()


@pytest.fixture
def use_cases(repo: InMemoryConversationRepo) -> UseCases:
    return build_use_cases(
        repo=repo, llm=FakeLLM(), clock=FrozenClock(FROZEN), verifier=FakeVerifier()
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
