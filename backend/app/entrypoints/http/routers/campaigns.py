from fastapi import APIRouter, Depends, File, Request, Response, UploadFile

from app.application.campaigns import (
    CreateCampaign,
    GetCampaign,
    GetCampaignImage,
    ListCampaigns,
    ListSystems,
    SetCampaignImage,
)
from app.application.dto import CampaignView
from app.entrypoints.http.auth import require_identity
from app.entrypoints.http.schemas.campaigns import (
    CampaignOut,
    CreateCampaignBody,
    SystemOut,
)
from app.ports.auth import Identity

PREFIX = "/api/v1"
router = APIRouter(prefix=PREFIX)


def _out(view: CampaignView) -> CampaignOut:
    image_url = (
        None
        if view.image_version is None
        # The version changes with the banner, so a cached copy is never stale.
        else f"{PREFIX}/campaigns/{view.id}/image?v={view.image_version}"
    )
    return CampaignOut(
        id=view.id,
        name=view.name,
        system=SystemOut(id=view.system.id, name=view.system.name),
        tint=view.tint,
        imageUrl=image_url,
        sessionCount=view.session_count,
        lastPlayedAt=view.last_played_at,
    )


@router.get("/systems", response_model=list[SystemOut])
def list_systems(
    request: Request, _identity: Identity = Depends(require_identity)
) -> list[SystemOut]:
    systems: ListSystems = request.app.state.list_systems
    return [SystemOut(id=s.id, name=s.name) for s in systems.execute()]


@router.get("/campaigns", response_model=list[CampaignOut])
def list_campaigns(
    request: Request, identity: Identity = Depends(require_identity)
) -> list[CampaignOut]:
    campaigns: ListCampaigns = request.app.state.list_campaigns
    return [_out(view) for view in campaigns.execute(owner_id=identity.user_id)]


@router.post("/campaigns", status_code=201, response_model=CampaignOut)
def create_campaign(
    body: CreateCampaignBody,
    request: Request,
    identity: Identity = Depends(require_identity),
) -> CampaignOut:
    create: CreateCampaign = request.app.state.create_campaign
    view = create.execute(
        owner_id=identity.user_id,
        name=body.name,
        system_id=body.system_id,
        tint=body.tint,
    )
    return _out(view)


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: str, request: Request, identity: Identity = Depends(require_identity)
) -> CampaignOut:
    get: GetCampaign = request.app.state.get_campaign
    return _out(get.execute(owner_id=identity.user_id, campaign_id=campaign_id))


@router.post("/campaigns/{campaign_id}/image", response_model=CampaignOut)
def set_campaign_image(
    campaign_id: str,
    request: Request,
    file: UploadFile = File(),  # noqa: B008 — FastAPI's parameter declaration
    identity: Identity = Depends(require_identity),
) -> CampaignOut:
    set_image: SetCampaignImage = request.app.state.set_campaign_image
    view = set_image.execute(
        owner_id=identity.user_id, campaign_id=campaign_id, content=file.file
    )
    return _out(view)


@router.get("/campaigns/{campaign_id}/image")
def get_campaign_image(
    campaign_id: str, request: Request, identity: Identity = Depends(require_identity)
) -> Response:
    get_image: GetCampaignImage = request.app.state.get_campaign_image
    image = get_image.execute(owner_id=identity.user_id, campaign_id=campaign_id)
    return Response(
        image.data,
        media_type=image.media_type,
        headers={
            "Cache-Control": "private, max-age=31536000, immutable",
            # Only the magic bytes were checked: never let a browser sniff it as more.
            "X-Content-Type-Options": "nosniff",
        },
    )
