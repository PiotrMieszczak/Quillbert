from app.application.campaigns.views import campaign_view
from app.application.dto import CampaignView
from app.domain.campaigns import System
from app.ports.repositories import CampaignRepo


class ListCampaigns:
    def __init__(self, repo: CampaignRepo) -> None:
        self._repo = repo

    def execute(self, *, owner_id: str) -> list[CampaignView]:
        return [campaign_view(c) for c in self._repo.list_for_owner(owner_id)]


class ListSystems:
    def __init__(self, repo: CampaignRepo) -> None:
        self._repo = repo

    def execute(self) -> list[System]:
        return self._repo.systems()
