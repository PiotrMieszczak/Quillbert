import dataclasses
from collections.abc import Sequence

from app.domain.documents import Chunk, Document, DocumentStatus
from app.domain.shared import NotFound


class InMemoryDocumentRepo:
    def __init__(self, campaigns: set[str] | None = None) -> None:
        # None accepts any campaign id. A set mirrors the SQL foreign key, for the
        # contract suite.
        self._campaigns = campaigns
        self._documents: dict[int, Document] = {}
        self.chunks: dict[int, list[Chunk]] = {}
        self._next_id = 1

    def next_document_id(self) -> int:
        ident = self._next_id
        self._next_id += 1
        return ident

    def add(self, document: Document) -> None:
        if self._campaigns is not None and document.campaign_id not in self._campaigns:
            raise NotFound("campaign not found")
        self._documents[document.id] = document

    def get(self, campaign_id: str, document_id: int) -> Document | None:
        document = self._documents.get(document_id)
        if document is None or document.campaign_id != campaign_id:
            return None
        return document

    def list_for_campaign(self, campaign_id: str) -> list[Document]:
        return sorted(
            (d for d in self._documents.values() if d.campaign_id == campaign_id),
            key=lambda document: document.id,
        )

    def remove(self, campaign_id: str, document_id: int) -> Document | None:
        document = self.get(campaign_id, document_id)
        if document is not None:
            del self._documents[document_id]
            self.chunks.pop(document_id, None)
        return document

    def find_by_sha256(self, campaign_id: str, sha256: str) -> Document | None:
        for document in self.list_for_campaign(campaign_id):
            if document.sha256 == sha256:
                return document
        return None

    def claim_queued(self) -> Document | None:
        queued = [
            d for d in self._documents.values() if d.status is DocumentStatus.QUEUED
        ]
        if not queued:
            return None
        document = min(queued, key=lambda d: d.id)
        document.status = DocumentStatus.PROCESSING
        return dataclasses.replace(document)

    def requeue_processing(self) -> int:
        stuck = [
            d for d in self._documents.values() if d.status is DocumentStatus.PROCESSING
        ]
        for document in stuck:
            document.status = DocumentStatus.QUEUED
            document.progress = 0
        return len(stuck)

    def update(self, document: Document) -> None:
        if document.id in self._documents:
            self._documents[document.id] = dataclasses.replace(document)

    def index(self, document: Document, chunks: Sequence[Chunk]) -> None:
        if document.id not in self._documents:
            return
        self.chunks[document.id] = list(chunks)
        self._documents[document.id] = dataclasses.replace(document)
