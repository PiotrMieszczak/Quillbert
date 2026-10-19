from dataclasses import dataclass
from datetime import datetime

from app.domain.documents.values import DocumentKind, DocumentSource, DocumentStatus


@dataclass
class Document:
    """A file in a campaign's library. Mirrors docs/data-model.md `document`."""

    id: int
    campaign_id: str
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
