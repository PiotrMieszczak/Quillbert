import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from app.adapters.persistence.sqlalchemy.embedding_space import check_embedding_space
from app.adapters.persistence.sqlalchemy.tables import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def test_migrations_match_the_table_models(migrated: str) -> None:
    """Fails when tables.py changes without a migration (or the reverse)."""
    engine = create_engine(migrated)
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    engine.dispose()
    assert diff == []


def test_embedding_space_names_the_configured_model(
    sessions: sessionmaker[Session],
) -> None:
    check_embedding_space(sessions, "google/gemini-embedding-2", 1024)
    with pytest.raises(RuntimeError, match="re-embed migration"):
        check_embedding_space(sessions, "voyage-4", 1024)
