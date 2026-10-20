from typing import BinaryIO

from app.application.campaigns.views import campaign_view
from app.application.dto import CampaignImage, CampaignView
from app.domain.campaigns import SNIFF_BYTES, image_type
from app.domain.shared import NotFound
from app.ports.files import FileStore
from app.ports.repositories import CampaignRepo


class SetCampaignImage:
    def __init__(self, files: FileStore, repo: CampaignRepo, *, max_bytes: int) -> None:
        self._files = files
        self._repo = repo
        self._max_bytes = max_bytes

    def execute(
        self, *, owner_id: str, campaign_id: str, content: BinaryIO
    ) -> CampaignView:
        if self._repo.get(owner_id, campaign_id) is None:
            raise NotFound("campaign not found")
        image_type(content.read(SNIFF_BYTES))
        content.seek(0)

        stored = self._files.put(content, max_bytes=self._max_bytes)
        try:
            previous = self._repo.set_image(owner_id, campaign_id, stored.key)
        except Exception:
            self._files.delete(stored.key)
            raise
        if previous is not None:
            self._files.delete(previous)
        campaign = self._repo.get(owner_id, campaign_id)
        if campaign is None:  # deleted between the two calls
            raise NotFound("campaign not found")
        return campaign_view(campaign)


class GetCampaignImage:
    def __init__(self, files: FileStore, repo: CampaignRepo) -> None:
        self._files = files
        self._repo = repo

    def execute(self, *, owner_id: str, campaign_id: str) -> CampaignImage:
        campaign = self._repo.get(owner_id, campaign_id)
        if campaign is None or campaign.image_key is None:
            raise NotFound("campaign image not found")
        data = self._files.read(campaign.image_key)
        return CampaignImage(data=data, media_type=image_type(data[:SNIFF_BYTES]))
