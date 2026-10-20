import uuid

from app.application.campaigns.views import campaign_view
from app.application.dto import CampaignView
from app.domain.campaigns import (
    DEFAULT_TINT,
    Campaign,
    UnknownSystem,
    check_tint,
    clean_name,
)
from app.ports.clock import Clock
from app.ports.repositories import CampaignRepo


class CreateCampaign:
    def __init__(self, repo: CampaignRepo, clock: Clock) -> None:
        self._repo = repo
        self._clock = clock

    def execute(
        self, *, owner_id: str, name: str, system_id: str, tint: str | None = None
    ) -> CampaignView:
        system = next((s for s in self._repo.systems() if s.id == system_id), None)
        if system is None:
            raise UnknownSystem(f"unknown system {system_id!r}")
        campaign = Campaign(
            # Random, not a slug of the name: ids appear in every nested URL.
            id=uuid.uuid4().hex,
            owner_id=owner_id,
            name=clean_name(name),
            system=system,
            tint=check_tint(tint or DEFAULT_TINT),
            created_at=self._clock.now(),
        )
        self._repo.add(campaign)
        return campaign_view(campaign)
