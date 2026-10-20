import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from app.adapters.persistence.sqlalchemy.embedding_space import check_embedding_space
from app.adapters.persistence.sqlalchemy.tables import Base
from sqlalchemy import create_engine, text
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


def test_every_public_table_has_row_level_security(migrated: str) -> None:
    """Supabase serves the public schema over its Data API: a table without RLS is open
    to anyone holding the publishable key. A new table's migration must enable it."""
    engine = create_engine(migrated)
    with engine.connect() as connection:
        open_tables = (
            connection.execute(
                text(
                    "SELECT c.relname FROM pg_class c "
                    "JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'public' AND c.relkind = 'r' "
                    "AND NOT c.relrowsecurity ORDER BY 1"
                )
            )
            .scalars()
            .all()
        )
    engine.dispose()
    assert open_tables == []
