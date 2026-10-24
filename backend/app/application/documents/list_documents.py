from app.application.documents.views import document_view
from app.application.dto import DocumentView
from app.domain.documents import Shelf
from app.domain.shared import ValidationFailed
from app.ports.repositories import DocumentRepo


class ListDocuments:
    def __init__(self, repo: DocumentRepo) -> None:
        self._repo = repo

    def execute(self, *, shelf: Shelf) -> list[DocumentView]:
        if shelf.campaign_id is not None and not shelf.campaign_id.strip():
            raise ValidationFailed("campaign_id is required")
        return [document_view(document) for document in self._repo.list_shelf(shelf)]
