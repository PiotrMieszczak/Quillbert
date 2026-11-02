from dataclasses import dataclass, field
from typing import Any

from app.domain.cast.values import Relationship


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
