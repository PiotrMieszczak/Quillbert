from dataclasses import dataclass
from enum import StrEnum


class DocumentKind(StrEnum):
    PDF = "PDF"
    DOC = "DOC"
    IMG = "IMG"


class DocumentStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    # A scan with no extractable text. Not a failure (ADR-0021 IMP-007).
    AWAITING_OCR = "awaiting_ocr"


class DocumentSource(StrEnum):
    UPLOAD = "upload"
    GOOGLE_DRIVE = "google_drive"


@dataclass(frozen=True)
class Shelf:
    """Where a document lives (ADR-0027): a campaign, a GM's library, or the vault."""

    campaign_id: str | None = None
    owner_id: str | None = None

    @classmethod
    def campaign(cls, campaign_id: str) -> "Shelf":
        return cls(campaign_id=campaign_id)

    @classmethod
    def gm(cls, owner_id: str) -> "Shelf":
        return cls(owner_id=owner_id)

    @classmethod
    def vault(cls) -> "Shelf":
        return cls()
