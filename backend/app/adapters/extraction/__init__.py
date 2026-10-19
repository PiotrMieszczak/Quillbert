"""TextExtractor adapters: PyMuPDF for PDF, Tesseract for scanned pages, the stdlib for
Markdown, text and DOCX. No model is reachable from here (BND-001)."""

from app.adapters.extraction.ocr import TesseractOcr
from app.adapters.extraction.pymupdf import extract_pdf
from app.adapters.extraction.text import extract_docx, extract_text
from app.ports.extraction import Extraction, ExtractionFailed


class FileExtractor:
    """Picks the reader by extension; upload already checked the bytes agree."""

    def __init__(self, ocr: TesseractOcr | None) -> None:
        self._ocr = ocr

    def extract(self, data: bytes, filename: str) -> Extraction:
        extension = filename.rpartition(".")[2].lower()
        if extension == "pdf":
            return extract_pdf(data, self._ocr)
        if extension == "docx":
            return extract_docx(data)
        if extension in ("md", "txt"):
            return extract_text(data, markdown=extension == "md")
        raise ExtractionFailed(f"no extractor for .{extension}")


__all__ = ["FileExtractor", "TesseractOcr"]
