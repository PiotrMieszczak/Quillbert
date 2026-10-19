import csv
import io
import shutil
import subprocess

from app.domain.documents import Block

# Tesseract word confidence is 0-100. Below this mean, a page's text is too unreliable
# to cite, so it is left out of the index rather than indexed as noise.
# shortcut: an uncalibrated guess; tune it on the scanned fixtures of the evaluation set
# (ADR-0021 IMP-004).
MIN_CONFIDENCE = 60
_TIMEOUT_SECONDS = 120


class TesseractOcr:
    """OCR through the `tesseract` binary (github.com/tesseract-ocr/tesseract).

    Deterministic for a given binary and language data, so it stays inside BND-001
    (ADR-0002 IMP-005). Reads the TSV output to get per-word confidence.
    """

    def __init__(self, languages: str = "eng+pol", binary: str = "tesseract") -> None:
        self._languages = languages
        self._binary = binary

    @staticmethod
    def available(binary: str = "tesseract") -> bool:
        return shutil.which(binary) is not None

    def read(self, image: bytes) -> tuple[Block, ...]:
        """Paragraphs of one page image (PNG), or () when the page is unreadable."""
        result = subprocess.run(
            [self._binary, "stdin", "stdout", "-l", self._languages, "tsv"],
            input=image,
            capture_output=True,
            timeout=_TIMEOUT_SECONDS,
            check=True,
        )
        return paragraphs(result.stdout.decode("utf-8", errors="replace"))


def paragraphs(tsv: str) -> tuple[Block, ...]:
    """Tesseract TSV to paragraphs, or () when mean confidence is below the floor."""
    lines: dict[tuple[str, str], dict[str, list[str]]] = {}
    weighted = 0.0
    characters = 0
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        word = (row.get("text") or "").strip()
        if row.get("level") != "5" or not word:
            continue
        confidence = float(row["conf"])
        if confidence < 0:
            continue
        weighted += confidence * len(word)
        characters += len(word)
        paragraph = lines.setdefault((row["block_num"], row["par_num"]), {})
        paragraph.setdefault(row["line_num"], []).append(word)
    if not characters or weighted / characters < MIN_CONFIDENCE:
        return ()
    return tuple(
        Block("\n".join(" ".join(words) for words in paragraph.values()))
        for paragraph in lines.values()
    )
