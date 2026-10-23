import re

from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.domain.documents import Document, DocumentStatus
from app.ports.search import Hit

_WORD = re.compile(r"\w+")


def _words(text: str) -> set[str]:
    return set(_WORD.findall(text.lower()))


class InMemoryChunkSearch:
    """Keyword overlap over an InMemoryDocumentRepo, for unit tests.

    shortcut: ignores the vector, so it cannot rank by meaning; the SQL adapter's
    contract tests cover that. Layers follow the same rules as the SQL (ADR-0027).
    """

    def __init__(self, documents: InMemoryDocumentRepo) -> None:
        self._documents = documents

    def search(
        self,
        campaign_id: str,
        owner_id: str | None,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        wanted = _words(text)
        hits = []
        for document in self._documents.all():
            if document.status is not DocumentStatus.INDEXED:
                continue
            layer = _layer(document, campaign_id, owner_id, system_id)
            if layer is False:
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
                            layer,
                        )
                    )
        hits.sort(key=lambda hit: (-hit.score, hit.chunk_id))
        return hits[: max(k, 0)]


def _layer(
    document: Document, campaign_id: str, owner_id: str | None, system_id: str | None
) -> str | None | bool:
    """The hit's attribution, or False when the document is out of reach."""
    if document.campaign_id is not None:
        return None if document.campaign_id == campaign_id else False
    if document.owner_id is not None and document.owner_id != owner_id:
        return False
    if document.systems and system_id not in document.systems:
        return False
    if document.owner_id is not None:
        return "My library"
    return document.attribution or "Vault"
