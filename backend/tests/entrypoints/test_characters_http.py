from pathlib import Path

import pytest
from app.adapters.files import LocalDiskFileStore
from app.adapters.persistence.memory.campaigns import InMemoryCampaignRepo
from app.adapters.persistence.memory.characters import InMemoryCharacterRepo
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.composition import build_app, build_use_cases
from app.ports.auth import Identity, InvalidToken
from fastapi.testclient import TestClient

TOKENS = {"gm-token": "gm", "rival-token": "rival"}


class TwoUsers:
    def verify(self, token: str) -> Identity:
        if token not in TOKENS:
            raise InvalidToken("nope")
        return Identity(user_id=TOKENS[token], email=None)


@pytest.fixture
def app(tmp_path: Path):
    use_cases = build_use_cases(
        repo=InMemoryConversationRepo(),
        documents=InMemoryDocumentRepo(),
        campaigns=InMemoryCampaignRepo(),
        characters=InMemoryCharacterRepo(),
        files=LocalDiskFileStore(tmp_path / "files"),
        verifier=TwoUsers(),
    )
    return build_app(use_cases)


@pytest.fixture
def gm(app) -> TestClient:
    return TestClient(app, headers={"Authorization": "Bearer gm-token"})


@pytest.fixture
def rival(app) -> TestClient:
    return TestClient(app, headers={"Authorization": "Bearer rival-token"})


@pytest.fixture
def url(gm: TestClient) -> str:
    response = gm.post(
        "/api/v1/campaigns", json={"name": "Ashfall", "systemId": "dnd-2024"}
    )
    assert response.status_code == 201, response.text
    return f"/api/v1/campaigns/{response.json()['id']}/characters"


def _create(client: TestClient, url: str, **body) -> dict:
    response = client.post(url, json={"name": "Mother Ansel"} | body)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_returns_the_detail_with_text_cleaned(gm: TestClient, url: str) -> None:
    created = _create(
        gm,
        url,
        name="  Brother   Cael ",
        isPlayer=True,
        relationship="ally",
        role=" Human Cleric ",
        level=5,
        stats={"abilities": {"STR": 14}},
        tags=["Healer", " Healer ", "Faith"],
        notes="",
        playerProfile={"playerName": "Jordan Kim", "class": "Cleric (Light)"},
    )

    assert created == {
        "id": created["id"],
        "name": "Brother Cael",
        "isPlayer": True,
        "relationship": "ally",
        "role": "Human Cleric",
        "level": 5,
        "location": None,
        "tags": ["Healer", "Faith"],
        "portraitUrl": None,
        "playerProfile": {
            "playerName": "Jordan Kim",
            "class": "Cleric (Light)",
            "race": None,
            "background": None,
            "xp": None,
            "pronouns": None,
            "bonds": None,
        },
        "disposition": None,
        "lastSeen": None,
        "stats": {"abilities": {"STR": 14}},
        "quote": None,
        "notes": None,
    }


def test_an_npc_defaults_to_neutral_and_has_no_profile(
    gm: TestClient, url: str
) -> None:
    npc = _create(gm, url)

    assert npc["isPlayer"] is False
    assert npc["relationship"] == "neutral"
    assert npc["playerProfile"] is None


def test_a_player_always_gets_a_profile(gm: TestClient, url: str) -> None:
    assert _create(gm, url, isPlayer=True)["playerProfile"]["playerName"] is None


@pytest.mark.parametrize(
    "body",
    [
        {"name": "   "},
        {"name": "x" * 121},
        {"level": -1},
        {"tags": ["x" * 41]},
        {"tags": [f"t{i}" for i in range(21)]},
        {"stats": {"blob": "x" * 20_001}},
        {"playerProfile": {"playerName": "Jordan"}},
    ],
)
def test_invalid_character_is_400(gm: TestClient, url: str, body: dict) -> None:
    response = gm.post(url, json={"name": "Ansel"} | body)

    assert response.status_code == 400, response.text
    assert gm.get(url).json()["items"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {"role": "Cleric"},
        {"name": "Ansel", "relationship": "frenemy"},
        {"name": "Ansel", "role": "x" * 121},
    ],
)
def test_malformed_body_is_422(gm: TestClient, url: str, payload: dict) -> None:
    assert gm.post(url, json=payload).status_code == 422


def test_list_is_slim_and_sorted_by_name(gm: TestClient, url: str) -> None:
    _create(gm, url, name="zed", notes="secret", stats={"STR": 7})
    _create(gm, url, name="Ansel")
    _create(gm, url, name="borin")

    page = gm.get(url).json()

    assert [c["name"] for c in page["items"]] == ["Ansel", "borin", "zed"]
    assert page["nextCursor"] is None
    assert not {"notes", "stats", "quote"} & page["items"][2].keys()


def test_list_filters(gm: TestClient, url: str) -> None:
    _create(gm, url, name="Cael", isPlayer=True, relationship="ally")
    _create(gm, url, name="Ansel", relationship="ally")
    _create(gm, url, name="Vex", relationship="enemy")

    def names(**params) -> list[str]:
        return [c["name"] for c in gm.get(url, params=params).json()["items"]]

    assert names(isPlayer="true") == ["Cael"]
    assert names(isPlayer="false") == ["Ansel", "Vex"]
    assert names(isPlayer="false", relationship="ally") == ["Ansel"]
    assert names(q="  AN ") == ["Ansel"]
    assert gm.get(url, params={"relationship": "frenemy"}).status_code == 422


