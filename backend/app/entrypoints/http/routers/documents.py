from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile

from app.application.documents import (
    DeleteDocument,
    GetDocument,
    ListDocuments,
    UploadDocument,
)
from app.application.dto import DocumentView
from app.domain.documents import Shelf
from app.domain.shared import ValidationFailed
from app.entrypoints.http.auth import require_admin, require_campaign, require_identity
from app.entrypoints.http.schemas.documents import DocumentOut
from app.ports.auth import Identity

# Three shelves, one set of handlers (ADR-0027): a campaign's documents, the caller's
# own library, and the vault (everyone reads it, only an admin writes it).
router = APIRouter(
    prefix="/api/v1/campaigns/{campaign_id}", dependencies=[Depends(require_campaign)]
)
library_router = APIRouter(prefix="/api/v1/library")
vault_router = APIRouter(prefix="/api/v1/vault")


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
        systems=list(view.systems),
        attribution=view.attribution,
    )


def _systems(request: Request, raw: str) -> tuple[str, ...]:
    """Comma-separated system ids from the form; each must be a known system."""
    wanted = tuple(part.strip() for part in raw.split(",") if part.strip())
    known = {system.id for system in request.app.state.list_systems.execute()}
    unknown = [system for system in wanted if system not in known]
    if unknown:
        raise ValidationFailed(f"unknown system: {', '.join(unknown)}")
    return wanted


def _upload(
    request: Request,
    response: Response,
    shelf: Shelf,
    file: UploadFile,
    systems: tuple[str, ...] = (),
    attribution: str | None = None,
) -> DocumentOut:
    upload: UploadDocument = request.app.state.upload_document
    result = upload.execute(
        shelf=shelf,
        filename=file.filename or "",
        content=file.file,
        systems=systems,
        attribution=attribution,
    )
    if not result.created:
        # The same bytes were already on this shelf: that document, nothing new.
        response.status_code = 200
    return _out(result.document)


def _list(request: Request, shelf: Shelf) -> list[DocumentOut]:
    documents: ListDocuments = request.app.state.list_documents
    return [_out(view) for view in documents.execute(shelf=shelf)]


def _get(request: Request, shelf: Shelf, document_id: int) -> DocumentOut:
    document: GetDocument = request.app.state.get_document
    return _out(document.execute(shelf=shelf, document_id=document_id))


def _delete(request: Request, shelf: Shelf, document_id: int) -> Response:
    delete: DeleteDocument = request.app.state.delete_document
    delete.execute(shelf=shelf, document_id=document_id)
    return Response(status_code=204)


# --- a campaign's documents -----------------------------------------------------


@router.post("/documents", status_code=202, response_model=DocumentOut)
def upload_document(
    campaign_id: str,
    request: Request,
    response: Response,
    file: UploadFile = File(),  # noqa: B008 — FastAPI's parameter declaration
) -> DocumentOut:
    return _upload(request, response, Shelf.campaign(campaign_id), file)


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(campaign_id: str, request: Request) -> list[DocumentOut]:
    return _list(request, Shelf.campaign(campaign_id))


@router.get("/documents/{document_id}", response_model=DocumentOut)
def get_document(campaign_id: str, document_id: int, request: Request) -> DocumentOut:
    return _get(request, Shelf.campaign(campaign_id), document_id)


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(campaign_id: str, document_id: int, request: Request) -> Response:
    return _delete(request, Shelf.campaign(campaign_id), document_id)


# --- the caller's library: every campaign of theirs reads it ----------------------


@library_router.post("/documents", status_code=202, response_model=DocumentOut)
def upload_library_document(
    request: Request,
    response: Response,
    file: UploadFile = File(),  # noqa: B008
    systems: str = Form(""),
    identity: Identity = Depends(require_identity),  # noqa: B008
) -> DocumentOut:
    shelf = Shelf.gm(identity.user_id)
    return _upload(request, response, shelf, file, _systems(request, systems))


@library_router.get("/documents", response_model=list[DocumentOut])
def list_library_documents(
    request: Request,
    identity: Identity = Depends(require_identity),  # noqa: B008
) -> list[DocumentOut]:
    return _list(request, Shelf.gm(identity.user_id))


@library_router.delete("/documents/{document_id}", status_code=204)
def delete_library_document(
    document_id: int,
    request: Request,
    identity: Identity = Depends(require_identity),  # noqa: B008
) -> Response:
    return _delete(request, Shelf.gm(identity.user_id), document_id)


# --- the vault: read by every GM, written by an admin -------------------------------


@vault_router.post(
    "/documents",
    status_code=202,
    response_model=DocumentOut,
    dependencies=[Depends(require_admin)],
)
def upload_vault_document(
    request: Request,
    response: Response,
    file: UploadFile = File(),  # noqa: B008
    systems: str = Form(""),
    attribution: str = Form(""),
) -> DocumentOut:
    return _upload(
        request,
        response,
        Shelf.vault(),
        file,
        _systems(request, systems),
        attribution,
    )


@vault_router.get(
    "/documents",
    response_model=list[DocumentOut],
    dependencies=[Depends(require_identity)],
)
def list_vault_documents(request: Request) -> list[DocumentOut]:
    return _list(request, Shelf.vault())


@vault_router.delete(
    "/documents/{document_id}",
    status_code=204,
    dependencies=[Depends(require_admin)],
)
def delete_vault_document(document_id: int, request: Request) -> Response:
    return _delete(request, Shelf.vault(), document_id)
