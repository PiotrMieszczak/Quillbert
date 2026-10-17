from app.application.dto import DocumentView
from app.domain.documents import Document


def document_view(document: Document) -> DocumentView:
    return DocumentView(
        id=document.id,
        filename=document.filename,
        kind=document.kind,
        page_count=document.page_count,
        meta=document.meta,
        status=document.status,
        progress=document.progress,
        error=document.error,
    )
