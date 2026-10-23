from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Hit:
    # None for a passage from the shared library (ADR-0027): it has no chunk here.
    chunk_id: int | None
    document_id: int | None
    filename: str
    page_from: int | None
    heading: str | None
    content: str
    # Reciprocal-rank-fusion score: only the order and the floor mean anything.
    score: float
    # Where a library passage comes from, shown with its citation; None for campaign.
    attribution: str | None = None


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
        search alone then (ADR-0016). `system_id` is the campaign's game system; the
        shared library searches it (ADR-0027), campaign search ignores it.
        """
        ...
