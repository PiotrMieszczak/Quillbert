"""One suite, every CampaignRepo. Ownership is enforced in the repository (DEC-005)."""

from datetime import UTC, date, datetime

import pytest
from app.domain.campaigns import Campaign, System
from app.domain.shared import NotFound
from app.ports.repositories import CampaignRepo

T0 = datetime(2026, 10, 20, 12, 0, tzinfo=UTC)
DND_2014 = System("dnd-2014", "D&D 2014")


def _campaign(cid: str, owner_id: str = "gm", **fields) -> Campaign:
    values = {
        "name": cid.title(),
        "system": DND_2014,
        "tint": "#EF7777",
        "created_at": T0,
    }
    return Campaign(id=cid, owner_id=owner_id, **values | fields)


def test_systems_are_listed_by_name(campaign_repo: CampaignRepo) -> None:
    assert [s.name for s in campaign_repo.systems()] == [
        "D&D 2014",
        "D&D 2024",
        "Traveller 2e",
    ]


def test_added_campaign_reads_back(campaign_repo: CampaignRepo) -> None:
    added = _campaign("ashfall")
    campaign_repo.add(added)
    assert campaign_repo.get("gm", "ashfall") == added


def test_another_owner_sees_nothing(campaign_repo: CampaignRepo) -> None:
    campaign_repo.add(_campaign("ashfall", owner_id="gm"))

    assert campaign_repo.get("rival", "ashfall") is None
    assert campaign_repo.list_for_owner("rival") == []
    with pytest.raises(NotFound):
        campaign_repo.set_image("rival", "ashfall", "f" * 32)
    assert campaign_repo.get("gm", "ashfall").image_key is None


def test_list_is_recently_played_first_then_newest(
    campaign_repo: CampaignRepo,
) -> None:
    campaign_repo.add(_campaign("old"))
    campaign_repo.add(_campaign("new", created_at=T0.replace(hour=13)))
    campaign_repo.add(_campaign("played", last_played_at=date(2026, 7, 5)))

    assert [c.id for c in campaign_repo.list_for_owner("gm")] == [
        "played",
        "new",
        "old",
    ]


def test_set_image_returns_the_previous_key(campaign_repo: CampaignRepo) -> None:
    campaign_repo.add(_campaign("ashfall"))

    assert campaign_repo.set_image("gm", "ashfall", "a" * 32) is None
    assert campaign_repo.set_image("gm", "ashfall", "b" * 32) == "a" * 32
    assert campaign_repo.get("gm", "ashfall").image_key == "b" * 32
