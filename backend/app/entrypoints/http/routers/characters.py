import dataclasses

from fastapi import APIRouter, Depends, File, Query, Request, Response, UploadFile

from app.application.cast import (
    CreateCharacter,
    DeleteCharacter,
    GetCharacter,
    GetCharacterPortrait,
    ListCharacters,
    SetCharacterPortrait,
    UpdateCharacter,
)
from app.application.dto import CharacterView
from app.domain.cast import PlayerProfile, Relationship
from app.entrypoints.http.auth import require_campaign
from app.entrypoints.http.schemas.characters import (
    CharacterListItemOut,
    CharacterOut,
    CharacterPageOut,
    CreateCharacterBody,
    PlayerProfileIO,
    UpdateCharacterBody,
)

PREFIX = "/api/v1/campaigns/{campaign_id}"
router = APIRouter(prefix=PREFIX, dependencies=[Depends(require_campaign)])


def _fields(campaign_id: str, view: CharacterView) -> dict:
    profile = view.player_profile
    version = view.portrait_version
    portrait = f"/api/v1/campaigns/{campaign_id}/characters/{view.id}/portrait"
    return {
        "id": view.id,
        "name": view.name,
        "is_player": view.is_player,
        "relationship": view.relationship,
        "role": view.role,
        "level": view.level,
        "location": view.location,
        "tags": list(view.tags),
        # The version changes with the portrait, so a cached copy is never stale.
        "portrait_url": None if version is None else f"{portrait}?v={version}",
        "player_profile": None
        if profile is None
        else PlayerProfileIO(**dataclasses.asdict(profile)),
        "disposition": view.disposition,
        "last_seen": view.last_seen,
        "stats": view.stats,
        "quote": view.quote,
        "notes": view.notes,
        "bio": view.bio,
    }


def _out(campaign_id: str, view: CharacterView) -> CharacterOut:
    return CharacterOut(**_fields(campaign_id, view))


def _item(campaign_id: str, view: CharacterView) -> CharacterListItemOut:
    # Extra keys are ignored, so the slim row is the detail minus what it omits.
    return CharacterListItemOut(**_fields(campaign_id, view))


@router.post("/characters", status_code=201, response_model=CharacterOut)
def create_character(
    campaign_id: str, body: CreateCharacterBody, request: Request
) -> CharacterOut:
    create: CreateCharacter = request.app.state.create_character
    profile = body.player_profile
    view = create.execute(
        campaign_id=campaign_id,
        system_id=request.state.campaign.system.id,
        name=body.name,
        is_player=body.is_player,
        relationship=body.relationship,
        role=body.role,
        level=body.level,
        location=body.location,
        disposition=body.disposition,
        last_seen=body.last_seen,
        stats=body.stats,
        tags=body.tags,
        quote=body.quote,
        notes=body.notes,
        bio=body.bio,
        player_profile=None
        if profile is None
        else PlayerProfile(**profile.model_dump(by_alias=False)),
    )
    return _out(campaign_id, view)


@router.get("/characters", response_model=CharacterPageOut)
def list_characters(
    campaign_id: str,
    request: Request,
    is_player: bool | None = Query(None, alias="isPlayer"),
    relationship: Relationship | None = None,
    q: str | None = Query(None, max_length=120),
    cursor: str | None = Query(None, max_length=512),
    limit: int = Query(50, ge=1, le=200),
) -> CharacterPageOut:
    characters: ListCharacters = request.app.state.list_characters
    page = characters.execute(
        campaign_id=campaign_id,
        is_player=is_player,
        relationship=relationship,
        q=q,
        cursor=cursor,
        limit=limit,
    )
    return CharacterPageOut(
        items=[_item(campaign_id, view) for view in page.items],
        nextCursor=page.next_cursor,
    )


@router.get("/characters/{character_id}", response_model=CharacterOut)
def get_character(
    campaign_id: str, character_id: int, request: Request
) -> CharacterOut:
    get: GetCharacter = request.app.state.get_character
    view = get.execute(campaign_id=campaign_id, character_id=character_id)
    return _out(campaign_id, view)


@router.patch("/characters/{character_id}", response_model=CharacterOut)
def update_character(
    campaign_id: str, character_id: int, body: UpdateCharacterBody, request: Request
) -> CharacterOut:
    update: UpdateCharacter = request.app.state.update_character
    # Only what the client sent: an omitted field is kept, null clears it.
    changes = body.model_dump(exclude_unset=True)
    if changes.get("player_profile") is not None:
        changes["player_profile"] = PlayerProfile(**changes["player_profile"])
    view = update.execute(
        campaign_id=campaign_id,
        system_id=request.state.campaign.system.id,
        character_id=character_id,
        changes=changes,
    )
    return _out(campaign_id, view)


@router.delete("/characters/{character_id}", status_code=204)
def delete_character(campaign_id: str, character_id: int, request: Request) -> Response:
    delete: DeleteCharacter = request.app.state.delete_character
    delete.execute(campaign_id=campaign_id, character_id=character_id)
    return Response(status_code=204)


@router.post("/characters/{character_id}/portrait", response_model=CharacterOut)
def set_character_portrait(
    campaign_id: str,
    character_id: int,
    request: Request,
    file: UploadFile = File(),  # noqa: B008 — FastAPI's parameter declaration
) -> CharacterOut:
    set_portrait: SetCharacterPortrait = request.app.state.set_character_portrait
    view = set_portrait.execute(
        campaign_id=campaign_id, character_id=character_id, content=file.file
    )
    return _out(campaign_id, view)


@router.get("/characters/{character_id}/portrait")
def get_character_portrait(
    campaign_id: str, character_id: int, request: Request
) -> Response:
    get_portrait: GetCharacterPortrait = request.app.state.get_character_portrait
    image = get_portrait.execute(campaign_id=campaign_id, character_id=character_id)
    return Response(
        image.data,
        media_type=image.media_type,
        headers={
            "Cache-Control": "private, max-age=31536000, immutable",
            # Only the magic bytes were checked: never let a browser sniff it as more.
            "X-Content-Type-Options": "nosniff",
        },
    )
