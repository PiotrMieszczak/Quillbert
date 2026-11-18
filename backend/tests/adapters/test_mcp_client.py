import json
import socket

import httpx
import pytest
from app.adapters.mcp import HttpMcpClient
from app.adapters.mcp.address_guard import check
from app.ports.mcp import AddressRefused, McpError

PUBLIC = "93.184.216.34"
URL = "https://mcp.example.com/mcp"

TOOLS = [
    {
        "name": "search_rules",
        "description": "Search rules.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
            "required": ["query"],
        },
        "annotations": {"readOnlyHint": True},
    },
    {
        "name": "add_homebrew",
        "description": "x" * 900,
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "annotations": {"readOnlyHint": False},
    },
    {"name": "wipe", "annotations": {"readOnlyHint": True, "destructiveHint": True}},
    {"name": "unmarked"},
]


def _resolver(*addresses: str):
    calls: list[str] = []

    def resolve(host, port, **_):
        calls.append(host)
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (a, port)) for a in addresses
        ]

    resolve.calls = calls
    return resolve


def _sse(message: dict) -> httpx.Response:
    # A notification first, then the reply split across the event's data lines.
    noise = 'data: {"jsonrpc":"2.0","method":"notifications/message"}\n\n'
    head, tail = json.dumps(message)[:10], json.dumps(message)[10:]
    return httpx.Response(
        200,
        headers={"content-type": "text/event-stream"},
        content=f"event: message\r\n{noise}data: {head}{tail}\n\n".encode(),
    )


def _server(
    seen: list[httpx.Request], *, sse: bool = False, result: dict | None = None
):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = json.loads(request.content)
        if "id" not in body:
            return httpx.Response(202)
        if body["method"] == "initialize":
            reply = {"protocolVersion": "2025-03-26", "capabilities": {}}
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": body["id"], "result": reply},
                headers={"mcp-session-id": "sess-1"},
            )
        payload = result if result is not None else {"tools": TOOLS}
        message = {"jsonrpc": "2.0", "id": body["id"], "result": payload}
        return _sse(message) if sse else httpx.Response(200, json=message)

    return httpx.MockTransport(handler)


def _client(transport, resolve=None, **kwargs) -> HttpMcpClient:
    return HttpMcpClient(
        httpx.Client(transport=transport),
        resolve=resolve or _resolver(PUBLIC),
        **kwargs,
    )


@pytest.mark.parametrize("sse", [False, True])
def test_lists_tools_over_json_and_sse_and_carries_the_session(sse: bool) -> None:
    seen: list[httpx.Request] = []

    tools = _client(_server(seen, sse=sse)).list_tools(URL, "secret-token")

    by_name = {tool.name: tool for tool in tools}
    assert by_name["search_rules"].read_only is True
    assert by_name["search_rules"].query_arg == "query"
    assert by_name["add_homebrew"].read_only is False
    assert len(by_name["add_homebrew"].description) == 300
    assert by_name["wipe"].read_only is False
    assert by_name["unmarked"].read_only is None
    assert by_name["unmarked"].query_arg is None

    methods = [json.loads(r.content)["method"] for r in seen]
    assert methods == ["initialize", "notifications/initialized", "tools/list"]
    assert "mcp-session-id" not in seen[0].headers
    for request in seen[1:]:
        assert request.headers["mcp-session-id"] == "sess-1"
        assert request.headers["mcp-protocol-version"] == "2025-03-26"
    assert all(r.headers["authorization"] == "Bearer secret-token" for r in seen)


def test_every_request_goes_to_the_address_that_was_checked() -> None:
    """DNS rebinding: one lookup per operation, and the socket target is its answer."""
    seen: list[httpx.Request] = []
    resolve = _resolver(PUBLIC)

    _client(_server(seen), resolve).list_tools(URL, None)

    assert resolve.calls == ["mcp.example.com"]
    assert len(seen) == 3
    for request in seen:
        assert request.url.host == PUBLIC
        assert request.headers["host"] == "mcp.example.com"
        assert request.extensions["sni_hostname"] == "mcp.example.com"
        assert "authorization" not in request.headers


