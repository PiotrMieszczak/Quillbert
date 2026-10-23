import logging

from app.adapters.library.arkon import ArkonUnavailable
from app.ports.search import ChunkSearch, Hit

logger = logging.getLogger(__name__)


class CampaignAndLibrarySearch:
    """Campaign hits plus up to `library_k` shared-library hits (ADR-0027).

    A fixed quota, not merged scores: the two rankings are not comparable. Library
    hits fill the tail of the k slots. Arkon being down costs the library hits only.
    """

    def __init__(
        self, campaign: ChunkSearch, library: ChunkSearch, *, library_k: int
    ) -> None:
        self._campaign = campaign
        self._library = library
        self._library_k = library_k

    def search(
        self,
        campaign_id: str,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        own = self._campaign.search(campaign_id, system_id, text, vector, k)
        try:
            shared = self._library.search(
                campaign_id, system_id, text, vector, min(self._library_k, k)
            )
        except ArkonUnavailable:
            logger.warning(
                "shared library unavailable; campaign hits only", exc_info=True
            )
            shared = []
        return own[: k - len(shared)] + shared
