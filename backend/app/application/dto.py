from dataclasses import dataclass
from datetime import datetime

from app.domain.assistant import Mode, Role
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
class TurnDelta:
    message_id: int
    text: str


@dataclass(frozen=True)
class TurnFinished:
    conversation_id: int
    run_id: str
    message_id: int


TurnEvent = TurnStarted | TurnDelta | TurnFinished
