from sqlalchemy import delete, func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import FactionRow
from app.domain.cast import Faction
from app.domain.shared import NotFound


class SqlFactionRepo:
    """FactionRepo over PostgreSQL. Every query filters on campaign_id."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def next_faction_id(self) -> int:
        with self._sessions() as session:
            return session.execute(
                text("SELECT nextval(pg_get_serial_sequence('faction', 'id'))")
            ).scalar_one()

    def add(self, faction: Faction) -> None:
        with self._sessions.begin() as session:
            session.add(mappers.faction_to_row(faction))

    def get(self, campaign_id: str, faction_id: int) -> Faction | None:
        with self._sessions() as session:
            row = session.get(FactionRow, faction_id)
            if row is None or row.campaign_id != campaign_id:
                return None
            return mappers.faction_from_row(row)

    def update(self, faction: Faction) -> None:
        with self._sessions.begin() as session:
            row = session.get(FactionRow, faction.id)
            if row is None or row.campaign_id != faction.campaign_id:
                raise NotFound("faction not found")
            session.merge(mappers.faction_to_row(faction))

    def remove(self, campaign_id: str, faction_id: int) -> Faction | None:
        query = (
            delete(FactionRow)
            .where(FactionRow.id == faction_id, FactionRow.campaign_id == campaign_id)
            .returning(FactionRow)
        )
        with self._sessions.begin() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.faction_from_row(row)

    def list(self, campaign_id: str) -> list[Faction]:
        # The column's "C" collation makes this match Faction.sort_key.
        query = (
            select(FactionRow)
            .where(FactionRow.campaign_id == campaign_id)
            .order_by(func.lower(FactionRow.name), FactionRow.id)
        )
        with self._sessions() as session:
            return [mappers.faction_from_row(row) for row in session.scalars(query)]
