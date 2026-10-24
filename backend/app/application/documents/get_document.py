from app.application.documents.views import document_view
from app.application.dto import DocumentView
from app.domain.documents import Shelf
from app.domain.shared import NotFound
from app.ports.repositories import DocumentRepo


class GetDocument:
    def __init__(self, repo: DocumentRepo) -> None:
        self._repo = repo

    def execute(self, *, shelf: Shelf, document_id: int) -> DocumentView:
        document = self._repo.get(shelf, document_id)
        if document is None:
            raise NotFound("document not found")
        return document_view(document)
