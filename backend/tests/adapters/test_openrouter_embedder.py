import json
import math

import httpx
import pytest
from app.adapters.llm.openrouter_embedder import OpenRouterEmbedder
from app.ports.embeddings import EmbeddingUnavailable

DIMS = 4


def _unit(*values: float) -> list[float]:
    norm = math.sqrt(sum(x * x for x in values))
    return [x / norm for x in values]


def _embedder(handler: httpx.MockTransport | None, sleeps: list[float] | None = None):
    return OpenRouterEmbedder(
        api_key="test-key",
        model="google/gemini-embedding-2",
        provider="google-vertex/eu",
        dimensions=DIMS,
        client=httpx.Client(transport=handler),
        sleep=(sleeps if sleeps is not None else []).append,
    )


def _ok(vector: list[float]) -> httpx.Response:
    return httpx.Response(200, json={"data": [{"embedding": vector}]})


def test_request_is_pinned_to_a_zero_retention_endpoint() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return _ok(_unit(1, 0, 0, 0))

    _embedder(httpx.MockTransport(handler)).embed(["hello"], "document")

    (request,) = seen
    body = json.loads(request.content)
    assert request.headers["authorization"] == "Bearer test-key"
    assert body["model"] == "google/gemini-embedding-2"
    assert body["dimensions"] == DIMS
    assert body["provider"] == {
        "only": ["google-vertex/eu"],
        "zdr": True,
        "allow_fallbacks": False,
    }


def test_task_prefix_and_single_input_per_request() -> None:
    inputs: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        inputs.append(json.loads(request.content)["input"])
        return _ok(_unit(1, 0, 0, 0))

    embedder = _embedder(httpx.MockTransport(handler))
    embedder.embed(["a", "b"], "document")
    embedder.embed(["q"], "query")

    assert sorted(inputs) == [
        "task: search result | query: q",
        "title: none | text: a",
        "title: none | text: b",
    ]


def test_vectors_come_back_in_input_order() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        text = json.loads(request.content)["input"].removeprefix("title: none | text: ")
        return _ok(_unit(1, 0, 0, 0) if text == "first" else _unit(0, 1, 0, 0))

    vectors = _embedder(httpx.MockTransport(handler)).embed(
        ["first", "second", "first"], "document"
    )

    assert vectors == [_unit(1, 0, 0, 0), _unit(0, 1, 0, 0), _unit(1, 0, 0, 0)]


def test_transient_errors_are_retried_with_backoff() -> None:
    statuses = iter([429, 503])
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        status = next(statuses, 200)
        return httpx.Response(status) if status != 200 else _ok(_unit(1, 0, 0, 0))

    vectors = _embedder(httpx.MockTransport(handler), sleeps).embed(["x"], "query")

    assert vectors == [_unit(1, 0, 0, 0)]
    assert sleeps == [1, 2]


def test_gives_up_after_three_attempts() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503)

    with pytest.raises(EmbeddingUnavailable):
        _embedder(httpx.MockTransport(handler)).embed(["x"], "document")
    assert len(calls) == 3


def test_a_refusal_is_not_retried() -> None:
    """404 means no zero-retention endpoint: fail closed, do not retry."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(404, json={"error": {"message": "no ZDR endpoint"}})

    with pytest.raises(EmbeddingUnavailable):
        _embedder(httpx.MockTransport(handler)).embed(["x"], "document")
    assert len(calls) == 1


@pytest.mark.parametrize(
    "vector", [[1.0, 0.0, 0.0], [1.0, 1.0, 0.0, 0.0]], ids=["wrong-size", "not-unit"]
)
def test_malformed_vectors_are_rejected(vector: list[float]) -> None:
    transport = httpx.MockTransport(lambda request: _ok(vector))
    with pytest.raises(EmbeddingUnavailable):
        _embedder(transport).embed(["x"], "document")


def test_malformed_body_is_rejected() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    with pytest.raises(EmbeddingUnavailable):
        _embedder(transport).embed(["x"], "document")
