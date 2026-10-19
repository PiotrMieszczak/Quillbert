"""Which embedder composition picks, by key and storage (#64)."""

import logging

import pytest
from app.adapters.llm.openrouter_embedder import OpenRouterEmbedder
from app.composition import build_use_cases


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("OPEN_ROUTER_API_KEY", "DATABASE_URL", "EMBEDDING_MODEL"):
        monkeypatch.delenv(name, raising=False)


def _embedder(cases):
    # Reaching into the worker is the only way to see what composition chose.
    return cases.worker._ingest._embedder


def test_no_key_in_memory_uses_a_fake_labelled_fake() -> None:
    cases = build_use_cases()

    assert cases.worker is not None
    assert _embedder(cases).model == "fake"


def test_no_key_with_a_database_turns_ingestion_off(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    # Never connected: without an embedder nothing checks embedding_space.
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://x:x@127.0.0.1:9/none")

    with caplog.at_level(logging.ERROR, logger="app.composition"):
        cases = build_use_cases()

    assert cases.worker is None
    assert "ingestion is off" in caplog.text


def test_a_key_uses_the_configured_gemini_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPEN_ROUTER_API_KEY", "test-key")

    embedder = _embedder(build_use_cases())

    assert isinstance(embedder, OpenRouterEmbedder)
    assert embedder.model == "google/gemini-embedding-2"
