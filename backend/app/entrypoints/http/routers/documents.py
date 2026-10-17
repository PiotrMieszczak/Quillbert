from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from app.application.documents import GetDocument, ListDocuments, UploadDocument
from app.application.dto import DocumentView
from app.entrypoints.http.auth import require_identity
from app.entrypoints.http.schemas.documents import DocumentOut

router = APIRouter(
    prefix="/api/v1/campaigns/{campaign_id}", dependencies=[Depends(require_identity)]
)


def _upload(request: Request) -> UploadDocument:
    return request.app.state.upload_document


def _list(request: Request) -> ListDocuments:
    return request.app.state.list_documents


def _get(request: Request) -> GetDocument:
    return request.app.state.get_document


def _out(view: DocumentView) -> DocumentOut:
    return DocumentOut(
        id=view.id,
        filename=view.filename,
        kind=view.kind,
        pageCount=view.page_count,
        meta=view.meta,
        status=view.status,
        progress=view.progress,
        error=view.error,
    )


@router.post("/documents", status_code=202, response_model=DocumentOut)
def upload_document(
    campaign_id: str,
    request: Request,
    response: Response,
    file: UploadFile = File(),  # noqa: B008 — FastAPI's parameter declaration
) -> DocumentOut:
    result = _upload(request).execute(
        campaign_id=campaign_id, filename=file.filename or "", content=file.file
    )
    if not result.created:
        # The same bytes were already in this campaign: that document, nothing new.
        response.status_code = 200
    return _out(result.document)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(campaign_id: str, request: Request) -> list[DocumentOut]:
    return [_out(view) for view in _list(request).execute(campaign_id=campaign_id)]


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(campaign_id: str, document_id: int, request: Request) -> DocumentOut:
    return _out(_get(request).execute(campaign_id=campaign_id, document_id=document_id))
