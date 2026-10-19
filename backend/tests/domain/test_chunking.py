from app.domain.documents import Block, Page, chunk_pages
from app.domain.documents.chunking import OVERLAP_CHARS, TARGET_CHARS


def _page(number: int, *texts: str, heading: str | None = None) -> Page:
    blocks = ([Block(heading, heading=True)] if heading else []) + [
        Block(text) for text in texts
    ]
    return Page(number, tuple(blocks))


def _words(n: int) -> str:
    """Body text that differs page to page in letters, not just numbers."""
    return " ".join(chr(97 + (n * 7 + i) % 26) * 3 for i in range(12)) + "."


def test_watermarks_headers_and_page_numbers_are_dropped() -> None:
    pages = [
        Page(
            n,
            (
                Block("Pirates of Drinax"),
                Block(f"{_words(n)}\n{_words(n + 1)}\n{_words(n + 2)}"),
                Block(f"{_words(n + 3)}\n{_words(n + 4)}"),
                Block("Jane Doe - Order #48213"),
                Block(str(n)),
            ),
        )
        for n in range(1, 7)
    ]

    content = "\n\n".join(chunk.content for chunk in chunk_pages(pages))

    assert "Order" not in content
    assert "Drinax" not in content
    assert _words(3) in content
    assert not any(line.strip().isdigit() for line in content.split("\n\n"))


def test_short_documents_keep_every_line() -> None:
    pages = [_page(1, "Order #1", "Rule.")]

    assert chunk_pages(pages)[0].content == "Order #1\n\nRule."


def test_chunks_stay_near_target_and_overlap() -> None:
    pages = [
        _page(n, *(f"{_words(n + i)} " * 8 for i in range(3))) for n in range(1, 11)
    ]

    chunks = chunk_pages(pages)

    assert len(chunks) > 1
    assert all(len(c.content) <= TARGET_CHARS + OVERLAP_CHARS + 4 for c in chunks)
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    for previous, chunk in zip(chunks, chunks[1:], strict=False):
        carried = chunk.content.split("\n\n")[0]
        assert 0 < len(carried) <= OVERLAP_CHARS
        assert previous.content.endswith(carried)


def test_chunks_record_pages_and_the_heading_in_effect() -> None:
    pages = [
        _page(1, "Intro words.", heading="Skills"),
        _page(2, "More about skills."),
        _page(3, "Ships move.", heading="Spacecraft"),
    ]

    (chunk,) = chunk_pages(pages)

    assert (chunk.page_from, chunk.page_to, chunk.heading) == (1, 3, "Skills")


def test_an_oversized_paragraph_is_split_at_sentences() -> None:
    text = "Short sentence here. " * 300

    chunks = chunk_pages([_page(1, text)])

    assert len(chunks) > 1
    assert all(c.content.endswith(".") for c in chunks)


def test_hyphenated_line_breaks_are_rejoined() -> None:
    (chunk,) = chunk_pages([_page(1, "The star-\nship and the work-\nshop.")])

    assert chunk.content == "The starship and the workshop."


def test_same_pages_give_same_chunks() -> None:
    pages = [_page(n, f"Paragraph {n}. " * 40) for n in range(1, 8)]

    assert chunk_pages(pages) == chunk_pages(pages)


def test_no_text_gives_no_chunks() -> None:
    assert chunk_pages([Page(1, ()), Page(2, (Block("   "),))]) == []
