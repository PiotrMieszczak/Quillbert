from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload, sessionmaker

from app.adapters.persistence.sqlalchemy import mappers
from app.adapters.persistence.sqlalchemy.tables import CampaignRow, SystemRow
from app.domain.campaigns import Campaign, System
from app.domain.shared import NotFound


class SqlCampaignRepo:
    """CampaignRepo over PostgreSQL. Every campaign query filters on owner_id."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def systems(self) -> list[System]:
        with self._sessions() as session:
            rows = session.scalars(select(SystemRow).order_by(SystemRow.name))
            return [System(row.id, row.name) for row in rows]

    def add(self, campaign: Campaign) -> None:
        with self._sessions.begin() as session:
            session.add(mappers.campaign_to_row(campaign))

    def get(self, owner_id: str, campaign_id: str) -> Campaign | None:
        query = (
            select(CampaignRow)
            .options(joinedload(CampaignRow.system))
            .where(CampaignRow.id == campaign_id, CampaignRow.owner_id == owner_id)
        )
        with self._sessions() as session:
            row = session.scalars(query).one_or_none()
            return None if row is None else mappers.campaign_from_row(row)

    def list_for_owner(self, owner_id: str) -> list[Campaign]:
        query = (
            select(CampaignRow)
            .options(joinedload(CampaignRow.system))
            .where(CampaignRow.owner_id == owner_id)
            .order_by(
                CampaignRow.last_played_at.desc().nulls_last(),
                CampaignRow.created_at.desc(),
            )
        )
        with self._sessions() as session:
            return [mappers.campaign_from_row(row) for row in session.scalars(query)]

    def set_image(
        self, owner_id: str, campaign_id: str, image_key: str | None
    ) -> str | None:
        owned = (CampaignRow.id == campaign_id, CampaignRow.owner_id == owner_id)
        with self._sessions.begin() as session:
            previous = session.execute(
                select(CampaignRow.image_path).where(*owned).with_for_update()
            ).one_or_none()
            if previous is None:
                raise NotFound("campaign not found")
            session.execute(
                update(CampaignRow).where(*owned).values(image_path=image_key)
            )
            return previous[0]
