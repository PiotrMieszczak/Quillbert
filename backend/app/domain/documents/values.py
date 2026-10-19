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
