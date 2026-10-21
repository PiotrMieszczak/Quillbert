import json
from datetime import UTC, datetime

import httpx
import pytest
from app.adapters.llm.openrouter import ZDR_PROVIDERS, OpenRouterChat
from app.domain.assistant import Message, Mode, Role
from app.ports.llm import LLMError, Usage
from app.ports.search import Hit

HISTORY = [
    Message(1, 1, Role.USER, "What is a grapple?", datetime.now(UTC), Mode.RESEARCH)
]
HITS = [Hit(1, 1, "SRD.pdf", 177, "Grappled", "A grapple is a hold.", 1.0)]


def _sse(*chunks: dict | str) -> bytes:
    lines = [": OPENROUTER PROCESSING\n"]
    for chunk in chunks:
        data = chunk if isinstance(chunk, str) else json.dumps(chunk)
        lines.append(f"data: {data}\n")
    return "\n".join(lines).encode()


def _delta(text: str) -> dict:
    return {
        "model": "google/gemini-3.5-flash-lite-x",
        "choices": [{"delta": {"content": text}}],
    }


USAGE = {
    "choices": [],
    "usage": {"prompt_tokens": 120, "completion_tokens": 9, "cost": 0.0000123},
}


def _chat(handler, provider: str = "google-vertex/eu") -> OpenRouterChat:
    return OpenRouterChat(
        api_key="sk-test",
        model="google/gemini-3.5-flash-lite",
        provider=provider,
        max_tokens=700,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def _run(chat: OpenRouterChat) -> list[str | Usage]:
    return list(chat.stream(mode=Mode.RESEARCH, history=HISTORY, hits=HITS))


def test_streams_text_then_usage() -> None:
    body = _sse(_delta("A grapple "), _delta("[S1]."), USAGE, "[DONE]")
    chat = _chat(lambda request: httpx.Response(200, content=body))

    assert _run(chat) == [
        "A grapple ",
        "[S1].",
        Usage("google/gemini-3.5-flash-lite-x", 120, 9, 0.0000123),
    ]


def test_request_pins_one_zero_retention_endpoint() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, content=_sse("[DONE]"))

    _run(_chat(handler))

    (request,) = seen
    body = json.loads(request.content)
    assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer sk-test"
    assert body["provider"] == {
        "only": ["google-vertex/eu"],
        "zdr": True,
        "allow_fallbacks": False,
        "data_collection": "deny",
    }
    assert body["stream"] is True
    assert body["usage"] == {"include": True}
    assert body["temperature"] == 0
    assert body["max_tokens"] == 700
    assert body["reasoning"] == {"effort": "low"}
    assert body["messages"][0]["role"] == "system"
    assert "A grapple is a hold." in body["messages"][-1]["content"]


@pytest.mark.parametrize("provider", ["google-ai-studio", "google-vertex", "", "any"])
def test_a_provider_off_the_allowlist_is_refused_and_nothing_is_sent(
    provider: str,
) -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(200, content=_sse("[DONE]"))

    with pytest.raises(ValueError, match="allowlist"):
        _chat(handler, provider)
    assert sent == []
    assert provider not in ZDR_PROVIDERS


def test_a_non_200_is_an_llm_error() -> None:
    chat = _chat(lambda request: httpx.Response(404, json={"error": "no endpoint"}))
    with pytest.raises(LLMError, match="HTTP 404"):
        _run(chat)


def test_an_error_chunk_mid_stream_is_an_llm_error() -> None:
    body = _sse(_delta("partial"), {"error": {"message": "boom"}})
    chat = _chat(lambda request: httpx.Response(200, content=body))
    with pytest.raises(LLMError):
        _run(chat)


def test_a_transport_failure_is_an_llm_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")

    with pytest.raises(LLMError):
        _run(_chat(handler))


def test_closing_the_generator_closes_the_http_stream() -> None:
    closed: list[bool] = []

    class Body(httpx.SyncByteStream):
        def __iter__(self):
            yield _sse(_delta("one "), _delta("two "))

        def close(self) -> None:
            closed.append(True)

    chat = _chat(lambda request: httpx.Response(200, stream=Body()))
    stream = chat.stream(mode=Mode.RESEARCH, history=HISTORY, hits=HITS)
    assert next(stream) == "one "
    stream.close()

    assert closed == [True]


def test_no_reasoning_field_when_effort_is_unset() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, content=_sse("[DONE]"))

    chat = OpenRouterChat(
        api_key="k",
        model="m",
        provider="google-vertex/eu",
        max_tokens=700,
        reasoning_effort=None,
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    _run(chat)
    assert "reasoning" not in seen[0]


def test_the_provider_error_text_reaches_the_exception() -> None:
    chat = _chat(
        lambda request: httpx.Response(
            400, json={"error": {"message": "Reasoning is mandatory"}}
        )
    )
    with pytest.raises(LLMError, match="Reasoning is mandatory"):
        _run(chat)
