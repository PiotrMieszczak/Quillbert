from sqlalchemy import delete, func, select, text, tuple_
from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import CharacterRow
from app.domain.cast import Character, Relationship
from app.domain.shared import NotFound

# Matches Character.sort_key: the column's "C" collation orders by code point.
_SORT_NAME = func.lower(CharacterRow.name)


class SqlCharacterRepo:
    """CharacterRepo over PostgreSQL. Every query filters on campaign_id."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def next_character_id(self) -> int:
        # The port hands out ids before insert; the identity column's sequence is
        # safe under concurrent callers.
        with self._sessions() as session:
            return session.execute(
                text("SELECT nextval(pg_get_serial_sequence('character', 'id'))")
            ).scalar_one()

    def add(self, character: Character) -> None:
        with self._sessions.begin() as session:
            session.add(mappers.character_to_row(character))

    def get(self, campaign_id: str, character_id: int) -> Character | None:
        with self._sessions() as session:
            row = session.get(CharacterRow, character_id)
            if row is None or row.campaign_id != campaign_id:
                return None
            return mappers.character_from_row(row)

    def update(self, character: Character) -> None:
        with self._sessions.begin() as session:
            row = session.get(CharacterRow, character.id)
            if row is None or row.campaign_id != character.campaign_id:
                raise NotFound("character not found")
            session.merge(mappers.character_to_row(character))

    def remove(self, campaign_id: str, character_id: int) -> Character | None:
        query = (
            delete(CharacterRow)
            .where(
                CharacterRow.id == character_id,
                CharacterRow.campaign_id == campaign_id,
            )
            .returning(CharacterRow)
        )
        with self._sessions.begin() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.character_from_row(row)

    def page(
        self,
        campaign_id: str,
        *,
        is_player: bool | None,
        relationship: Relationship | None,
        name_contains: str | None,
        after: tuple[str, int] | None,
        limit: int,
    ) -> list[Character]:
        query = select(CharacterRow).where(CharacterRow.campaign_id == campaign_id)
        if is_player is not None:
            query = query.where(CharacterRow.is_player == is_player)
        if relationship is not None:
            query = query.where(CharacterRow.relationship == relationship.value)
        if name_contains:
            # autoescape: a % or _ in the search is text, not a wildcard.
            query = query.where(
                func.lower(CharacterRow.name).contains(
                    name_contains.lower(), autoescape=True
                )
            )
        if after is not None:
            query = query.where(tuple_(_SORT_NAME, CharacterRow.id) > after)
        query = query.order_by(_SORT_NAME, CharacterRow.id).limit(limit)
        with self._sessions() as session:
            return [mappers.character_from_row(row) for row in session.scalars(query)]
