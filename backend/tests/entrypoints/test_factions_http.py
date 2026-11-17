import pytest
from fastapi.testclient import TestClient

# The app, gm and rival fixtures are the character suite's.
from tests.entrypoints.test_characters_http import app, gm, rival  # noqa: F401


@pytest.fixture
def url(gm: TestClient) -> str:  # noqa: F811
    response = gm.post(
        "/api/v1/campaigns", json={"name": "Ashfall", "systemId": "dnd-2024"}
    )
    return f"/api/v1/campaigns/{response.json()['id']}/factions"


def _create(client: TestClient, url: str, **body) -> dict:
    response = client.post(url, json={"name": "The Pale Court"} | body)
    assert response.status_code == 201, response.text
    return response.json()


def test_a_faction_needs_only_a_name(gm: TestClient, url: str) -> None:  # noqa: F811
    created = _create(gm, url, name="  The Pale Court ", motto=" ")
    assert created == {
        "id": created["id"],
        "name": "The Pale Court",
        "relationship": "neutral",
        "type": None,
        "influence": None,
        "reach": None,
        "motto": None,
        "goal": None,
        "notes": None,
    }
    assert gm.get(f"{url}/{created['id']}").json() == created


def test_a_blank_name_is_refused(gm: TestClient, url: str) -> None:  # noqa: F811
    assert gm.post(url, json={"name": "  "}).status_code == 400
    assert (
        gm.post(url, json={"name": "x", "relationship": "nemesis"}).status_code == 422
    )
    assert gm.get(url).json() == []


def test_the_list_is_by_name_ignoring_case(gm: TestClient, url: str) -> None:  # noqa: F811
    for name in ("zhent", "Ash", "ash"):
        _create(gm, url, name=name)
    assert [f["name"] for f in gm.get(url).json()] == ["Ash", "ash", "zhent"]


def test_patch_changes_only_what_is_sent(gm: TestClient, url: str) -> None:  # noqa: F811
    one = f"{url}/{_create(gm, url, type='Cabal', motto='We wait.')['id']}"
    patched = gm.patch(one, json={"relationship": "enemy", "motto": None})
    assert patched.status_code == 200, patched.text
    assert patched.json() | {"id": 0} == {
        "id": 0,
        "name": "The Pale Court",
        "relationship": "enemy",
        "type": "Cabal",
        "influence": None,
        "reach": None,
        "motto": None,
        "goal": None,
        "notes": None,
    }
    for body in ({"name": None}, {"relationship": None}, {"name": " "}):
        assert gm.patch(one, json=body).status_code == 400
    assert gm.get(one).json()["name"] == "The Pale Court"


def test_delete_removes_the_faction(gm: TestClient, url: str) -> None:  # noqa: F811
    one = f"{url}/{_create(gm, url)['id']}"
    assert gm.delete(one).status_code == 204
    assert gm.get(one).status_code == 404
    assert gm.delete(one).status_code == 404
    assert gm.get(url).json() == []


def test_a_faction_is_reachable_only_through_its_own_campaign(
    gm: TestClient,  # noqa: F811
    rival: TestClient,  # noqa: F811
    url: str,
) -> None:
    faction_id = _create(gm, url)["id"]
    other = gm.post("/api/v1/campaigns", json={"name": "Other", "systemId": "dnd-2024"})
    wrong = f"/api/v1/campaigns/{other.json()['id']}/factions/{faction_id}"
    for path in (wrong, f"{url}/999"):
        assert gm.get(path).status_code == 404
        assert gm.patch(path, json={"name": "x"}).status_code == 404
        assert gm.delete(path).status_code == 404
    # Another GM gets 404 on everything under the campaign.
    one = f"{url}/{faction_id}"
    assert rival.get(url).status_code == 404
    assert rival.post(url, json={"name": "x"}).status_code == 404
    assert rival.get(one).status_code == 404
    assert rival.patch(one, json={"name": "x"}).status_code == 404
    assert rival.delete(one).status_code == 404
    assert gm.get(one).json()["name"] == "The Pale Court"
