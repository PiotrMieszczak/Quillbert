import dataclasses
from typing import Any

from app.application.cast.views import character_view
from app.application.dto import CharacterView
from app.domain.campaigns import clean_name
from app.domain.cast import (
    Character,
    PlayerProfile,
    Relationship,
    check_level,
    check_stats,
    clean_tags,
    clean_text,
)
from app.domain.shared import ValidationFailed
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
        if player_profile is not None and not is_player:
            raise ValidationFailed("only a player character has a player profile")
        character = Character(
            id=self._repo.next_character_id(),
            campaign_id=campaign_id,
            name=clean_name(name, "character name"),
            is_player=is_player,
            relationship=relationship,
            role=clean_text(role),
            level=check_level(level),
            location=clean_text(location),
            disposition=clean_text(disposition),
            last_seen=clean_text(last_seen),
            stats=check_stats(stats or {}),
            tags=clean_tags(tags or []),
            quote=clean_text(quote),
            notes=clean_text(notes),
            player_profile=_clean_profile(player_profile) if is_player else None,
        )
        self._repo.add(character)
        return character_view(character)


def _clean_profile(profile: PlayerProfile | None) -> PlayerProfile:
    # A player always has a profile, even an empty one; the Players page relies on it.
    if profile is None:
        return PlayerProfile()
    return PlayerProfile(
        **{
            f.name: clean_text(getattr(profile, f.name))
            for f in dataclasses.fields(profile)
        }
    )
