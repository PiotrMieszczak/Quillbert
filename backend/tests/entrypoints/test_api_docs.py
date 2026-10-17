from app.entrypoints.http import create_http_app
from fastapi.testclient import TestClient


def test_swagger_and_redoc_are_off_by_default() -> None:
    client = TestClient(create_http_app())
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404


def test_swagger_and_redoc_can_be_enabled() -> None:
    client = TestClient(create_http_app(api_docs=True))
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200
