"""Markdown, plain text and DOCX: formats without pages, read with the stdlib."""

import io
import re
import zipfile
from xml.etree import ElementTree

from app.domain.documents import Block, Page
from app.ports.extraction import Extraction, ExtractionFailed

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def extract_text(data: bytes, *, markdown: bool) -> Extraction:
    text = data.decode("utf-8", errors="replace").replace("\r\n", "\n")
    blocks = []
    for part in re.split(r"\n\s*\n", text):
        part = part.strip()
        if not part:
            continue
        heading = markdown and part.startswith("#") and "\n" not in part
        blocks.append(Block(part.lstrip("#").strip() if heading else part, heading))
    return _single(tuple(blocks))


def extract_docx(data: bytes) -> Extraction:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            root = ElementTree.fromstring(archive.read("word/document.xml"))
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ExtractionFailed(f"not a readable DOCX: {exc}") from exc
    blocks = []
    for paragraph in root.iter(f"{_W}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{_W}t")).strip()
        if not text:
            continue
        style = paragraph.find(f"{_W}pPr/{_W}pStyle")
        name = "" if style is None else style.get(f"{_W}val", "")
        blocks.append(Block(text, heading=name.startswith(("Heading", "Title"))))
    return _single(tuple(blocks))


def _single(blocks: tuple[Block, ...]) -> Extraction:
    return Extraction(page_count=1, pages=iter([Page(None, blocks)]))
