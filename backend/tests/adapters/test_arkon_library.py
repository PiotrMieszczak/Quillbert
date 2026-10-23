import json

import httpx
import pytest
from app.adapters.library.arkon import ArkonLibrary, ArkonUnavailable
from app.adapters.library.combined import CampaignAndLibrarySearch
from app.ports.search import Hit

SOURCE_ID = "3f2b8c1e-0d4a-4b7e-9a51-6c2f0e8d1a77"

# search_wiki's text at Arkon 5e4069d: one model-written wiki page, one verbatim source.
SEARCH = f"""**KB search — 2 result(s) for: "grapple"**

- 📘 `rules/grappling` (concept) — 91%
  **Grappling** — A summary the model wrote.
  _Read: `read_wiki_page("rules/grappling")`_
- 📄 **SRD 5.2** (nguyên văn) — 84% — trang 12,13
  “A grapple is a hold…”
  _Đọc bản gốc: `get_source_pages("{SOURCE_ID}", "12")` · Link: /wiki/source/x_"""

PAGE = "--- page 12 ---\nGrappled. While Grappled, your Speed is 0."


def _sse(text: str, *, is_error: bool = False) -> httpx.Response:
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {"content": [{"type": "text", "text": text}], "isError": is_error},
    }
    return httpx.Response(
        200,
        text=f"event: message\ndata: {json.dumps(payload)}\n\n",
        headers={"content-type": "text/event-stream"},
    )


def _library(handler) -> ArkonLibrary:
    return ArkonLibrary(
        url="http://arkon:5055",
        tokens={"dnd-2024": "tok-2024"},
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_cites_verbatim_source_pages_never_wiki_pages() -> None:
    calls: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://arkon:5055/mcp/"
        assert request.headers["authorization"] == "Bearer tok-2024"
        body = json.loads(request.content)
        calls.append(body["params"])
        return _sse(SEARCH if body["params"]["name"] == "search_wiki" else PAGE)

    hits = _library(handler).search("ashfall", "dnd-2024", "grapple", None, 2)

    assert hits == [
        Hit(
            chunk_id=None,
            document_id=None,
            filename="SRD 5.2",
            page_from=12,
            heading=None,
            content="Grappled. While Grappled, your Speed is 0.",
            score=0.84,
            attribution="Shared library · dnd-2024",
        )
    ]
    assert calls[1] == {
        "name": "get_source_pages",
        "arguments": {"source_id": SOURCE_ID, "pages": "12"},
    }


def test_a_system_without_a_token_has_no_library_and_no_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request expected")

    assert _library(handler).search("ashfall", "traveller-2e", "jump", None, 2) == []


@pytest.mark.parametrize(
    "response",
    [httpx.Response(401), _sse("Error: invalid token", is_error=True)],
)
def test_a_failed_call_is_unavailable(response: httpx.Response) -> None:
    with pytest.raises(ArkonUnavailable):
        _library(lambda request: response).search("a", "dnd-2024", "q", None, 2)


class _Fixed:
    def __init__(self, hits: list[Hit] | Exception) -> None:
        self._hits = hits
        self.systems: list[str | None] = []

    def search(self, campaign_id, system_id, text, vector, k) -> list[Hit]:
        self.systems.append(system_id)
        if isinstance(self._hits, Exception):
            raise self._hits
        return self._hits[:k]


def _hit(name: str, attribution: str | None = None) -> Hit:
    return Hit(None, None, name, None, None, name, 1.0, attribution)


def test_library_hits_take_a_fixed_quota_of_the_tail() -> None:
    campaign = _Fixed([_hit(f"c{n}") for n in range(6)])
    library = _Fixed([_hit("l0", "lib"), _hit("l1", "lib"), _hit("l2", "lib")])
    search = CampaignAndLibrarySearch(campaign, library, library_k=2)

    hits = search.search("ashfall", "dnd-2024", "q", None, 6)

    assert [h.filename for h in hits] == ["c0", "c1", "c2", "c3", "l0", "l1"]
    assert library.systems == ["dnd-2024"]


def test_arkon_down_leaves_the_campaign_hits() -> None:
    campaign = _Fixed([_hit("c0")])
    search = CampaignAndLibrarySearch(
        campaign, _Fixed(ArkonUnavailable("down")), library_k=2
    )
    assert [h.filename for h in search.search("a", "dnd-2024", "q", None, 6)] == ["c0"]
