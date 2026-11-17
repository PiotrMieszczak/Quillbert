import dataclasses

from fastapi import APIRouter, Depends, Request, Response

from app.application.cast import (
    CreateFaction,
    DeleteFaction,
    GetFaction,
    ListFactions,
    UpdateFaction,
)
from app.domain.cast import Faction
from app.entrypoints.http.auth import require_campaign
from app.entrypoints.http.schemas.factions import (
    CreateFactionBody,
    FactionOut,
    UpdateFactionBody,
)

router = APIRouter(
    prefix="/api/v1/campaigns/{campaign_id}", dependencies=[Depends(require_campaign)]
)


def _out(faction: Faction) -> FactionOut:
    # Extra keys (campaign_id) are ignored.
    return FactionOut(**dataclasses.asdict(faction))


@router.post("/factions", status_code=201, response_model=FactionOut)
def create_faction(
    campaign_id: str, body: CreateFactionBody, request: Request
) -> FactionOut:
    create: CreateFaction = request.app.state.create_faction
    return _out(create.execute(campaign_id=campaign_id, **body.model_dump()))


# shortcut: unpaged; a campaign has a handful of factions. Page it like characters
# if one ever holds hundreds.
@router.get("/factions", response_model=list[FactionOut])
def list_factions(campaign_id: str, request: Request) -> list[FactionOut]:
    factions: ListFactions = request.app.state.list_factions
    return [_out(faction) for faction in factions.execute(campaign_id=campaign_id)]


@router.get("/factions/{faction_id}", response_model=FactionOut)
def get_faction(campaign_id: str, faction_id: int, request: Request) -> FactionOut:
    get: GetFaction = request.app.state.get_faction
    return _out(get.execute(campaign_id=campaign_id, faction_id=faction_id))


@router.patch("/factions/{faction_id}", response_model=FactionOut)
def update_faction(
    campaign_id: str, faction_id: int, body: UpdateFactionBody, request: Request
) -> FactionOut:
    update: UpdateFaction = request.app.state.update_faction
    # Only what the client sent: an omitted field is kept, null clears it.
    changes = body.model_dump(exclude_unset=True)
    return _out(
        update.execute(campaign_id=campaign_id, faction_id=faction_id, changes=changes)
    )


@router.delete("/factions/{faction_id}", status_code=204)
def delete_faction(campaign_id: str, faction_id: int, request: Request) -> Response:
    delete: DeleteFaction = request.app.state.delete_faction
    delete.execute(campaign_id=campaign_id, faction_id=faction_id)
    return Response(status_code=204)
