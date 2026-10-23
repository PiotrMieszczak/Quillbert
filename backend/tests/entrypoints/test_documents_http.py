from pathlib import Path

import pytest
from app.adapters.files import LocalDiskFileStore
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.composition import build_app, build_use_cases
from fastapi.testclient import TestClient
from tests.conftest import FakeVerifier, owned_campaigns

URL = "/api/v1/campaigns/ashfall/documents"
PDF = b"%PDF-1.7\nhello"


def _upload(
    client: TestClient, name: str = "Core Rulebook.pdf", data: bytes = PDF, url=URL
):
    return client.post(url, files={"file": (name, data, "application/octet-stream")})


def test_upload_returns_202_with_a_queued_document(client: TestClient) -> None:
    response = _upload(client)

    assert response.status_code == 202
    assert response.json() == {
        "id": 1,
        "filename": "Core Rulebook.pdf",
        "kind": "PDF",
        "pageCount": None,
        "meta": None,
        "status": "queued",
        "progress": 0,
        "error": None,
        "systems": [],
        "attribution": None,
    }


def test_uploading_the_same_bytes_again_returns_the_existing_document(
    client: TestClient,
) -> None:
    first = _upload(client)
    again = _upload(client, name="copy.pdf")

    assert again.status_code == 200
    assert again.json() == first.json()
    assert len(client.get(URL).json()) == 1


def test_the_list_and_single_endpoints_serve_the_upload(client: TestClient) -> None:
    created = _upload(client).json()

    assert client.get(URL).json() == [created]
    assert client.get(f"{URL}/{created['id']}").json() == created


def test_a_missing_document_is_404(client: TestClient) -> None:
    response = client.get(f"{URL}/99")
    assert response.status_code == 404
    assert response.json() == {"detail": "document not found"}


def test_a_disallowed_type_is_415_with_the_error_envelope(client: TestClient) -> None:
    response = _upload(client, name="old.doc", data=b"\xd0\xcf\x11\xe0")
    assert response.status_code == 415
    assert "unsupported file type" in response.json()["detail"]


def test_content_that_does_not_match_the_extension_is_415(client: TestClient) -> None:
    assert _upload(client, name="fake.pdf", data=b"plain text").status_code == 415


def test_an_empty_file_is_400(client: TestClient) -> None:
    assert _upload(client, name="empty.txt", data=b"").status_code == 400


def test_a_missing_file_part_is_422(client: TestClient) -> None:
    assert client.post(URL, data={"other": "x"}).status_code == 422


def test_an_oversize_file_is_413(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, client: TestClient
) -> None:
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")  # read when the use cases are built
    small = build_use_cases(
        repo=InMemoryConversationRepo(),
        documents=InMemoryDocumentRepo(),
        files=LocalDiskFileStore(tmp_path / "files"),
        verifier=FakeVerifier(),
        campaigns=owned_campaigns("ashfall"),
    )
    with TestClient(build_app(small), headers=client.headers) as limited:
        response = _upload(limited, data=PDF + b"x" * (1024 * 1024))

    assert response.status_code == 413
    assert "larger than 1 MB" in response.json()["detail"]


def test_campaigns_are_isolated(client: TestClient) -> None:
    created = _upload(client).json()
    other = "/api/v1/campaigns/other/documents"

    assert client.get(other).json() == []
    assert client.get(f"{other}/{created['id']}").status_code == 404
    # The same bytes in another campaign are a separate document, not a duplicate.
    assert _upload(client, url=other).status_code == 202


def test_every_documents_route_needs_a_token(anonymous_client: TestClient) -> None:
    assert anonymous_client.get(URL).status_code == 401
    assert anonymous_client.get(f"{URL}/1").status_code == 401
    assert _upload(anonymous_client).status_code == 401


def test_delete_returns_204_and_the_document_is_gone(client: TestClient) -> None:
    created = _upload(client).json()

    response = client.delete(f"{URL}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(URL).json() == []
    assert client.get(f"{URL}/{created['id']}").status_code == 404


def test_deleting_a_missing_or_foreign_document_is_404(client: TestClient) -> None:
    created = _upload(client).json()

    assert client.delete(f"{URL}/99").status_code == 404
    other = "/api/v1/campaigns/other/documents"
    assert client.delete(f"{other}/{created['id']}").status_code == 404
    assert len(client.get(URL).json()) == 1


def test_delete_needs_a_token(anonymous_client: TestClient) -> None:
    assert anonymous_client.delete(f"{URL}/1").status_code == 401


ADMIN = {"Authorization": "Bearer admin-token"}


def test_a_gm_cannot_write_the_vault(client: TestClient) -> None:
    """ADR-0027: only an admin writes the vault; the server decides, not the UI."""
    assert _upload(client, url="/api/v1/vault/documents").status_code == 403
    assert client.delete("/api/v1/vault/documents/1").status_code == 403


def test_an_admin_adds_to_the_vault_and_every_gm_reads_it(client: TestClient) -> None:
    response = client.post(
        "/api/v1/vault/documents",
        files={"file": ("SRD.pdf", PDF, "application/octet-stream")},
        data={"systems": "dnd-2024", "attribution": "SRD 5.2 · CC-BY-4.0"},
        headers=ADMIN,
    )

    assert response.status_code == 202
    assert response.json()["systems"] == ["dnd-2024"]
    assert response.json()["attribution"] == "SRD 5.2 · CC-BY-4.0"
    assert [d["filename"] for d in client.get("/api/v1/vault/documents").json()] == [
        "SRD.pdf"
    ]
    # Not in any campaign's own list.
    assert client.get(URL).json() == []


def test_an_unknown_system_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/library/documents",
        files={"file": ("x.pdf", PDF, "application/octet-stream")},
        data={"systems": "no-such-system"},
    )
    assert response.status_code == 400


def test_the_library_is_the_callers_own(client: TestClient) -> None:
    assert _upload(client, url="/api/v1/library/documents").status_code == 202

    mine = client.get("/api/v1/library/documents").json()
    admins = client.get("/api/v1/library/documents", headers=ADMIN).json()

    assert [d["filename"] for d in mine] == ["Core Rulebook.pdf"]
    assert admins == []
    assert (
        client.delete(
            f"/api/v1/library/documents/{mine[0]['id']}", headers=ADMIN
        ).status_code
        == 404
    )
