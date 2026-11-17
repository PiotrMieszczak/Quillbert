import dataclasses

import pytest
from app.domain.cast import Faction, Relationship
from app.domain.shared import NotFound
from app.ports.repositories import FactionRepo


def _add(repo: FactionRepo, campaign_id: str = "ashfall", **fields) -> Faction:
    faction = Faction(
        id=repo.next_faction_id(),
        campaign_id=campaign_id,
        **{"name": "The Pale Court", "relationship": Relationship.ENEMY} | fields,
    )
    repo.add(faction)
    return faction


def test_a_faction_round_trips_every_field(faction_repo: FactionRepo) -> None:
    faction = _add(
        faction_repo,
        type="Hidden cabal",
        influence="High",
        reach="Old Quarter",
        motto="We keep the light.",
        goal="Unseat the council",
        notes="Do not reveal before Session 15",
    )
    assert faction_repo.get("ashfall", faction.id) == faction


def test_another_campaign_cannot_read_change_or_remove(
    faction_repo: FactionRepo,
) -> None:
    faction = _add(faction_repo)
    assert faction_repo.get("other", faction.id) is None
    assert faction_repo.remove("other", faction.id) is None
    with pytest.raises(NotFound):
        faction_repo.update(
            dataclasses.replace(faction, campaign_id="other", name="Stolen")
        )
    assert faction_repo.get("ashfall", faction.id) == faction


def test_list_is_by_name_ignoring_case_then_id_and_own_campaign_only(
    faction_repo: FactionRepo,
) -> None:
    _add(faction_repo, name="ash")
    _add(faction_repo, name="Zhent")
    _add(faction_repo, name="Ash")
    _add(faction_repo, "other", name="Aaa")
    assert [f.name for f in faction_repo.list("ashfall")] == ["ash", "Ash", "Zhent"]


def test_update_persists_and_remove_returns_the_faction(
    faction_repo: FactionRepo,
) -> None:
    faction = _add(faction_repo)
    changed = dataclasses.replace(
        faction, name="The Bright Court", relationship=Relationship.ALLY, motto=None
    )
    faction_repo.update(changed)
    assert faction_repo.get("ashfall", faction.id) == changed
    assert faction_repo.remove("ashfall", faction.id) == changed
    assert faction_repo.list("ashfall") == []
