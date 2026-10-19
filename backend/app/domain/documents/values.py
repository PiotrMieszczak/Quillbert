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


class DocumentSource(StrEnum):
    UPLOAD = "upload"
    GOOGLE_DRIVE = "google_drive"
