import dataclasses

from app.domain.cast import Character, Relationship
from app.domain.shared import NotFound


class InMemoryCharacterRepo:
    def __init__(self) -> None:
        self._characters: dict[int, Character] = {}
        self._next_id = 1

    def next_character_id(self) -> int:
        ident = self._next_id
        self._next_id += 1
        return ident

    def add(self, character: Character) -> None:
        self._characters[character.id] = dataclasses.replace(character)

    def get(self, campaign_id: str, character_id: int) -> Character | None:
        character = self._characters.get(character_id)
        if character is None or character.campaign_id != campaign_id:
            return None
        return dataclasses.replace(character)

    def update(self, character: Character) -> None:
        if self.get(character.campaign_id, character.id) is None:
            raise NotFound("character not found")
        self._characters[character.id] = dataclasses.replace(character)

    def remove(self, campaign_id: str, character_id: int) -> Character | None:
        character = self.get(campaign_id, character_id)
        if character is not None:
            del self._characters[character_id]
        return character

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
        needle = name_contains.lower() if name_contains else None
        matches = [
            c
            for c in self._characters.values()
            if c.campaign_id == campaign_id
            and (is_player is None or c.is_player == is_player)
            and (relationship is None or c.relationship == relationship)
            and (needle is None or needle in c.name.lower())
            and (after is None or c.sort_key > after)
        ]
        matches.sort(key=lambda c: c.sort_key)
        return [dataclasses.replace(c) for c in matches[:limit]]
