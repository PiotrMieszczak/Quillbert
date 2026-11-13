from typing import Any

from app.application.cast.views import character_view
from app.application.dto import CharacterView
from app.domain.cast import Character, PlayerProfile, Relationship, clean_character
from app.ports.repositories import CharacterRepo


class CreateCharacter:
    def __init__(self, repo: CharacterRepo) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        campaign_id: str,
        name: str,
        is_player: bool,
        relationship: Relationship,
        role: str | None = None,
        level: int | None = None,
        location: str | None = None,
        disposition: str | None = None,
        last_seen: str | None = None,
        stats: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        quote: str | None = None,
        notes: str | None = None,
        player_profile: PlayerProfile | None = None,
    ) -> CharacterView:
        character = clean_character(
            Character(
                id=0,
                campaign_id=campaign_id,
                name=name,
                is_player=is_player,
                relationship=relationship,
                role=role,
                level=level,
                location=location,
                disposition=disposition,
                last_seen=last_seen,
                stats=stats or {},
                tags=tuple(tags or ()),
                quote=quote,
                notes=notes,
                player_profile=player_profile,
            )
        )
        # The id is taken only once the character is valid, so a rejected one uses none.
        character.id = self._repo.next_character_id()
        self._repo.add(character)
        return character_view(character)
