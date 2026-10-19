from collections import Counter
from collections.abc import Iterator

import pymupdf

from app.adapters.extraction.ocr import TesseractOcr
from app.domain.documents import Block, Page
from app.ports.extraction import Extraction, ExtractionFailed, NeedsOcr

# A page with fewer characters than this in its text layer is treated as a scan.
_SCAN_CHARS = 20
_OCR_DPI = 300
# A block is a heading when its type is this much larger than the page's body text.
_HEADING_SCALE = 1.2
_HEADING_MAX_CHARS = 120


def extract_pdf(data: bytes, ocr: TesseractOcr | None) -> Extraction:
    try:
        document = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises several types for a broken file
        raise ExtractionFailed(f"not a readable PDF: {exc}") from exc
    if document.needs_pass:
        document.close()
        raise ExtractionFailed("the PDF is password-protected")
    return Extraction(page_count=document.page_count, pages=_pages(document, ocr))


def _pages(document: pymupdf.Document, ocr: TesseractOcr | None) -> Iterator[Page]:
    with document:
        for index, page in enumerate(document):
            number = index + 1
            blocks = _text_blocks(page)
            if sum(len(block.text) for block in blocks) >= _SCAN_CHARS:
                yield Page(number, blocks)
                continue
            if ocr is None:
                raise NeedsOcr(f"page {number} has no text layer")
            image = page.get_pixmap(dpi=_OCR_DPI, colorspace=pymupdf.csGRAY)
            yield Page(number, ocr.read(image.tobytes("png")), ocr=True)


def _text_blocks(page: pymupdf.Page) -> tuple[Block, ...]:
    # Content-stream order, not sort=True: sorting by position interleaves the
    # columns of a two-column rulebook.
    raw = [b for b in page.get_text("dict")["blocks"] if b.get("type") == 0]
    sizes: Counter[float] = Counter()
    for block in raw:
        for span in _spans(block):
            sizes[round(span["size"], 1)] += len(span["text"])
    body = sizes.most_common(1)[0][0] if sizes else 0.0
    blocks: list[Block] = []
    for block in raw:
        text = "\n".join(
            "".join(span["text"] for span in line["spans"]) for line in block["lines"]
        ).strip()
        if not text:
            continue
        largest = max((span["size"] for span in _spans(block)), default=0.0)
        heading = (
            body > 0
            and largest >= body * _HEADING_SCALE
            and len(text) <= _HEADING_MAX_CHARS
        )
        blocks.append(Block(text, heading=heading))
    return tuple(blocks)


def _spans(block: dict) -> Iterator[dict]:
    for line in block["lines"]:
        for span in line["spans"]:
            if span["text"].strip():
                yield span
