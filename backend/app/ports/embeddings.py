from collections.abc import Sequence
from typing import Literal, Protocol

Purpose = Literal["document", "query"]


class EmbeddingUnavailable(Exception):
    """The provider could not embed right now. Callers retry or degrade (ADR-0021)."""


class Embedder(Protocol):
    """The one fixed embedding model (BND-002). Adapters live in app.adapters.llm."""

    model: str
    dimensions: int

    def embed(self, texts: Sequence[str], purpose: Purpose) -> list[list[float]]:
        """One unit-length vector per text, in input order.

        Raises EmbeddingUnavailable; it never returns a partial result.
        """
        ...
