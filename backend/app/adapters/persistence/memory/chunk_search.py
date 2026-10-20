import re

from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.domain.documents import DocumentStatus
from app.ports.search import Hit

_WORD = re.compile(r"\w+")


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


class InMemoryChunkSearch:
    """Keyword overlap over an InMemoryDocumentRepo, for unit tests.

    shortcut: ignores the vector and system_id, so it cannot rank by meaning;
    the SQL adapter's contract tests cover that.
    """

    def __init__(self, documents: InMemoryDocumentRepo) -> None:
        self._documents = documents

    def search(
        self,
        campaign_id: str,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        wanted = _words(text)
        hits = []
        for document in self._documents.list_for_campaign(campaign_id):
            if document.status is not DocumentStatus.INDEXED:
                continue
            for chunk in self._documents.chunks.get(document.id, []):
                overlap = len(wanted & _words(chunk.content))
                if overlap:
                    # No chunk row, so no id: document id and ordinal stand in.
                    hits.append(
                        Hit(
                            document.id * 100_000 + chunk.ordinal,
                            document.id,
                            document.filename,
                            chunk.page_from,
                            chunk.heading,
                            chunk.content,
                            overlap / len(wanted),
                        )
                    )
        hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return hits[: max(k, 0)]
