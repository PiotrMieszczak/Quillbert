"""DEC-013: every campaign references exactly one system from the system table."""

import pytest
from alembic import command
from alembic.config import Config
from app.adapters.persistence.sqlalchemy.tables import CampaignRow, SystemRow
from sqlalchemy import create_engine, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


def test_systems_are_seeded_by_migration(sessions: sessionmaker[Session]) -> None:
    with sessions() as session:
        names = dict(session.execute(select(SystemRow.id, SystemRow.name)).all())
    assert names == {
        "dnd-2014": "D&D 2014",
        "dnd-2024": "D&D 2024",
        "traveller-2e": "Traveller 2e",
    }


@pytest.mark.parametrize("system_id", ["no-such-system", None])
def test_campaign_needs_an_existing_system(
    sessions: sessionmaker[Session], system_id: str | None
) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.add(
            CampaignRow(id="orphan", name="Orphan", system_id=system_id, tint="#000")
        )


def test_system_in_use_cannot_be_deleted(sessions: sessionmaker[Session]) -> None:
    with pytest.raises(IntegrityError), sessions.begin() as session:
        session.execute(text("DELETE FROM system WHERE id = 'dnd-2024'"))


def test_upgrade_backfills_existing_campaigns(
    migrated: str, alembic_config: Config
) -> None:
    """A campaign stored as free text before 0002 keeps its system after it."""
    engine = create_engine(migrated)
    try:
        command.downgrade(alembic_config, "0001")
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE campaign CASCADE"))
            connection.execute(
                text(
                    "INSERT INTO campaign (id, name, system, tint) VALUES "
                    "('ashfall', 'Ashfall', 'D&D 2024', '#000'), "
                    "('rimward', 'Rimward', 'Mothership 1e', '#000')"
                )
            )
        command.upgrade(alembic_config, "head")
        with engine.connect() as connection:
            rows = dict(
                connection.execute(text("SELECT id, system_id FROM campaign")).all()
            )
    finally:
        command.upgrade(alembic_config, "head")
        with engine.begin() as connection:
            connection.execute(text("TRUNCATE campaign CASCADE"))
            connection.execute(
                text(
                    "DELETE FROM system "
                    "WHERE id NOT IN ('dnd-2014', 'dnd-2024', 'traveller-2e')"
                )
            )
        engine.dispose()

    assert rows == {"ashfall": "dnd-2024", "rimward": "mothership-1e"}