def test_call_tool_returns_text_blocks_only() -> None:
    result = {
        "content": [
            {"type": "text", "text": "Grappled: speed 0."},
            {"type": "image", "data": "..."},
            {"type": "text", "text": "PHB p. 290"},
        ]
    }
    seen: list[httpx.Request] = []

    texts = _client(_server(seen, result=result)).call_tool(
        URL, None, "search_rules", {"query": "grappled"}
    )

    assert texts == ["Grappled: speed 0.", "PHB p. 290"]
    assert json.loads(seen[-1].content)["params"] == {
        "name": "search_rules",
        "arguments": {"query": "grappled"},
    }


def test_a_tool_error_raises() -> None:
    result = {"isError": True, "content": [{"type": "text", "text": "boom"}]}
    with pytest.raises(McpError):
        _client(_server([], result=result)).call_tool(URL, None, "t", {})


@pytest.mark.parametrize(
    "url",
    [
        "http://mcp.example.com/mcp",
        "https://user:pw@mcp.example.com/mcp",
        "ftp://mcp.example.com",
        "https:///mcp",
        "not a url",
    ],
)
def test_only_plain_https_urls_are_accepted(url: str) -> None:
    with pytest.raises(AddressRefused):
        check(url, _resolver(PUBLIC))


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.5",
        "192.168.1.10",
        "169.254.169.254",
        "100.64.0.1",
        "0.0.0.0",
        "::1",
        "fe80::1",
        "fd00::1",
        "::ffff:127.0.0.1",
        "64:ff9b::a00:1",
    ],
)
def test_a_host_that_resolves_to_a_private_address_is_refused(address: str) -> None:
    with pytest.raises(AddressRefused):
        check(URL, _resolver(address))


def test_one_private_answer_among_public_ones_is_refused() -> None:
    with pytest.raises(AddressRefused):
        check(URL, _resolver(PUBLIC, "10.0.0.5"))


def test_public_addresses_pass_and_keep_port_path_and_query() -> None:
    target = check("https://mcp.example.com:8443/v1/mcp?x=1", _resolver("2606:4700::1"))
    assert target.url == "https://[2606:4700::1]:8443/v1/mcp?x=1"
    assert target.host == "mcp.example.com"
    # DNS64 form of a public IPv4 address.
    assert check(URL, _resolver("64:ff9b::5db8:d822")).ip == "64:ff9b::5db8:d822"


def test_a_refused_address_is_never_contacted() -> None:
    seen: list[httpx.Request] = []
    with pytest.raises(AddressRefused):
        _client(_server(seen), _resolver("127.0.0.1")).list_tools(URL, None)
    assert seen == []


def test_a_redirect_is_an_error_not_followed() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(307, headers={"location": "https://127.0.0.1/mcp"})

    with pytest.raises(McpError):
        _client(httpx.MockTransport(handler)).list_tools(URL, None)
    assert len(seen) == 1


def test_an_oversized_reply_raises() -> None:
    big = {"tools": [{"name": "t", "description": "x" * 5000}]}
    with pytest.raises(McpError, match="too large"):
        _client(_server([], result=big), max_bytes=1024).list_tools(URL, None)


def test_a_timeout_raises_without_the_token_or_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout(f"timed out {request.url} secret-token")

    with pytest.raises(McpError) as caught:
        _client(httpx.MockTransport(handler)).list_tools(URL, "secret-token")
    assert "secret-token" not in str(caught.value)
    assert "ReadTimeout" in str(caught.value)


def test_a_slow_stream_hits_the_deadline() -> None:
    with pytest.raises(McpError, match="too slow"):
        _client(_server([]), deadline_s=-1).list_tools(URL, None)
