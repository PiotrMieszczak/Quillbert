"""Which files a library accepts: the extension picks the kind, the bytes must agree."""

from app.domain.documents.values import DocumentKind
from app.domain.shared import UnsupportedFileType, ValidationFailed

# How much of a file classify() needs to see.
SNIFF_BYTES = 8192

# Legacy .doc is out: it is the OLE container below, and the extractor reads .docx only.
ALLOWED: dict[str, DocumentKind] = {
    ".pdf": DocumentKind.PDF,
    ".md": DocumentKind.DOC,
    ".txt": DocumentKind.DOC,
    ".docx": DocumentKind.DOC,
}
_OLE_HEADER = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"


def classify(filename: str, head: bytes) -> DocumentKind:
    """The kind `filename` is, or UnsupportedFileType. `head` is its first bytes."""
    extension = _extension(filename)
    kind = ALLOWED.get(extension)
    if kind is None:
        allowed = ", ".join(ALLOWED)
        shown = extension or "(none)"
        raise UnsupportedFileType(f"unsupported file type {shown}; allowed: {allowed}")
    if not head:
        raise ValidationFailed("file is empty")
    if not _matches(extension, head):
        raise UnsupportedFileType(f"file content is not a valid {extension} file")
    return kind


def _extension(filename: str) -> str:
    _, dot, extension = filename.rpartition(".")
    return f".{extension.lower()}" if dot else ""


def _matches(extension: str, head: bytes) -> bool:
    if extension == ".pdf":
        return head.startswith(b"%PDF-")
    if extension == ".docx":
        return head.startswith(b"PK\x03\x04")
    return _is_text(head)


def _is_text(head: bytes) -> bool:
    if b"\x00" in head or head.startswith(_OLE_HEADER):
        return False
    try:
        head.decode("utf-8")
    except UnicodeDecodeError as error:
        # A full-size head can end inside a multi-byte character; a bad byte earlier
        # than that is not text.
        return len(head) == SNIFF_BYTES and error.start >= len(head) - 3
    return True
