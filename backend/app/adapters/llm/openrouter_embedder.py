import logging
import math
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.ports.embeddings import EmbeddingUnavailable, Purpose

logger = logging.getLogger(__name__)

URL = "https://openrouter.ai/api/v1/embeddings"

# gemini-embedding-2 takes its task as a text prefix; task_type is unsupported.
_PREFIX = {
    "query": "task: search result | query: ",
    "document": "title: none | text: ",
}
_RETRYABLE = {429, 500, 502, 503, 504}
_ATTEMPTS = 3
_WORKERS = 8


class OpenRouterEmbedder:
    """Gemini embeddings through OpenRouter, pinned to a zero-retention endpoint.

    Fails closed (ADR-0019 IMP-003): `zdr` plus `only` means OpenRouter refuses rather
    than fall back to an endpoint that retains data (Google AI Studio).
    `data_collection: deny` is deliberately absent: it also excludes Vertex.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        provider: str,
        dimensions: int = 1024,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.model = model
        self.dimensions = dimensions
        self._provider = {"only": [provider], "zdr": True, "allow_fallbacks": False}
        self._client = client or httpx.Client(timeout=30)
        self._headers = {"Authorization": f"Bearer {api_key}"}
        self._sleep = sleep

    def embed(self, texts: Sequence[str], purpose: Purpose) -> list[list[float]]:
        prefix = _PREFIX[purpose]
        # One text per request: on zero-retention Vertex, gemini-embedding-2 has no
        # batch endpoint, so a batch would be routed to a retaining one.
        with ThreadPoolExecutor(_WORKERS) as pool:
            return list(pool.map(lambda text: self._embed_one(prefix + text), texts))

    def _embed_one(self, text: str) -> list[float]:
        body = {
            "model": self.model,
            "input": text,
            "dimensions": self.dimensions,
            "encoding_format": "float",
            "provider": self._provider,
        }
        for attempt in range(_ATTEMPTS):
            try:
                response = self._client.post(URL, json=body, headers=self._headers)
            except httpx.TransportError as exc:
                failure = f"transport error: {exc}"
            else:
                if response.status_code == 200:
                    return self._vector(response)
                failure = f"HTTP {response.status_code}"
                if response.status_code not in _RETRYABLE:
                    raise EmbeddingUnavailable(f"OpenRouter embeddings: {failure}")
            if attempt < _ATTEMPTS - 1:
                self._sleep(2**attempt)
        logger.warning("OpenRouter embeddings gave up: %s", failure)
        raise EmbeddingUnavailable(f"OpenRouter embeddings: {failure}")

    def _vector(self, response: httpx.Response) -> list[float]:
        try:
            vector = response.json()["data"][0]["embedding"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise EmbeddingUnavailable("OpenRouter embeddings: malformed body") from exc
        if len(vector) != self.dimensions:
            raise EmbeddingUnavailable(
                f"OpenRouter embeddings: got {len(vector)} dimensions, "
                f"expected {self.dimensions}"
            )
        if not math.isclose(math.sqrt(sum(x * x for x in vector)), 1, abs_tol=1e-3):
            raise EmbeddingUnavailable("OpenRouter embeddings: vector not unit length")
        return vector
