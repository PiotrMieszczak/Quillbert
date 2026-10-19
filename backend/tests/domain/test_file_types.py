import pytest
from app.domain.documents import SNIFF_BYTES, DocumentKind, classify
from app.domain.shared import UnsupportedFileType, ValidationFailed

PDF = b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n"
DOCX = b"PK\x03\x04\x14\x00\x06\x00"
OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 24


@pytest.mark.parametrize(
    ("filename", "head", "kind"),
    [
        ("Core Rulebook.pdf", PDF, DocumentKind.PDF),
        ("SHOUTING.PDF", PDF, DocumentKind.PDF),
        ("module.docx", DOCX, DocumentKind.DOC),
        ("House Rules.md", "# Rules\n\nŁódź is a city.\n".encode(), DocumentKind.DOC),
        ("notes.txt", b"plain notes", DocumentKind.DOC),
    ],
)
def test_accepts_files_whose_content_matches_the_extension(
    filename: str, head: bytes, kind: DocumentKind
) -> None:
    assert classify(filename, head) is kind


@pytest.mark.parametrize(
    "filename", ["old.doc", "photo.png", "archive.zip", "noextension", "trailingdot."]
)
def test_rejects_other_extensions(filename: str) -> None:
    with pytest.raises(UnsupportedFileType):
        classify(filename, PDF)


@pytest.mark.parametrize(
    ("filename", "head"),
    [
        ("fake.pdf", b"just text"),
        ("fake.docx", b"%PDF-1.7"),
        ("renamed-doc.txt", OLE),
        ("binary.md", b"abc\x00def"),
        ("latin1.txt", "zażółć".encode("cp1250")),
    ],
)
def test_rejects_content_that_does_not_match_the_extension(
    filename: str, head: bytes
) -> None:
    with pytest.raises(UnsupportedFileType):
        classify(filename, head)


def test_rejects_an_empty_file() -> None:
    with pytest.raises(ValidationFailed):
        classify("empty.txt", b"")


def test_a_character_cut_by_the_sniff_window_is_still_text() -> None:
    text = ("a" * (SNIFF_BYTES - 1)) + "ł"  # the 2-byte "ł" straddles the cut
    head = text.encode()[:SNIFF_BYTES]
    assert classify("long.md", head) is DocumentKind.DOC
