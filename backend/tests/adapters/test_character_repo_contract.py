"""One suite, every CharacterRepo. The SQL repo must order and page exactly as the
in-memory one, or a cursor from one page would skip or repeat rows."""

import pytest
from app.domain.cast import Character, PlayerProfile, Relationship
from app.domain.shared import NotFound
from app.ports.repositories import CharacterRepo


def _add(repo: CharacterRepo, name: str, campaign_id: str = "ashfall", **fields):
    character = Character(
        id=repo.next_character_id(),
        campaign_id=campaign_id,
        name=name,
        is_player=fields.pop("is_player", False),
        relationship=fields.pop("relationship", Relationship.NEUTRAL),
        **fields,
    )
    repo.add(character)
    return character


def _page(repo: CharacterRepo, **query) -> list[str]:
    defaults = {
        "is_player": None,
        "relationship": None,
        "name_contains": None,
        "after": None,
        "limit": 50,
    }
    return [c.name for c in repo.page("ashfall", **defaults | query)]


def test_every_field_round_trips(character_repo: CharacterRepo) -> None:
    added = _add(
        character_repo,
        "Brother Cael",
        is_player=True,
        relationship=Relationship.ALLY,
        role="Human Cleric",
        level=5,
        location="The Party",
        disposition="Steadfast",
        last_seen="Session 13",
        stats={"abilities": {"STR": 14}, "skills": [{"name": "Medicine"}]},
        tags=("Healer", "Faith"),
        quote="The Light does not ask.",
        notes="Do not reveal before Session 15",
        portrait_key="f" * 32,
        player_profile=PlayerProfile(player_name="Jordan Kim", xp="6,500"),
    )

    assert character_repo.get("ashfall", added.id) == added


def test_a_wrong_campaign_reads_as_missing(character_repo: CharacterRepo) -> None:
    added = _add(character_repo, "Ansel")

    assert character_repo.get("other", added.id) is None
    assert character_repo.remove("other", added.id) is None
    with pytest.raises(NotFound):
        character_repo.update(Character(**vars(added) | {"campaign_id": "other"}))
    assert character_repo.get("ashfall", added.id) == added
    assert (
        character_repo.page(
            "other",
            is_player=None,
            relationship=None,
            name_contains=None,
            after=None,
            limit=50,
        )
        == []
    )


def test_update_persists_and_remove_returns_the_row(
    character_repo: CharacterRepo,
) -> None:
    added = _add(character_repo, "Ansel")
    changed = Character(**vars(added) | {"role": "Abbess", "tags": ("Faith",)})

    character_repo.update(changed)
    assert character_repo.get("ashfall", added.id) == changed

    assert character_repo.remove("ashfall", added.id) == changed
    assert character_repo.get("ashfall", added.id) is None


def test_order_is_lowercase_name_then_id(character_repo: CharacterRepo) -> None:
    for name in ["bo", "Ann", "ann", "Cy", "Ábel"]:
        _add(character_repo, name)

    # Code-point order: "á" sorts after every ASCII letter, as Python compares.
    assert _page(character_repo) == ["Ann", "ann", "bo", "Cy", "Ábel"]


def test_paging_crosses_a_tie_at_the_page_edge(character_repo: CharacterRepo) -> None:
    for name in ["Cy", "bo", "Al", "Bo", "dee"]:
        _add(character_repo, name)

    seen: list[str] = []
    after = None
    while True:
        page = character_repo.page(
            "ashfall",
            is_player=None,
            relationship=None,
            name_contains=None,
            after=after,
            limit=2,
        )
        if not page:
            break
        seen += [c.name for c in page]
        after = page[-1].sort_key

    assert seen == ["Al", "bo", "Bo", "Cy", "dee"]


def test_filters_alone_and_combined(character_repo: CharacterRepo) -> None:
    _add(character_repo, "Cael", is_player=True, relationship=Relationship.ALLY)
    _add(character_repo, "Ansel", relationship=Relationship.ALLY)
    _add(character_repo, "Vex", relationship=Relationship.ENEMY)
    _add(character_repo, "Cast Away", campaign_id="other")

    assert _page(character_repo, is_player=True) == ["Cael"]
    assert _page(character_repo, is_player=False) == ["Ansel", "Vex"]
    assert _page(character_repo, relationship=Relationship.ALLY) == ["Ansel", "Cael"]
    assert _page(character_repo, is_player=False, relationship=Relationship.ALLY) == [
        "Ansel"
    ]
    assert _page(character_repo, name_contains="AE") == ["Cael"]


def test_name_search_treats_wildcards_as_text(character_repo: CharacterRepo) -> None:
    _add(character_repo, "100% Loyal")
    _add(character_repo, "Ansel")
    _add(character_repo, "snake_eyes")

    assert _page(character_repo, name_contains="%") == ["100% Loyal"]
    assert _page(character_repo, name_contains="_") == ["snake_eyes"]
