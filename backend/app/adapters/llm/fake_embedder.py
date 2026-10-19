import hashlib
import math
import random
from collections.abc import Sequence

from app.ports.embeddings import Purpose


class FakeEmbedder:
    """Deterministic Embedder. No network; identical text gives identical vectors."""

    def __init__(self, model: str = "fake", dimensions: int = 1024) -> None:
        self.model = model
        self.dimensions = dimensions

    def embed(self, texts: Sequence[str], purpose: Purpose) -> list[list[float]]:
        del purpose
        return [self._vector(text) for text in texts]

    def _vector(self, text: str) -> list[float]:
        rng = random.Random(hashlib.sha256(text.encode()).digest())
        raw = [rng.gauss(0, 1) for _ in range(self.dimensions)]
        norm = math.sqrt(sum(x * x for x in raw))
        return [x / norm for x in raw]
