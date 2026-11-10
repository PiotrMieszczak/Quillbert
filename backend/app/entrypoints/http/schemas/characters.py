from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.cast import Relationship

# Short labels shown on cards; long ones are free text on the detail page.
SHORT = 120
LONG = 2_000


class PlayerProfileIO(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    player_name: str | None = Field(None, alias="playerName", max_length=SHORT)
    # `class` is a Python keyword.
    character_class: str | None = Field(None, alias="class", max_length=SHORT)
    race: str | None = Field(None, max_length=SHORT)
    background: str | None = Field(None, max_length=SHORT)
    xp: str | None = Field(None, max_length=SHORT)
    pronouns: str | None = Field(None, max_length=SHORT)
    bonds: str | None = Field(None, max_length=LONG)


class CreateCharacterBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    is_player: bool = Field(False, alias="isPlayer")
    relationship: Relationship = Relationship.NEUTRAL
    role: str | None = Field(None, max_length=SHORT)
    level: int | None = None
    location: str | None = Field(None, max_length=SHORT)
    disposition: str | None = Field(None, max_length=SHORT)
    last_seen: str | None = Field(None, alias="lastSeen", max_length=SHORT)
    stats: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    quote: str | None = Field(None, max_length=LONG)
    notes: str | None = Field(None, max_length=20_000)
    player_profile: PlayerProfileIO | None = Field(None, alias="playerProfile")


class UpdateCharacterBody(BaseModel):
    """Every field optional: an omitted field is kept, one sent as null is cleared."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = None
    is_player: bool | None = Field(None, alias="isPlayer")
    relationship: Relationship | None = None
    role: str | None = Field(None, max_length=SHORT)
    level: int | None = None
    location: str | None = Field(None, max_length=SHORT)
    disposition: str | None = Field(None, max_length=SHORT)
    last_seen: str | None = Field(None, alias="lastSeen", max_length=SHORT)
    stats: dict[str, Any] | None = None
    tags: list[str] | None = None
    quote: str | None = Field(None, max_length=LONG)
    notes: str | None = Field(None, max_length=20_000)
    player_profile: PlayerProfileIO | None = Field(None, alias="playerProfile")


class CharacterListItemOut(BaseModel):
    """What a card shows. Stats, notes and connections come only with the detail."""

    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    id: int
    name: str
    is_player: bool = Field(alias="isPlayer")
    relationship: Relationship
    role: str | None
    level: int | None
    location: str | None
    tags: list[str]
    portrait_url: str | None = Field(alias="portraitUrl")
    player_profile: PlayerProfileIO | None = Field(alias="playerProfile")


class CharacterOut(CharacterListItemOut):
    disposition: str | None
    last_seen: str | None = Field(alias="lastSeen")
    stats: dict[str, Any]
    quote: str | None
    notes: str | None


class CharacterPageOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    items: list[CharacterListItemOut]
    next_cursor: str | None = Field(alias="nextCursor")
