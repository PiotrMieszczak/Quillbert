from dataclasses import dataclass
from datetime import date, datetime

from app.domain.assistant import Citation, Mode, Role
from app.domain.campaigns import System
from app.domain.documents import DocumentKind, DocumentStatus


@dataclass(frozen=True)
class ConversationView:
    id: int
    campaign_id: str
    mode: Mode
    started_at: datetime


@dataclass(frozen=True)
class MessageView:
    id: int
    role: Role
    content: str
    created_at: datetime
    mode: Mode
    tool_label: str | None
    citations: tuple[Citation, ...] = ()
    # The reply is the refusal: nothing in the material answered it.
    refused: bool = False


@dataclass(frozen=True)
class CampaignView:
    id: str
    name: str
    system: System
    tint: str
    # Changes whenever the banner does; None when there is no banner.
    image_version: str | None
    session_count: int
    last_played_at: date | None


@dataclass(frozen=True)
class CampaignImage:
    data: bytes
    media_type: str


@dataclass(frozen=True)
class DocumentView:
    id: int
    filename: str
    kind: DocumentKind
    page_count: int | None
    meta: str | None
    status: DocumentStatus
    progress: int
    error: str | None
    systems: tuple[str, ...] = ()


@dataclass(frozen=True)
class UploadResult:
    document: DocumentView
    # False when the campaign already had these bytes and that document is returned.
    created: bool


@dataclass(frozen=True)
class TurnStarted:
    conversation_id: int
    run_id: str
    message_id: int


@dataclass(frozen=True)
class TurnSearched:
    """The retrieval step ran; `result` is the line the tool chip shows."""

    query: str
    result: str


@dataclass(frozen=True)
class TurnDelta:
    message_id: int
    text: str


@dataclass(frozen=True)
class TurnFinished:
    conversation_id: int
    run_id: str
    message_id: int


@dataclass(frozen=True)
class TurnCited:
    citation: Citation


@dataclass(frozen=True)
class TurnRefused:
    """The stored reply is the refusal; the panel shows what to do next."""


@dataclass(frozen=True)
class TurnFailed:
    """The turn ended with no assistant message stored."""

    code: str
    message: str


TurnEvent = (
    TurnStarted
    | TurnSearched
    | TurnDelta
    | TurnCited
    | TurnRefused
    | TurnFinished
    | TurnFailed
)