def test_cursor_pages_through_everyone_once(gm: TestClient, url: str) -> None:
    # "bo" ends page one and "Bo" starts page two: only the id tells them apart.
    for name in ["Cy", "bo", "Al", "Bo", "dee"]:
        _create(gm, url, name=name)

    seen: list[str] = []
    cursor = None
    while True:
        params = {"limit": 2} | ({"cursor": cursor} if cursor else {})
        page = gm.get(url, params=params).json()
        seen += [c["name"] for c in page["items"]]
        cursor = page["nextCursor"]
        if cursor is None:
            break

    assert seen == ["Al", "bo", "Bo", "Cy", "dee"]


@pytest.mark.parametrize("cursor", ["not-base64!", "WzFd", "eyJhIjoxfQ=="])
def test_a_bad_cursor_is_400(gm: TestClient, url: str, cursor: str) -> None:
    assert gm.get(url, params={"cursor": cursor}).status_code == 400


@pytest.mark.parametrize("limit", [0, 201])
def test_limit_is_bounded(gm: TestClient, url: str, limit: int) -> None:
    assert gm.get(url, params={"limit": limit}).status_code == 422


def test_another_gms_campaign_reads_as_missing(
    gm: TestClient, rival: TestClient, url: str
) -> None:
    _create(gm, url)

    assert rival.get(url).status_code == 404
    assert rival.post(url, json={"name": "Spy"}).status_code == 404
    assert [c["name"] for c in gm.get(url).json()["items"]] == ["Mother Ansel"]


def test_characters_stay_in_their_campaign(gm: TestClient, url: str) -> None:
    _create(gm, url)
    other = gm.post(
        "/api/v1/campaigns", json={"name": "Drinax", "systemId": "traveller-2e"}
    )
    other_url = f"/api/v1/campaigns/{other.json()['id']}/characters"

    assert gm.get(other_url).json()["items"] == []


# --- one character: get, update, delete (#140, #141) ----------------------------


def test_get_returns_what_create_returned(gm: TestClient, url: str) -> None:
    created = _create(gm, url, notes="Secretly the Pale Court", stats={"STR": 7})

    response = gm.get(f"{url}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_delete_removes_it(gm: TestClient, url: str) -> None:
    created = _create(gm, url)
    one = f"{url}/{created['id']}"

    assert gm.delete(one).status_code == 204
    assert gm.get(one).status_code == 404
    assert gm.get(url).json()["items"] == []
    assert gm.delete(one).status_code == 404


def test_an_id_from_another_campaign_is_404(gm: TestClient, url: str) -> None:
    created = _create(gm, url)
    other = gm.post(
        "/api/v1/campaigns", json={"name": "Drinax", "systemId": "dnd-2024"}
    )
    wrong = f"/api/v1/campaigns/{other.json()['id']}/characters/{created['id']}"

    assert gm.get(wrong).status_code == 404
    assert gm.patch(wrong, json={"role": "Spy"}).status_code == 404
    assert gm.delete(wrong).status_code == 404
    assert gm.get(f"{url}/{created['id']}").json() == created


def test_another_gm_cannot_reach_one_character(
    gm: TestClient, rival: TestClient, url: str
) -> None:
    one = f"{url}/{_create(gm, url)['id']}"

    assert rival.get(one).status_code == 404
    assert rival.patch(one, json={"name": "Spy"}).status_code == 404
    assert rival.delete(one).status_code == 404
    assert gm.get(one).status_code == 200


def test_a_non_numeric_id_is_422(gm: TestClient, url: str) -> None:
    assert gm.get(f"{url}/ansel").status_code == 422


def test_patch_changes_only_what_was_sent(gm: TestClient, url: str) -> None:
    created = _create(gm, url, role="Priestess", location="Temple", tags=["Faith"])

    response = gm.patch(f"{url}/{created['id']}", json={"location": " Market Row "})

    assert response.status_code == 200, response.text
    assert response.json() == created | {"location": "Market Row"}
    assert gm.get(f"{url}/{created['id']}").json() == response.json()


def test_patch_null_clears_a_field(gm: TestClient, url: str) -> None:
    created = _create(gm, url, role="Priestess", level=3)

    updated = gm.patch(f"{url}/{created['id']}", json={"role": None, "level": None})

    assert updated.json()["role"] is None
    assert updated.json()["level"] is None


@pytest.mark.parametrize("field", ["name", "isPlayer", "relationship", "stats", "tags"])
def test_patch_cannot_clear_a_required_field(
    gm: TestClient, url: str, field: str
) -> None:
    created = _create(gm, url)

    response = gm.patch(f"{url}/{created['id']}", json={field: None})

    assert response.status_code == 400, response.text
    assert gm.get(f"{url}/{created['id']}").json() == created


@pytest.mark.parametrize(
    "body",
    [
        {"name": "  "},
        {"level": 100},
        {"tags": ["x" * 41]},
        {"stats": {"blob": "x" * 20_001}},
        {"playerProfile": {"playerName": "Jordan"}},
    ],
)
def test_patch_validates_like_create(gm: TestClient, url: str, body: dict) -> None:
    created = _create(gm, url)

    assert gm.patch(f"{url}/{created['id']}", json=body).status_code == 400
    assert gm.get(f"{url}/{created['id']}").json() == created


def test_promoting_and_demoting_a_player(gm: TestClient, url: str) -> None:
    one = f"{url}/{_create(gm, url)['id']}"

    promoted = gm.patch(one, json={"isPlayer": True, "playerProfile": {"xp": "300"}})
    assert promoted.json()["playerProfile"]["xp"] == "300"

    demoted = gm.patch(one, json={"isPlayer": False})
    assert demoted.status_code == 200, demoted.text
    assert demoted.json()["playerProfile"] is None
