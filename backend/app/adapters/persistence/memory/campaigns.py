import dataclasses
from datetime import date, datetime

from app.domain.campaigns import Campaign, System
from app.domain.shared import NotFound

# What migrations 0002 and 0007 seed into the system table.
SYSTEMS = [
    System("dnd-2014", "D&D 2014"),
    System("dnd-2024", "D&D 2024"),
    System("traveller-2e", "Traveller 2e"),
]


class InMemoryCampaignRepo:
    def __init__(self, campaigns: list[Campaign] | None = None) -> None:
        self._campaigns = {c.id: c for c in campaigns or []}

    def systems(self) -> list[System]:
        return list(SYSTEMS)

    def add(self, campaign: Campaign) -> None:
        self._campaigns[campaign.id] = dataclasses.replace(campaign)

    def get(self, owner_id: str, campaign_id: str) -> Campaign | None:
        campaign = self._campaigns.get(campaign_id)
        if campaign is None or campaign.owner_id != owner_id:
            return None
        return dataclasses.replace(campaign)

    def list_for_owner(self, owner_id: str) -> list[Campaign]:
        mine = [c for c in self._campaigns.values() if c.owner_id == owner_id]
        # last_played_at DESC NULLS LAST, then created_at DESC — as the SQL repo.
        mine.sort(key=_recency, reverse=True)
        return [dataclasses.replace(c) for c in mine]

    def set_image(
        self, owner_id: str, campaign_id: str, image_key: str | None
    ) -> str | None:
        campaign = self._campaigns.get(campaign_id)
        if campaign is None or campaign.owner_id != owner_id:
            raise NotFound("campaign not found")
        previous, campaign.image_key = campaign.image_key, image_key
        return previous


def _recency(campaign: Campaign) -> tuple[bool, date, datetime]:
    played = campaign.last_played_at
    return (played is not None, played or date.min, campaign.created_at)
