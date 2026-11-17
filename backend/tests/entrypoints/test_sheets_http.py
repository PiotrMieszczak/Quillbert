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

SHEET = {
    "sections": [
        {
            "key": "abilities",
            "label": "Abilities",
            "fields": [
                {"key": "STR", "label": "Strength", "type": "int", "min": 1, "max": 30}
            ],
        }
    ],
    "sources": [{"documentId": "5dfa", "headingPath": ["Rules", "Abilities"]}],
}
PUT = "/api/v1/admin/sheets/dnd-2024"
GET = "/api/v1/systems/dnd-2024/sheet"


class GmAndAdmin:
    def verify(self, token: str) -> Identity:
        if token not in ("gm-token", "admin-token"):
            raise InvalidToken("nope")
        return Identity(user_id=token, email=None, is_admin=token == "admin-token")


@pytest.fixture
def app(tmp_path: Path):
    return build_app(
        build_use_cases(
            repo=InMemoryConversationRepo(),
            documents=InMemoryDocumentRepo(),
            campaigns=InMemoryCampaignRepo(),
            characters=InMemoryCharacterRepo(),
            files=LocalDiskFileStore(tmp_path / "files"),
            verifier=GmAndAdmin(),
        )
    )


@pytest.fixture
def gm(app) -> TestClient:
    return TestClient(app, headers={"Authorization": "Bearer gm-token"})


@pytest.fixture
def admin(app) -> TestClient:
    return TestClient(app, headers={"Authorization": "Bearer admin-token"})


@pytest.fixture
def characters(gm: TestClient) -> str:
    response = gm.post(
        "/api/v1/campaigns", json={"name": "Ashfall", "systemId": "dnd-2024"}
    )
    return f"/api/v1/campaigns/{response.json()['id']}/characters"


def test_a_system_without_a_sheet_answers_404(gm: TestClient) -> None:
    assert gm.get(GET).status_code == 404


def test_a_gm_cannot_save_a_sheet(gm: TestClient) -> None:
    assert gm.put(PUT, json=SHEET).status_code == 403
    assert gm.get(GET).status_code == 404


def test_an_admin_saves_a_sheet_every_gm_can_read(
    admin: TestClient, gm: TestClient
) -> None:
    assert admin.put(PUT, json=SHEET).status_code == 200
    # Nulls are left out, and the wire is camelCase.
    assert gm.get(GET).json() == {"systemId": "dnd-2024"} | SHEET


def test_a_malformed_sheet_or_unknown_system_is_refused(admin: TestClient) -> None:
    assert admin.put(PUT, json={"sections": []}).status_code == 422
    assert admin.put("/api/v1/admin/sheets/nope", json=SHEET).status_code == 404


def test_without_a_sheet_stats_are_free(gm: TestClient, characters: str) -> None:
    body = {"name": "Mother Ansel", "stats": {"anything": {"goes": "here"}}}
    assert gm.post(characters, json=body).status_code == 201


def test_a_saved_sheet_checks_stats_on_create_and_update(
    admin: TestClient, gm: TestClient, characters: str
) -> None:
    admin.put(PUT, json=SHEET)

    for stats in ({"abilities": {"STR": 31}}, {"abilities": {"WIS": 17}}):
        refused = gm.post(characters, json={"name": "Ansel", "stats": stats})
        assert refused.status_code == 422, refused.text
    assert gm.get(characters).json()["items"] == []

    created = gm.post(
        characters, json={"name": "Ansel", "stats": {"abilities": {"STR": 14}}}
    )
    assert created.status_code == 201, created.text
    one = f"{characters}/{created.json()['id']}"
    assert gm.patch(one, json={"stats": {"abilities": {"STR": 0}}}).status_code == 422
    assert gm.get(one).json()["stats"] == {"abilities": {"STR": 14}}


def test_a_stricter_sheet_does_not_block_other_edits(
    admin: TestClient, gm: TestClient, characters: str
) -> None:
    """ADR-0030 NEG-002: stats saved before the sheet stay until their next edit."""
    created = gm.post(characters, json={"name": "Ansel", "stats": {"old": {"x": 1}}})
    admin.put(PUT, json=SHEET)
    one = f"{characters}/{created.json()['id']}"
    assert gm.patch(one, json={"role": "Abbess"}).status_code == 200
