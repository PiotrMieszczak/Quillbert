import dataclasses
from typing import Any

from app.application.cast.views import character_view
from app.application.dto import CharacterView
from app.domain.cast import clean_character
from app.domain.shared import NotFound, ValidationFailed
from app.ports.repositories import CharacterRepo

# Fields a character always has: sending null for one is an error, not a clear.
REQUIRED = {"name", "is_player", "relationship", "stats", "tags"}
EDITABLE = REQUIRED | {
    "role",
    "level",
    "location",
    "disposition",
    "last_seen",
    "quote",
    "notes",
    "player_profile",
}


class UpdateCharacter:
    """Changes only the fields given; a field given as None is cleared."""

    def __init__(self, repo: CharacterRepo) -> None:
        self._repo = repo

    def execute(
        self, *, campaign_id: str, character_id: int, changes: dict[str, Any]
    ) -> CharacterView:
        unknown = changes.keys() - EDITABLE
        if unknown:
            raise ValidationFailed(f"cannot change {', '.join(sorted(unknown))}")
        cleared = sorted(k for k in REQUIRED & changes.keys() if changes[k] is None)
        if cleared:
            raise ValidationFailed(f"{', '.join(cleared)} cannot be cleared")
        current = self._repo.get(campaign_id, character_id)
        if current is None:
            raise NotFound("character not found")
        changes = dict(changes)
        # Demoting a player to an NPC drops the profile rather than rejecting the edit.
        if changes.get("is_player") is False and "player_profile" not in changes:
            changes["player_profile"] = None
        if "tags" in changes:
            changes["tags"] = tuple(changes["tags"])
        character = clean_character(dataclasses.replace(current, **changes))
        self._repo.update(character)
        return character_view(character)
