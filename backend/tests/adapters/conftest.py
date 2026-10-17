import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.adapters.persistence.sqlalchemy.engine import create_session_factory
from app.adapters.persistence.sqlalchemy.repositories import (
    SqlConversationRepo,
    SqlDocumentRepo,
)
from app.adapters.persistence.sqlalchemy.tables import CampaignRow
from app.ports.repositories import ConversationRepo, DocumentRepo
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

BACKEND = Path(__file__).resolve().parents[2]
CAMPAIGNS = {"ashfall", "other"}


def _alembic(url: str) -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option(
        "script_location", str(BACKEND / config.get_main_option("script_location"))
    )
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        return url
    if os.environ.get("CI"):
        pytest.fail(
            "TEST_DATABASE_URL must be set in CI; Postgres tests may not skip there."
        )
    pytest.skip("TEST_DATABASE_URL is not set; skipping Postgres tests.")


@pytest.fixture(scope="session")
def migrated(database_url: str) -> str:
    """Upgrade, downgrade, upgrade: every migration must run both ways."""
    config = _alembic(database_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    return database_url


@pytest.fixture
def alembic_config(migrated: str) -> Config:
    return _alembic(migrated)


@pytest.fixture
def sessions(migrated: str) -> Iterator[sessionmaker[Session]]:
    factory = create_session_factory(migrated)
    with factory.begin() as session:
        session.execute(
            text(
                "TRUNCATE document, message, conversation, campaign "
                "RESTART IDENTITY CASCADE"
            )
        )
        # system rows are reference data from migration 0002 and are not truncated.
        session.add_all(
            CampaignRow(id=cid, name=cid.title(), system_id="dnd-2024", tint="#000000")
            for cid in sorted(CAMPAIGNS)
        )
    yield factory
    factory.kw["bind"].dispose()


@pytest.fixture(params=["memory", "postgres"])
def conversation_repo(request: pytest.FixtureRequest) -> ConversationRepo:
    if request.param == "memory":
        return InMemoryConversationRepo(campaigns=CAMPAIGNS)
    return SqlConversationRepo(request.getfixturevalue("sessions"))


@pytest.fixture(params=["memory", "postgres"])
def document_repo(request: pytest.FixtureRequest) -> DocumentRepo:
    if request.param == "memory":
        return InMemoryDocumentRepo(campaigns=CAMPAIGNS)
    return SqlDocumentRepo(request.getfixturevalue("sessions"))
