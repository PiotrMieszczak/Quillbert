import io
import zipfile

import pymupdf
import pytest
from app.adapters.extraction import FileExtractor, TesseractOcr
from app.adapters.extraction.ocr import paragraphs
from app.domain.documents import Block
from app.ports.extraction import ExtractionFailed, NeedsOcr


def _pdf(*pages: list[tuple[str, float]], scanned: int = 0) -> bytes:
    """Text pages of (text, font size) lines, then `scanned` image-only pages."""
    document = pymupdf.open()
    for lines in pages:
        page = document.new_page()
        y = 72.0
        for line, size in lines:
            page.insert_text((72, y), line, fontsize=size)
            y += size * 2.5
    for _ in range(scanned):
        page = document.new_page()
        pixmap = pymupdf.Pixmap(pymupdf.csGRAY, pymupdf.IRect(0, 0, 50, 50), False)
        pixmap.clear_with(200)
        page.insert_image(page.rect, pixmap=pixmap)
    return document.tobytes()


class _StubOcr(TesseractOcr):
    def __init__(self) -> None:
        self.calls = 0

    def read(self, image: bytes) -> tuple[Block, ...]:
        self.calls += 1
        assert image.startswith(b"\x89PNG")
        return (Block("Scanned words"),)


BODY = "Body text of the rulebook that is long enough to count as a text layer."


def test_pdf_pages_come_back_with_headings_marked() -> None:
    data = _pdf([("Skills", 24), (BODY, 11), (BODY, 11)], [(BODY, 11)])

    extraction = FileExtractor(ocr=None).extract(data, "Core.pdf")
    pages = list(extraction.pages)

    assert extraction.page_count == 2
    assert [p.number for p in pages] == [1, 2]
    first = pages[0].blocks
    assert first[0] == Block("Skills", heading=True)
    assert all(not block.heading for block in first[1:])
    assert not pages[0].ocr


def test_a_scanned_page_goes_to_ocr() -> None:
    ocr = _StubOcr()
    data = _pdf([(BODY, 11)], scanned=1)

    pages = list(FileExtractor(ocr=ocr).extract(data, "scan.pdf").pages)

    assert ocr.calls == 1
    assert pages[1].ocr and pages[1].blocks == (Block("Scanned words"),)


def test_a_scanned_page_without_ocr_needs_ocr() -> None:
    data = _pdf(scanned=1)

    with pytest.raises(NeedsOcr):
        list(FileExtractor(ocr=None).extract(data, "scan.pdf").pages)


def test_a_broken_pdf_fails_extraction() -> None:
    with pytest.raises(ExtractionFailed):
        FileExtractor(ocr=None).extract(b"%PDF-1.7 not really", "bad.pdf")


def test_markdown_headings_and_paragraphs() -> None:
    data = b"# Skills\n\nRoll 2D.\nAdd DMs.\n\n## Combat\n\nInitiative first."

    (page,) = FileExtractor(ocr=None).extract(data, "notes.md").pages

    assert page.number is None
    assert page.blocks == (
        Block("Skills", heading=True),
        Block("Roll 2D.\nAdd DMs."),
        Block("Combat", heading=True),
        Block("Initiative first."),
    )


def test_docx_paragraphs_and_heading_styles() -> None:
    w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    xml = (
        f'<w:document xmlns:w="{w}"><w:body>'
        '<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        "<w:r><w:t>Session 3</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>The crew </w:t></w:r><w:r><w:t>lands.</w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("word/document.xml", xml)

    (page,) = FileExtractor(ocr=None).extract(buffer.getvalue(), "notes.docx").pages

    assert page.blocks == (Block("Session 3", heading=True), Block("The crew lands."))


def test_a_broken_docx_fails_extraction() -> None:
    with pytest.raises(ExtractionFailed):
        FileExtractor(ocr=None).extract(b"PK\x03\x04garbage", "notes.docx")


_TSV_HEADER = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\t"
    "left\ttop\twidth\theight\tconf\ttext\n"
)


def _tsv(*words: tuple[str, str, str, float, str]) -> str:
    rows = [
        f"5\t1\t{block}\t{par}\t{line}\t1\t0\t0\t1\t1\t{conf}\t{word}"
        for block, par, line, conf, word in words
    ]
    return _TSV_HEADER + "\n".join(["1\t1\t0\t0\t0\t0\t0\t0\t1\t1\t-1\t", *rows]) + "\n"


def test_ocr_tsv_becomes_paragraphs_of_lines() -> None:
    tsv = _tsv(
        ("1", "1", "1", 95, "Roll"),
        ("1", "1", "1", 92, "2D"),
        ("1", "1", "2", 90, "today."),
        ("1", "2", "1", 96, "Next"),
    )

    assert paragraphs(tsv) == (Block("Roll 2D\ntoday."), Block("Next"))


def test_low_confidence_ocr_is_unreadable() -> None:
    tsv = _tsv(("1", "1", "1", 20, "W#r!d"), ("1", "1", "1", 35, "n0ise"))

    assert paragraphs(tsv) == ()
