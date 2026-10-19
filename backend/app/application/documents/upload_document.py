from pathlib import PurePosixPath
from typing import BinaryIO

from app.application.documents.views import document_view
from app.application.dto import UploadResult
from app.domain.documents import SNIFF_BYTES, Document, classify
from app.domain.shared import ValidationFailed
from app.ports.clock import Clock
from app.ports.files import FileStore
from app.ports.repositories import DocumentRepo

MAX_FILENAME = 255


class UploadDocument:
    def __init__(
        self, files: FileStore, repo: DocumentRepo, clock: Clock, *, max_bytes: int
    ) -> None:
        self._files = files
        self._repo = repo
        self._clock = clock
        self._max_bytes = max_bytes

    def execute(
        self, *, campaign_id: str, filename: str, content: BinaryIO
    ) -> UploadResult:
        if not campaign_id.strip():
            raise ValidationFailed("campaign_id is required")
        name = _clean_filename(filename)
        kind = classify(name, content.read(SNIFF_BYTES))
        content.seek(0)

        stored = self._files.put(content, max_bytes=self._max_bytes)
        try:
            existing = self._repo.find_by_sha256(campaign_id, stored.sha256)
            if existing is not None:
                # Same bytes already in this campaign: keep that one, store nothing new.
                self._files.delete(stored.key)
                return UploadResult(document_view(existing), created=False)

            # shortcut: two identical uploads racing both pass the check above and the
            # second hits the unique (campaign_id, sha256) index; upgrade by catching it
            # and returning the winner.
            document = Document(
                id=self._repo.next_document_id(),
                campaign_id=campaign_id,
                filename=name,
                kind=kind,
                sha256=stored.sha256,
                storage_key=stored.key,
                uploaded_at=self._clock.now(),
            )
            self._repo.add(document)
        except Exception:
            self._files.delete(stored.key)
            raise
        return UploadResult(document_view(document), created=True)


def _clean_filename(filename: str) -> str:
    """The bare file name: browsers may send a path, and a name is never a path."""
    name = PurePosixPath(filename.replace("\\", "/")).name.strip()
    if not name or any(ord(char) < 32 for char in name):
        raise ValidationFailed("a file name is required")
    if len(name) > MAX_FILENAME:
        raise ValidationFailed(f"file name is longer than {MAX_FILENAME} characters")
    return name
