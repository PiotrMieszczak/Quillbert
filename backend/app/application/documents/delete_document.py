from app.domain.documents import Shelf
from app.domain.shared import NotFound
from app.ports.files import FileStore
from app.ports.repositories import DocumentRepo


class DeleteDocument:
    """Removes the document and its stored file. Its chunks go with it (the foreign
    key cascades)."""

    def __init__(self, files: FileStore, repo: DocumentRepo) -> None:
        self._files = files
        self._repo = repo

    def execute(self, *, shelf: Shelf, document_id: int) -> None:
        document = self._repo.remove(shelf, document_id)
        if document is None:
            raise NotFound("document not found")
        # The row goes first: a file left behind by a failure here is unreachable, not
        # a document pointing at nothing.
        self._files.delete(document.storage_key)
