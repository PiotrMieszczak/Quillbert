from pydantic import BaseModel, Field

from app.domain.cast import Relationship
from app.entrypoints.http.schemas.characters import LONG, SHORT


class CreateFactionBody(BaseModel):
    name: str
    relationship: Relationship = Relationship.NEUTRAL
    type: str | None = Field(None, max_length=SHORT)
    influence: str | None = Field(None, max_length=SHORT)
    reach: str | None = Field(None, max_length=SHORT)
    motto: str | None = Field(None, max_length=LONG)
    goal: str | None = Field(None, max_length=LONG)
    notes: str | None = Field(None, max_length=20_000)


class UpdateFactionBody(BaseModel):
    """Every field optional: an omitted field is kept, one sent as null is cleared."""

    name: str | None = None
    relationship: Relationship | None = None
    type: str | None = Field(None, max_length=SHORT)
    influence: str | None = Field(None, max_length=SHORT)
    reach: str | None = Field(None, max_length=SHORT)
    motto: str | None = Field(None, max_length=LONG)
    goal: str | None = Field(None, max_length=LONG)
    notes: str | None = Field(None, max_length=20_000)


class FactionOut(BaseModel):
    id: int
    name: str
    relationship: Relationship
    type: str | None
    influence: str | None
    reach: str | None
    motto: str | None
    goal: str | None
    notes: str | None
