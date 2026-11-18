import json
import socket
import time
from typing import Any

import httpx

from app.adapters.mcp.address_guard import Resolver, Target, check
from app.ports.mcp import McpError, McpTool

# The newest revision this client was written against; the server may answer older.
_PROTOCOL = "2025-06-18"
_MAX_TOOLS = 50
_MAX_DESCRIPTION = 300


class HttpMcpClient:
    """MCP over streamable HTTP with plain `httpx` (ADR-0031). Sync like the rest of
    the backend, and it owns the socket target, which the address guard needs.

    Every operation is one short session: initialize, initialized, the call.
    shortcut: the session is not deleted afterwards, add DELETE if a server leaks them.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        *,
        resolve: Resolver = socket.getaddrinfo,
        deadline_s: float = 8,
        max_bytes: int = 256 * 1024,
    ) -> None:
        # Redirects are never followed: a 3xx could point at a private address.
        self._client = client or httpx.Client(
            timeout=httpx.Timeout(5, connect=3), follow_redirects=False
        )
        self._resolve = resolve
        self._deadline_s = deadline_s
        self._max_bytes = max_bytes

    def list_tools(self, url: str, token: str | None) -> list[McpTool]:
        session = _Session(self, check(url, self._resolve), token)
        listed = session.request("tools/list", {}).get("tools")
        if not isinstance(listed, list):
            raise McpError("the server listed no tools")
        return [
            _tool(item)
            for item in listed[:_MAX_TOOLS]
            if isinstance(item, dict) and item.get("name")
        ]

    def call_tool(
        self, url: str, token: str | None, name: str, arguments: dict[str, Any]
    ) -> list[str]:
        session = _Session(self, check(url, self._resolve), token)
        result = session.request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise McpError("the tool reported an error")
        return [
            block["text"]
            for block in result.get("content") or []
            if isinstance(block, dict)
            and block.get("type") == "text"
            and isinstance(block.get("text"), str)
        ]

    def _post(
        self, target: Target, headers: dict[str, str], body: dict[str, Any]
    ) -> tuple[httpx.Headers, dict[str, Any] | None]:
        """One JSON-RPC message. Returns the response headers and, for a request,
        the reply with the same id."""
        wanted = body.get("id")
        started = time.monotonic()
        try:
            with self._client.stream(
                "POST",
                target.url,
                json=body,
                headers={
                    "Host": target.host,
                    "Accept": "application/json, text/event-stream",
                    **headers,
                },
                # TLS is verified against the name, though the socket goes to the IP.
                extensions={"sni_hostname": target.host},
            ) as response:
                if response.status_code >= 300:
                    raise McpError(f"the server answered {response.status_code}")
                if wanted is None:
                    return response.headers, None
                stream = response.headers.get("content-type", "").startswith(
                    "text/event-stream"
                )
                buffer = b""
                for chunk in response.iter_bytes():
                    buffer += chunk
                    if len(buffer) > self._max_bytes:
                        raise McpError("the reply was too large")
                    if time.monotonic() - started > self._deadline_s:
                        raise McpError("the server was too slow")
                    if stream and (reply := _event(buffer, wanted)) is not None:
                        return response.headers, reply
                reply = _event(buffer + b"\n\n", wanted) if stream else _json(buffer)
        except httpx.HTTPError as exc:
            # The exception text can hold the URL; the class name is enough.
            raise McpError(
                f"the server was not reached ({type(exc).__name__})"
            ) from exc
        if not isinstance(reply, dict) or reply.get("id") != wanted:
            raise McpError("the server sent no reply")
        return response.headers, reply


class _Session:
    def __init__(self, client: HttpMcpClient, target: Target, token: str | None):
        self._client = client
        self._target = target
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}
        self._id = 0
        opened = self.request(
            "initialize",
            {
                "protocolVersion": _PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "quillbert", "version": "1"},
            },
        )
        self._headers["MCP-Protocol-Version"] = str(
            opened.get("protocolVersion") or _PROTOCOL
        )
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._id += 1
        reply = self._send(
            {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params}
        )
        result = reply and reply.get("result")
        if not isinstance(result, dict):
            raise McpError(f"the server refused {method}")
        return result

    def _send(self, body: dict[str, Any]) -> dict[str, Any] | None:
        headers, reply = self._client._post(self._target, self._headers, body)
        if session := headers.get("mcp-session-id"):
            self._headers["Mcp-Session-Id"] = session
        return reply


def _json(raw: bytes) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return None


def _event(buffer: bytes, wanted: Any) -> dict[str, Any] | None:
    """The JSON-RPC reply with id `wanted` among the complete SSE events so far."""
    *complete, _ = buffer.replace(b"\r\n", b"\n").split(b"\n\n")
    for event in complete:
        data = b"\n".join(
            line[5:].lstrip()
            for line in event.split(b"\n")
            if line.startswith(b"data:")
        )
        message = _json(data)
        if isinstance(message, dict) and message.get("id") == wanted:
            return message
    return None


def _tool(item: dict[str, Any]) -> McpTool:
    schema = (
        item.get("inputSchema") if isinstance(item.get("inputSchema"), dict) else {}
    )
    required = schema.get("required") or []
    properties = schema.get("properties") or {}
    query_arg = None
    if len(required) == 1 and isinstance(properties.get(required[0]), dict):
        if properties[required[0]].get("type") == "string":
            query_arg = required[0]
    hints = item.get("annotations") if isinstance(item.get("annotations"), dict) else {}
    read_only = hints.get("readOnlyHint")
    if hints.get("destructiveHint") is True:
        read_only = False
    return McpTool(
        name=str(item.get("name", "")),
        description=str(item.get("description") or "")[:_MAX_DESCRIPTION],
        read_only=read_only if isinstance(read_only, bool) else None,
        query_arg=query_arg,
    )
