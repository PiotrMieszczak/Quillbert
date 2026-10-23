import json
import logging
import re
from collections.abc import Mapping

import httpx

from app.ports.search import Hit

logger = logging.getLogger(__name__)

# One 📄 verbatim match in search_wiki's text. 📘 wiki pages are model-written
# summaries and are never cited (ADR-0027, PRIN-001).
_SOURCE = re.compile(
    r"📄 \*\*(?P<title>.+?)\*\*.*?— (?P<pct>\d+)% —.*?"
    r'get_source_pages\("(?P<id>[0-9a-f-]{36})", "(?P<page>\d+)"\)',
    re.DOTALL,
)
_PAGE = re.compile(r"--- page (\d+) ---\n")
# shortcut: a whole page is one passage, capped; cite chunks once Arkon returns them.
_MAX_CHARS = 2000


class ArkonUnavailable(Exception):
    """Arkon did not answer, or answered something this adapter cannot read."""


class ArkonLibrary:
    """The shared rules library in Arkon, over its MCP endpoint (ADR-0027).

    One read-only token per game system: Arkon scopes what a token sees by the
    employee's departments, so the token is the system filter. Read tools only
    (BND-007). Arkon's tool output is text, parsed here.
    """

    def __init__(
        self,
        *,
        url: str,
        tokens: Mapping[str, str],
        client: httpx.Client | None = None,
    ) -> None:
        self._endpoint = url.rstrip("/") + "/mcp/"
        self._tokens = dict(tokens)
        self._client = client or httpx.Client(timeout=20)

    def search(
        self,
        campaign_id: str,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        """Raises ArkonUnavailable; no token for the system is simply no hits."""
        token = self._tokens.get(system_id or "")
        if token is None:
            return []
        found = self._call(token, "search_wiki", {"query": text, "top_k": k * 2})
        hits = []
        for match in list(_SOURCE.finditer(found))[:k]:
            page = int(match["page"])
            body = self._call(
                token,
                "get_source_pages",
                {"source_id": match["id"], "pages": str(page)},
            )
            content = _PAGE.sub("", body).strip()[:_MAX_CHARS]
            if not content:
                continue
            hits.append(
                Hit(
                    chunk_id=None,
                    document_id=None,
                    filename=match["title"],
                    page_from=page,
                    heading=None,
                    content=content,
                    score=int(match["pct"]) / 100,
                    attribution=f"Shared library · {system_id}",
                )
            )
        return hits

    def _call(self, token: str, tool: str, arguments: dict) -> str:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        }
        try:
            response = self._client.post(
                self._endpoint,
                json=request,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json, text/event-stream",
                },
            )
        except httpx.TransportError as exc:
            raise ArkonUnavailable(f"{tool}: transport error: {exc}") from exc
        if response.status_code != 200:
            raise ArkonUnavailable(f"{tool}: HTTP {response.status_code}")
        try:
            result = _rpc_result(response)
            text = "\n".join(
                part["text"] for part in result["content"] if part["type"] == "text"
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ArkonUnavailable(f"{tool}: unreadable reply") from exc
        if result.get("isError"):
            raise ArkonUnavailable(f"{tool}: {text[:200]}")
        return text


def _rpc_result(response: httpx.Response) -> dict:
    """The JSON-RPC result, from a JSON body or the SSE stream FastMCP sends."""
    if response.headers.get("content-type", "").startswith("text/event-stream"):
        data = [
            line.removeprefix("data:").strip()
            for line in response.text.splitlines()
            if line.startswith("data:")
        ]
        payload = json.loads(data[-1])
    else:
        payload = response.json()
    if "error" in payload:
        raise ValueError(payload["error"])
    return payload["result"]
