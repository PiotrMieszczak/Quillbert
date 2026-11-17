from fastapi import APIRouter, Depends, Request
from pydantic import ConfigDict, Field

from app.application.sheets import GetSheet, SaveSheet
from app.domain.sheets import Sheet
from app.entrypoints.http.auth import require_admin, require_identity
from app.ports.auth import Identity

router = APIRouter(prefix="/api/v1")


class SheetOut(Sheet):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    system_id: str = Field(alias="systemId")


def _out(system_id: str, sheet: Sheet) -> SheetOut:
    return SheetOut(system_id=system_id, **sheet.model_dump())


@router.get(
    "/systems/{system_id}/sheet",
    response_model=SheetOut,
    response_model_exclude_none=True,
)
def get_sheet(
    system_id: str, request: Request, _identity: Identity = Depends(require_identity)
) -> SheetOut:
    get: GetSheet = request.app.state.get_sheet
    return _out(system_id, get.execute(system_id=system_id))


# shortcut: no POST /admin/sheets/{system_id}/draft yet; it needs the vault source
# (#125) and Gateway complete_json. Until then an admin writes the sheet by hand.
@router.put(
    "/admin/sheets/{system_id}",
    response_model=SheetOut,
    response_model_exclude_none=True,
)
def save_sheet(
    system_id: str,
    body: Sheet,
    request: Request,
    identity: Identity = Depends(require_admin),
) -> SheetOut:
    save: SaveSheet = request.app.state.save_sheet
    saved = save.execute(system_id=system_id, sheet=body, saved_by=identity.user_id)
    return _out(system_id, saved)
