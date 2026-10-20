from pathlib import Path

import pytest
from app.adapters.files import LocalDiskFileStore
from app.adapters.persistence.memory.campaigns import InMemoryCampaignRepo
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.composition import build_app, build_use_cases
from app.ports.auth import Identity, InvalidToken
from fastapi.testclient import TestClient

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
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


def _create(client: TestClient, **body) -> dict:
    payload = {"name": "Ashfall Reach", "systemId": "dnd-2014", "tint": "#EF7777"}
    response = client.post("/api/v1/campaigns", json=payload | body)
    assert response.status_code == 201, response.text
    return response.json()


def test_systems_include_dnd_2014(gm: TestClient) -> None:
    names = {s["id"]: s["name"] for s in gm.get("/api/v1/systems").json()}
    assert names == {
        "dnd-2014": "D&D 2014",
        "dnd-2024": "D&D 2024",
        "traveller-2e": "Traveller 2e",
    }


def test_create_then_list(gm: TestClient) -> None:
    assert gm.get("/api/v1/campaigns").json() == []

    created = _create(gm, name="  Ashfall   Reach ")

    assert created == {
        "id": created["id"],
        "name": "Ashfall Reach",
        "system": {"id": "dnd-2014", "name": "D&D 2014"},
        "tint": "#EF7777",
        "imageUrl": None,
        "sessionCount": 0,
        "lastPlayedAt": None,
    }
    assert gm.get("/api/v1/campaigns").json() == [created]
    assert gm.get(f"/api/v1/campaigns/{created['id']}").json() == created


def test_a_campaign_without_a_system_is_rejected(gm: TestClient) -> None:
    missing = gm.post("/api/v1/campaigns", json={"name": "No System"})
    unknown = gm.post(
        "/api/v1/campaigns", json={"name": "No System", "systemId": "mothership"}
    )

    assert missing.status_code == 422
    assert unknown.status_code == 422
    assert unknown.json() == {"detail": "unknown system 'mothership'"}
    assert gm.get("/api/v1/campaigns").json() == []


@pytest.mark.parametrize(
    "body", [{"name": "   "}, {"tint": "red;background:url(x)"}, {"name": "x" * 121}]
)
def test_invalid_name_or_tint_is_400(gm: TestClient, body: dict) -> None:
    payload = {"name": "Ashfall", "systemId": "dnd-2024"} | body
    assert gm.post("/api/v1/campaigns", json=payload).status_code == 400


def test_owners_are_isolated(gm: TestClient, rival: TestClient) -> None:
    mine = _create(gm)
    url = f"/api/v1/campaigns/{mine['id']}"

    assert rival.get("/api/v1/campaigns").json() == []
    assert rival.get(url).status_code == 404
    image = rival.post(f"{url}/image", files={"file": ("b.png", PNG, "image/png")})
    assert image.status_code == 404
    # Routes nested under the campaign are gated by ownership too.
    assert rival.get(f"{url}/documents").status_code == 404
    assert rival.post(f"{url}/conversations", json={}).status_code == 404
    assert gm.get(f"{url}/documents").json() == []


def test_unauthenticated_is_401(app) -> None:
    assert TestClient(app).get("/api/v1/campaigns").status_code == 401


def test_banner_upload_sets_the_image_url(gm: TestClient, tmp_path: Path) -> None:
    campaign = _create(gm)
    url = f"/api/v1/campaigns/{campaign['id']}/image"

    first = gm.post(url, files={"file": ("banner.png", PNG, "image/png")})
    assert first.status_code == 200
    image_url = first.json()["imageUrl"]
    assert image_url.startswith(f"{url}?v=")

    served = gm.get(image_url)
    assert served.status_code == 200
    assert served.headers["content-type"] == "image/png"
    assert served.content == PNG

    # Replacing the banner removes the old file and changes the URL.
    second = gm.post(url, files={"file": ("b.png", PNG + b"2", "image/png")})
    assert second.json()["imageUrl"] != image_url
    stored = [p for p in (tmp_path / "files").rglob("*") if p.is_file()]
    assert len(stored) == 1


def test_a_banner_that_is_not_an_image_is_415(gm: TestClient) -> None:
    campaign = _create(gm)
    response = gm.post(
        f"/api/v1/campaigns/{campaign['id']}/image",
        files={"file": ("banner.png", b"%PDF-1.7", "image/png")},
    )
    assert response.status_code == 415
    assert gm.get(f"/api/v1/campaigns/{campaign['id']}/image").status_code == 404
