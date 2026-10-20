from app.application.campaigns.views import campaign_view
from app.application.dto import CampaignView
from app.domain.shared import NotFound
from app.ports.repositories import CampaignRepo


class GetCampaign:
    """The caller's campaign, or NotFound. Also the ownership gate for every route
    nested under a campaign (DEC-005)."""

    def __init__(self, repo: CampaignRepo) -> None:
        self._repo = repo

    def execute(self, *, owner_id: str, campaign_id: str) -> CampaignView:
        campaign = self._repo.get(owner_id, campaign_id)
        if campaign is None:
            raise NotFound("campaign not found")
        return campaign_view(campaign)
