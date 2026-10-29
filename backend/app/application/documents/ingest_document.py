import logging
from enum import Enum

from app.domain.documents import (
    Chunk,
    Document,
    DocumentKind,
    DocumentStatus,
    Page,
    chunk_pages,
)
from app.ports.embeddings import Embedder, EmbeddingUnavailable
from app.ports.extraction import ExtractionFailed, NeedsOcr, TextExtractor
from app.ports.files import FileStore
from app.ports.repositories import DocumentRepo

logger = logging.getLogger(__name__)

# Progress bar split: reading pages (and OCR) fills the first half, embedding the rest.
_EXTRACTED = 50
# Chunks per embedder call; progress is saved after each.
_BATCH = 64


class IngestOutcome(Enum):
    IDLE = "idle"  # nothing was queued
    DONE = "done"  # a document reached a final state
    DEFERRED = "deferred"  # the embedder is down; the document went back to the queue


class IngestDocument:
    """Takes the oldest queued document through extract → chunk → embed → index.

    No generative model is reachable from here (BND-001): the ports are an extractor
    and an embedder, never the LLMProvider.
    """

    def __init__(
        self,
        files: FileStore,
        repo: DocumentRepo,
        extractor: TextExtractor,
        embedder: Embedder,
    ) -> None:
        self._files = files
        self._repo = repo
        self._extractor = extractor
        self._embedder = embedder

    def execute(self) -> IngestOutcome:
        document = self._repo.claim_queued()
        if document is None:
            return IngestOutcome.IDLE
        try:
            return self._ingest(document)
        except Exception:
            # Never leave a document `processing` forever on a bug.
            logger.exception("ingesting document %s failed", document.id)
            self._finish(document, DocumentStatus.FAILED, error="internal error")
            return IngestOutcome.DONE

    def _ingest(self, document: Document) -> IngestOutcome:
        try:
            pages = self._read(document)
        except NeedsOcr:
            self._finish(
                document, DocumentStatus.AWAITING_OCR, meta="scanned — waiting for OCR"
            )
            return IngestOutcome.DONE
        except (ExtractionFailed, FileNotFoundError) as exc:
            self._finish(document, DocumentStatus.FAILED, error=str(exc))
            return IngestOutcome.DONE

        chunks = chunk_pages(pages)
        if not chunks:
            self._finish(document, DocumentStatus.FAILED, error="no readable text")
            return IngestOutcome.DONE

        try:
            self._embed(document, chunks)
        except EmbeddingUnavailable as exc:
            # A provider outage is not the document's fault (ADR-0021).
            logger.warning("embedding document %s deferred: %s", document.id, exc)
            document.status = DocumentStatus.QUEUED
            document.progress = 0
            self._repo.update(document)
            return IngestOutcome.DEFERRED

        document.status = DocumentStatus.INDEXED
        document.progress = 100
        document.error = None
        document.meta = _meta(pages, chunks)
        self._repo.index(document, chunks)
        return IngestOutcome.DONE

    def _read(self, document: Document) -> list[Page]:
        extraction = self._extractor.extract(
            self._files.read(document.storage_key), document.filename
        )
        if document.kind is DocumentKind.PDF:
            document.page_count = extraction.page_count
        pages: list[Page] = []
        for page in extraction.pages:
            pages.append(page)
            self._progress(document, _EXTRACTED * len(pages) // extraction.page_count)
        return pages

    def _embed(self, document: Document, chunks: list[Chunk]) -> None:
        for start in range(0, len(chunks), _BATCH):
            batch = chunks[start : start + _BATCH]
            vectors = self._embedder.embed([c.content for c in batch], "document")
            for chunk, vector in zip(batch, vectors, strict=True):
                chunk.embedding = vector
                chunk.embedding_model = self._embedder.model
            done = start + len(batch)
            self._progress(
                document, _EXTRACTED + (99 - _EXTRACTED) * done // len(chunks)
            )

    def _progress(self, document: Document, progress: int) -> None:
        if progress > document.progress:
            document.progress = progress
            self._repo.update(document)

    def _finish(
        self,
        document: Document,
        status: DocumentStatus,
        *,
        error: str | None = None,
        meta: str | None = None,
    ) -> None:
        document.status = status
        document.progress = 0
        document.error = error
        document.meta = meta
        self._repo.update(document)


def _count(n: int, noun: str) -> str:
    return f"{n} {noun}" if n == 1 else f"{n} {noun}s"


def _meta(pages: list[Page], chunks: list[Chunk]) -> str:
    """The Documents row's detail line: "412 passages · 12 scanned pages"."""
    parts = [_count(len(chunks), "passage")]
    scanned = sum(page.ocr for page in pages)
    unreadable = sum(page.ocr and not page.blocks for page in pages)
    if scanned:
        parts.append(_count(scanned, "scanned page"))
    if unreadable:
        parts.append(f"{unreadable} unreadable")
    return " · ".join(parts)
