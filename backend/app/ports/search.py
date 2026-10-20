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


class ChunkSearch(Protocol):
    """Hybrid retrieval over indexed chunks (ADR-0021). Read-only (BND-007)."""

    def search(
        self,
        campaign_id: str,
        system_id: str | None,
        text: str,
        vector: list[float] | None,
        k: int,
    ) -> list[Hit]:
        """Up to k hits, best first; empty when nothing clears the relevance floor.

        Only INDEXED documents of `campaign_id` are searched (BND-003). `vector` is
        the query embedding, or None when the embedder was unavailable: keyword
        search alone then (ADR-0016). `system_id` names the shared rules library to
        search as well; it is accepted now and ignored until that column exists
        (ADR-0023).
        """
        ...
