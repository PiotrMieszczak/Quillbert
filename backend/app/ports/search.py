from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Hit:
    chunk_id: int
    document_id: int
    filename: str
    page_from: int | None
    heading: str | None
    content: str
    # Reciprocal-rank-fusion score: only the order and the floor mean anything.
    score: float
    # The layer a passage comes from, e.g. "My library" or a vault licence line; None
    # for the campaign's own documents (ADR-0027).
    attribution: str | None = None


class ChunkSearch(Protocol):
    """Hybrid retrieval over indexed chunks (ADR-0021). Read-only (BND-007)."""

    def search(
        self,
        campaign_id: str,
        owner_id: str | None,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        """Up to k hits, best first; empty when nothing clears the relevance floor.

        Only INDEXED documents are searched: the campaign's own, plus its owner's
        library and the vault, the last two only where they apply to `system_id`
        (ADR-0027, BND-003). `vector` is the query embedding, or None when the embedder
        was unavailable: keyword search alone then (ADR-0016).
        """
        ...
