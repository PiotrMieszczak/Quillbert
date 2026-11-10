import dataclasses
from dataclasses import dataclass, field
from typing import Any

from app.domain.campaigns import clean_name
from app.domain.cast.values import (
    Relationship,
    check_level,
    check_stats,
    clean_tags,
    clean_text,
)
from app.domain.shared import ValidationFailed


@dataclass(frozen=True)
class PlayerProfile:
    """The player-character extension, always read with its character."""

    player_name: str | None = None
    character_class: str | None = None
    race: str | None = None
    background: str | None = None
    xp: str | None = None
    pronouns: str | None = None
    bonds: str | None = None


@dataclass
class Character:
    """Mirrors docs/data-model.md `character`: NPCs and player characters, split by
    `is_player`. Belongs to one campaign."""

    id: int
    campaign_id: str
    name: str
    is_player: bool
    relationship: Relationship
    role: str | None = None
    level: int | None = None
    location: str | None = None
    disposition: str | None = None
    last_seen: str | None = None
    # Keyed by the campaign system's sheet once one exists (ADR-0030); free until then.
    stats: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    quote: str | None = None
    # GM-private: never in assistant context unless asked for (DEC-004).
    notes: str | None = None
    portrait_key: str | None = None
    # Present only when is_player.
    player_profile: PlayerProfile | None = None

    @property
    def sort_key(self) -> tuple[str, int]:
        """List order and paging key; the SQL repo orders by lower(name), id."""
        return (self.name.lower(), self.id)


def clean_character(character: Character) -> Character:
    """The character with its text cleaned, or ValidationFailed. Create and update both
    pass through here, so the rules cannot drift apart."""
    if character.player_profile is not None and not character.is_player:
        raise ValidationFailed("only a player character has a player profile")
    return dataclasses.replace(
        character,
        name=clean_name(character.name, "character name"),
        role=clean_text(character.role),
        level=check_level(character.level),
        location=clean_text(character.location),
        disposition=clean_text(character.disposition),
        last_seen=clean_text(character.last_seen),
        stats=check_stats(character.stats),
        tags=clean_tags(list(character.tags)),
        quote=clean_text(character.quote),
        notes=clean_text(character.notes),
        player_profile=_clean_profile(character.player_profile)
        if character.is_player
        else None,
    )


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
