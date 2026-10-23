from dataclasses import dataclass
from datetime import datetime

from app.domain.documents.values import (
    DocumentKind,
    DocumentSource,
    DocumentStatus,
    Shelf,
)


@dataclass
class Document:
    """A file on a shelf: a campaign or a GM's library (ADR-0027).
    Mirrors docs/data-model.md `document`."""

    id: int
    # Set for a campaign document; owner_id instead for a GM's library.
    campaign_id: str | None
    filename: str
    kind: DocumentKind
    sha256: str
    # Opaque key into the FileStore: a path locally, an object key when hosted.
    storage_key: str
    uploaded_at: datetime
    status: DocumentStatus = DocumentStatus.QUEUED
    progress: int = 0
    page_count: int | None = None
    meta: str | None = None
    error: str | None = None
    source: DocumentSource = DocumentSource.UPLOAD
    source_ref: str | None = None
    owner_id: str | None = None
    # Systems a library document applies to; empty means all.
    systems: tuple[str, ...] = ()

    @property
    def shelf(self) -> Shelf:
        return Shelf(self.campaign_id, self.owner_id)
