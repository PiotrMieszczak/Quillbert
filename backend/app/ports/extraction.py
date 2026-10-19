from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from app.domain.documents import Page


class ExtractionFailed(Exception):
    """The file cannot be read at all: corrupt, encrypted, or not what it claims."""


class NeedsOcr(Exception):
    """A page has no text layer and no OCR engine is available (ADR-0021 IMP-007)."""


@dataclass(frozen=True)
class Extraction:
    page_count: int
    # Lazy, so progress can be reported page by page.
    pages: Iterator[Page]


class TextExtractor(Protocol):
    """Bytes to pages, deterministically. No model is involved (BND-001, ADR-0002)."""

    def extract(self, data: bytes, filename: str) -> Extraction:
        """Raises ExtractionFailed; iterating `pages` may raise ExtractionFailed or
        NeedsOcr. An OCR page whose text is too unreliable to index has no blocks."""
        ...
