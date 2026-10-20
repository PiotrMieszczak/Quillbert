from app.application.dto import CampaignView
from app.domain.campaigns import Campaign


def campaign_view(campaign: Campaign) -> CampaignView:
    return CampaignView(
        id=campaign.id,
        name=campaign.name,
        system=campaign.system,
        tint=campaign.tint,
        image_version=None if campaign.image_key is None else campaign.image_key[:8],
        # shortcut: no session table yet, so always 0; count sessions once they exist.
        session_count=0,
        last_played_at=campaign.last_played_at,
    )
