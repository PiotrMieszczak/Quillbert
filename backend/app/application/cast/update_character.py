import dataclasses
from typing import Any

from app.application.cast.views import character_view
from app.application.dto import CharacterView
from app.domain.cast import clean_character
from app.domain.shared import NotFound, ValidationFailed
from app.domain.sheets import validate_stats
from app.ports.repositories import CharacterRepo, SheetRepo

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
    "bio",
    "player_profile",
}


class UpdateCharacter:
    """Changes only the fields given; a field given as None is cleared."""

    def __init__(self, repo: CharacterRepo, sheets: SheetRepo) -> None:
        self._repo = repo
        self._sheets = sheets

    def execute(
        self,
        *,
        campaign_id: str,
        system_id: str,
        character_id: int,
        changes: dict[str, Any],
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
        # Only when stats are sent: stats saved under an older sheet stay editable
        # elsewhere and are fixed on their next stats edit (ADR-0030 NEG-002).
        if "stats" in changes:
            sheet = self._sheets.get(system_id)
            if sheet is not None:
                validate_stats(sheet, character.stats)
        self._repo.update(character)
        return character_view(character)
