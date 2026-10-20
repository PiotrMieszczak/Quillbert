from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SystemOut(BaseModel):
    id: str
    name: str


class CreateCampaignBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    system_id: str = Field(alias="systemId")
    tint: str | None = None


class CampaignOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    id: str
    name: str
    system: SystemOut
    tint: str
    image_url: str | None = Field(alias="imageUrl")
    session_count: int = Field(alias="sessionCount")
    last_played_at: date | None = Field(alias="lastPlayedAt")
