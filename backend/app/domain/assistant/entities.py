from dataclasses import dataclass, field
from datetime import datetime

from app.domain.assistant.values import Mode, Role


@dataclass(frozen=True)
class Citation:
    """A passage an assistant message cites, as the GM sees it (AC-002)."""

    label: str
    chunk_id: int
    document_id: int
    filename: str
    page_from: int | None
    heading: str | None
    # The layer outside the campaign it came from (ADR-0027); None for the campaign.
    attribution: str | None = None


@dataclass(frozen=True)
class Trace:
    """What the Gateway recorded about one assistant reply (ADR-0024).

    Usage fields are None when no provider was called.
    """

    prompt_id: str
    prompt_version: str
    model: str | None = None
    ttft_ms: int | None = None
    duration_ms: int | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


@dataclass(frozen=True)
class Message:
    id: int
    conversation_id: int
    role: Role
    content: str
    created_at: datetime
    mode: Mode
    tool_label: str | None = None
    # Assistant messages only.
    citations: tuple[Citation, ...] = ()
    trace: Trace | None = None


@dataclass
class Conversation:
    id: int
    campaign_id: str
    mode: Mode
    started_at: datetime
    messages: list[Message] = field(default_factory=list)
