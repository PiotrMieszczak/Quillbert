from pydantic import BaseModel, ConfigDict, Field

from app.domain.documents import DocumentKind, DocumentStatus


class DocumentOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, ser_json_by_alias=True)

    id: int
    filename: str
    kind: DocumentKind
    page_count: int | None = Field(alias="pageCount")
    meta: str | None
    status: DocumentStatus
    progress: int
    error: str | None
