"""Faction use cases. A faction has no shape of its own to hide, so these return the
entity itself, not a view."""

import dataclasses
from typing import Any

from app.domain.cast import Faction, Relationship, clean_faction
from app.domain.shared import NotFound, ValidationFailed
from app.ports.repositories import FactionRepo

# Fields a faction always has: sending null for one is an error, not a clear.
REQUIRED = {"name", "relationship"}
EDITABLE = REQUIRED | {"type", "influence", "reach", "motto", "goal", "notes"}


class CreateFaction:
    def __init__(self, repo: FactionRepo) -> None:
        self._repo = repo

    def execute(
        self, *, campaign_id: str, name: str, relationship: Relationship, **text: Any
    ) -> Faction:
        faction = clean_faction(
            Faction(
                id=0,
                campaign_id=campaign_id,
                name=name,
                relationship=relationship,
                **text,
            )
        )
        # The id is taken only once the faction is valid, so a rejected one uses none.
        faction.id = self._repo.next_faction_id()
        self._repo.add(faction)
        return faction


class ListFactions:
    def __init__(self, repo: FactionRepo) -> None:
        self._repo = repo

    def execute(self, *, campaign_id: str) -> list[Faction]:
        return self._repo.list(campaign_id)


class GetFaction:
    def __init__(self, repo: FactionRepo) -> None:
        self._repo = repo

    def execute(self, *, campaign_id: str, faction_id: int) -> Faction:
        faction = self._repo.get(campaign_id, faction_id)
        if faction is None:
            raise NotFound("faction not found")
        return faction


class UpdateFaction:
    """Changes only the fields given; a field given as None is cleared."""

    def __init__(self, repo: FactionRepo) -> None:
        self._repo = repo

    def execute(
        self, *, campaign_id: str, faction_id: int, changes: dict[str, Any]
    ) -> Faction:
        unknown = changes.keys() - EDITABLE
        if unknown:
            raise ValidationFailed(f"cannot change {', '.join(sorted(unknown))}")
        cleared = sorted(k for k in REQUIRED & changes.keys() if changes[k] is None)
        if cleared:
            raise ValidationFailed(f"{', '.join(cleared)} cannot be cleared")
        current = self._repo.get(campaign_id, faction_id)
        if current is None:
            raise NotFound("faction not found")
        faction = clean_faction(dataclasses.replace(current, **changes))
        self._repo.update(faction)
        return faction


class DeleteFaction:
    def __init__(self, repo: FactionRepo) -> None:
        self._repo = repo

    def execute(self, *, campaign_id: str, faction_id: int) -> None:
        if self._repo.remove(campaign_id, faction_id) is None:
            raise NotFound("faction not found")
