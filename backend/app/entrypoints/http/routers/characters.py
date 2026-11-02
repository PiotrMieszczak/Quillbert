import dataclasses

from fastapi import APIRouter, Depends, Query, Request

from app.application.cast import CreateCharacter, ListCharacters
from app.application.dto import CharacterView
from app.domain.cast import PlayerProfile, Relationship
from app.entrypoints.http.auth import require_campaign
from app.entrypoints.http.schemas.characters import (
    CharacterListItemOut,
    CharacterOut,
    CharacterPageOut,
    CreateCharacterBody,
    PlayerProfileIO,
)

PREFIX = "/api/v1/campaigns/{campaign_id}"
router = APIRouter(prefix=PREFIX, dependencies=[Depends(require_campaign)])


def _fields(view: CharacterView) -> dict:
    profile = view.player_profile
    return {
        "id": view.id,
        "name": view.name,
        "is_player": view.is_player,
        "relationship": view.relationship,
        "role": view.role,
        "level": view.level,
        "location": view.location,
        "tags": list(view.tags),
        # shortcut: always None until the portrait upload route lands (#110).
        "portrait_url": None,
        "player_profile": None
        if profile is None
        else PlayerProfileIO(**dataclasses.asdict(profile)),
        "disposition": view.disposition,
        "last_seen": view.last_seen,
        "stats": view.stats,
        "quote": view.quote,
        "notes": view.notes,
    }


def _out(view: CharacterView) -> CharacterOut:
    return CharacterOut(**_fields(view))


def _item(view: CharacterView) -> CharacterListItemOut:
    # Extra keys are ignored, so the slim row is the detail minus what it omits.
    return CharacterListItemOut(**_fields(view))


@router.post("/characters", status_code=201, response_model=CharacterOut)
def create_character(
    campaign_id: str, body: CreateCharacterBody, request: Request
) -> CharacterOut:
    create: CreateCharacter = request.app.state.create_character
    profile = body.player_profile
    view = create.execute(
        campaign_id=campaign_id,
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
        player_profile=None
        if profile is None
        else PlayerProfile(**profile.model_dump(by_alias=False)),
    )
    return _out(view)


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
        items=[_item(view) for view in page.items],
        nextCursor=page.next_cursor,
    )
