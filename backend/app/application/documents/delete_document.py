from app.domain.shared import NotFound
from app.ports.files import FileStore
from app.ports.repositories import DocumentRepo


class DeleteDocument:
    """Removes the document and its stored file. Chunks and index rows go with it once
    extraction exists (their foreign key cascades)."""

    def __init__(self, files: FileStore, repo: DocumentRepo) -> None:
        self._files = files
        self._repo = repo

    def execute(self, *, campaign_id: str, document_id: int) -> None:
        document = self._repo.remove(campaign_id, document_id)
        if document is None:
            raise NotFound("document not found")
        # The row goes first: a file left behind by a failure here is unreachable, not
        # a document pointing at nothing.
        self._files.delete(document.storage_key)
