import dataclasses

from app.domain.cast import Faction
from app.domain.shared import NotFound


class InMemoryFactionRepo:
    def __init__(self) -> None:
        self._factions: dict[int, Faction] = {}
        self._next_id = 1

    def next_faction_id(self) -> int:
        ident = self._next_id
        self._next_id += 1
        return ident

    def add(self, faction: Faction) -> None:
        self._factions[faction.id] = dataclasses.replace(faction)

    def get(self, campaign_id: str, faction_id: int) -> Faction | None:
        faction = self._factions.get(faction_id)
        if faction is None or faction.campaign_id != campaign_id:
            return None
        return dataclasses.replace(faction)

    def update(self, faction: Faction) -> None:
        if self.get(faction.campaign_id, faction.id) is None:
            raise NotFound("faction not found")
        self._factions[faction.id] = dataclasses.replace(faction)

    def remove(self, campaign_id: str, faction_id: int) -> Faction | None:
        faction = self.get(campaign_id, faction_id)
        if faction is not None:
            del self._factions[faction_id]
        return faction

    def list(self, campaign_id: str) -> list[Faction]:
        mine = [f for f in self._factions.values() if f.campaign_id == campaign_id]
        return [dataclasses.replace(f) for f in sorted(mine, key=lambda f: f.sort_key)]
