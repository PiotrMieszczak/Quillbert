"""Pages in, chunks out. Deterministic: the same pages always give the same chunks."""

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field

# ~500 tokens of English. Well under the embedder's 8,192-token input limit, past which
# text is silently truncated (ADR-0021 NEG-006).
TARGET_CHARS = 1800
# Text repeated at the start of the next chunk, so a passage cut at a boundary is
# still found whole in one of them (ADR-0021 IMP-006).
OVERLAP_CHARS = 200
# A line counts as page furniture when it is on this share of pages.
_FURNITURE_SHARE = 0.6
_FURNITURE_MIN_PAGES = 4
# Header/footer lines live in the first and last lines of a page.
_EDGE_LINES = 2


# (text, page number, heading in effect)
_Paragraph = tuple[str, int | None, str | None]


@dataclass(frozen=True)
class Block:
    """A paragraph or heading, in reading order."""

    text: str
    heading: bool = False


@dataclass(frozen=True)
class Page:
    # None for formats without pages (Markdown, text, DOCX).
    number: int | None
    blocks: tuple[Block, ...]
    # Text came from OCR, not the PDF's text layer.
    ocr: bool = False


@dataclass
class Chunk:
    ordinal: int
    content: str
    page_from: int | None
    page_to: int | None
    heading: str | None
    embedding: list[float] | None = field(default=None, repr=False)
    # The model that produced `embedding`, so a model change knows what to re-embed.
    embedding_model: str | None = None


def chunk_pages(pages: Sequence[Page]) -> list[Chunk]:
    """Split pages into overlapping chunks on paragraph boundaries.

    Repeated headers, footers, and watermarks ("Jane Doe – Order #123") are removed
    first, or they would be embedded into every chunk.
    """
    furniture = _furniture(pages)
    paragraphs: list[_Paragraph] = []
    heading: str | None = None
    for page in pages:
        for block in page.blocks:
            kept = [
                line
                for line in block.text.splitlines()
                if _key(_clean(line)) not in furniture
            ]
            text = _clean("\n".join(kept))
            if not text:
                continue
            if block.heading:
                heading = text
            for piece in _split_long(text):
                paragraphs.append((piece, page.number, heading))
    return _pack(paragraphs)


def _pack(paragraphs: list[_Paragraph]) -> list[Chunk]:
    chunks: list[Chunk] = []
    current: list[_Paragraph] = []
    carried = 0  # how many of `current` are overlap from the previous chunk
    size = 0
    for paragraph in paragraphs:
        if len(current) > carried and size + len(paragraph[0]) > TARGET_CHARS:
            chunks.append(_chunk(len(chunks), current))
            current = _overlap(current)
            carried = len(current)
            size = sum(len(text) + 2 for text, _, _ in current)
        current.append(paragraph)
        size += len(paragraph[0]) + 2
    # A remainder that is only overlap repeats text the last chunk already holds.
    if len(current) > carried:
        chunks.append(_chunk(len(chunks), current))
    return chunks


def _overlap(paragraphs: list[_Paragraph]) -> list[_Paragraph]:
    """About OVERLAP_CHARS from the end: whole short paragraphs, else the last
    paragraph's closing sentences."""
    kept: list[_Paragraph] = []
    size = 0
    for text, page, heading in reversed(paragraphs):
        if size + len(text) > OVERLAP_CHARS:
            if not kept:
                kept.append((_tail(text), page, heading))
            break
        kept.insert(0, (text, page, heading))
        size += len(text)
    return kept


def _tail(text: str) -> str:
    window = text[-OVERLAP_CHARS:]
    sentence = window.find(". ")
    if 0 <= sentence < len(window) // 2:
        return window[sentence + 2 :]
    return window[window.find(" ") + 1 :]


def _chunk(ordinal: int, paragraphs: list[_Paragraph]) -> Chunk:
    return Chunk(
        ordinal=ordinal,
        content="\n\n".join(text for text, _, _ in paragraphs),
        page_from=paragraphs[0][1],
        page_to=paragraphs[-1][1],
        heading=paragraphs[0][2],
    )


def _split_long(text: str) -> list[str]:
    """A paragraph longer than a chunk, split at sentence ends, else at spaces."""
    if len(text) <= TARGET_CHARS:
        return [text]
    pieces: list[str] = []
    rest = text
    while len(rest) > TARGET_CHARS:
        window = rest[:TARGET_CHARS]
        cut = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
        cut = cut + 1 if cut > TARGET_CHARS // 2 else window.rfind(" ")
        if cut <= 0:
            cut = TARGET_CHARS
        pieces.append(rest[:cut].strip())
        rest = rest[cut:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def _furniture(pages: Sequence[Page]) -> set[str]:
    if len(pages) < _FURNITURE_MIN_PAGES:
        return set()
    seen: Counter[str] = Counter()
    for page in pages:
        lines = [
            line
            for block in page.blocks
            for line in (_clean(part) for part in block.text.splitlines())
            if line
        ]
        edges = lines[:_EDGE_LINES] + lines[-_EDGE_LINES:]
        seen.update({_key(line) for line in edges})
    threshold = len(pages) * _FURNITURE_SHARE
    return {key for key, count in seen.items() if count >= threshold}


def _key(line: str) -> str:
    """Page furniture matches across pages once its numbers are ignored."""
    return re.sub(r"\d+", "#", line.casefold())


def _clean(text: str) -> str:
    # Rejoin words hyphenated across a line break, then collapse whitespace.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    return re.sub(r"\s+", " ", text).strip()
