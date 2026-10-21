import json
import logging
from collections.abc import Generator, Sequence

import httpx

from app.adapters.llm.prompts import profile, research
from app.domain.assistant import Message, Mode
from app.ports.llm import LLMError, Profile, Usage
from app.ports.search import Hit

logger = logging.getLogger(__name__)

URL = "https://openrouter.ai/api/v1/chat/completions"

# OpenRouter endpoint tags that serve Gemini with zero data retention (ADR-0019
# IMP-003), per openrouter.ai/api/v1/endpoints/zdr. Google AI Studio is absent on
# purpose: it retains prompts.
ZDR_PROVIDERS = frozenset(
    {"google-vertex/eu", "google-vertex/us", "google-vertex/global"}
)


class OpenRouterChat:
    """Research answers from a chat model through OpenRouter. The only caller of chat
    completions (BND-002).

    Fails closed (ADR-0019 IMP-003): a provider outside ZDR_PROVIDERS is refused before
    any request exists, and every request pins that one endpoint with zdr, no
    fallbacks and data_collection deny, so OpenRouter errors rather than reroute.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        provider: str,
        max_tokens: int,
        client: httpx.Client | None = None,
        allowed: frozenset[str] = ZDR_PROVIDERS,
        reasoning_effort: str | None = "low",
    ) -> None:
        if provider not in allowed:
            raise ValueError(f"{provider!r} is not on the zero-retention allowlist")
        self.model = model
        self._max_tokens = max_tokens
        self._reasoning_effort = reasoning_effort
        self._provider = {
            "only": [provider],
            "zdr": True,
            "allow_fallbacks": False,
            "data_collection": "deny",
        }
        # Connect and write fast; a long read is a model thinking, not a dead link.
        self._client = client or httpx.Client(timeout=httpx.Timeout(60, connect=10))
        self._headers = {"Authorization": f"Bearer {api_key}"}

    def profile(self, mode: Mode) -> Profile:
        return profile(mode)

    def stream(
        self, *, mode: Mode, history: Sequence[Message], hits: Sequence[Hit]
    ) -> Generator[str | Usage, None, None]:
        if mode is not Mode.RESEARCH:
            raise ValueError("only research mode has a prompt")
        messages, _ = research.compose(history, hits)
        body = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": research.TEMPERATURE,
            "max_tokens": self._max_tokens,
            "usage": {"include": True},
            "provider": self._provider,
        }
        if self._reasoning_effort:
            # Thinking tokens count against max_tokens; some endpoints cannot turn
            # thinking off, so the lowest accepted effort is configuration.
            body["reasoning"] = {"effort": self._reasoning_effort}
        model = self.model
        usage: dict = {}
        try:
            with self._client.stream(
                "POST", URL, json=body, headers=self._headers
            ) as response:
                if response.status_code != 200:
                    raise LLMError(
                        f"OpenRouter chat: HTTP {response.status_code} "
                        f"{_error_message(response.read())}"
                    )
                for line in response.iter_lines():
                    # Blank lines and ": OPENROUTER PROCESSING" keep-alives.
                    if not line.startswith("data:"):
                        continue
                    payload = line.removeprefix("data:").strip()
                    if payload == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    if "error" in chunk:
                        raise LLMError("OpenRouter chat: error mid-stream")
                    model = chunk.get("model", model)
                    usage = chunk.get("usage") or usage
                    for choice in chunk.get("choices", []):
                        if text := (choice.get("delta") or {}).get("content"):
                            yield text
        except (httpx.HTTPError, ValueError) as exc:
            # ValueError: a malformed SSE payload.
            raise LLMError(f"OpenRouter chat: {type(exc).__name__}") from exc
        logger.info("chat reply from %s", model)
        yield Usage(
            model=model,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            cost_usd=usage.get("cost"),
        )


def _error_message(body: bytes) -> str:
    """OpenRouter's error text, for the log; never shown to the GM."""
    try:
        return str(json.loads(body)["error"]["message"])[:200]
    except (ValueError, KeyError, TypeError):
        return ""
