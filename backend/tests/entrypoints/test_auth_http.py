from fastapi.testclient import TestClient

URL = "/api/v1/campaigns/ashfall/conversations"


def test_missing_token_is_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(URL, json={"mode": "research"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_token_is_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        URL, json={"mode": "research"}, headers={"Authorization": "Bearer nope"}
    )
    assert response.status_code == 401


def test_non_bearer_scheme_is_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        URL, json={"mode": "research"}, headers={"Authorization": "Basic abc"}
    )
    assert response.status_code == 401


def test_valid_token_passes(client: TestClient) -> None:
    assert client.post(URL, json={"mode": "research"}).status_code == 201
