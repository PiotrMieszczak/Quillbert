"""Which banner images a campaign accepts: the bytes decide, not the file name."""

from app.domain.shared import UnsupportedFileType, ValidationFailed

SNIFF_BYTES = 16


def image_type(head: bytes) -> str:
    """The media type of the image starting with `head`, or UnsupportedFileType."""
    if not head:
        raise ValidationFailed("file is empty")
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"
    raise UnsupportedFileType("banner must be a PNG, JPEG or WebP image")
