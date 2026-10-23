"""Row <-> entity translation. The domain never sees a row."""

from app.adapters.persistence.sqlalchemy.tables import (
    CampaignRow,
    CitationRow,
    ConversationRow,
    DocumentRow,
    MessageRow,
)
from app.domain.assistant import Citation, Conversation, Message, Mode, Role, Trace
from app.domain.campaigns import Campaign, System
from app.domain.documents import Document, DocumentKind, DocumentSource, DocumentStatus


def message_to_row(message: Message) -> MessageRow:
    trace = message.trace
    return MessageRow(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role.value,
        content=message.content,
        mode=message.mode.value,
        tool_label=message.tool_label,
        created_at=message.created_at,
        prompt_id=trace and trace.prompt_id,
        prompt_version=trace and trace.prompt_version,
        model=trace and trace.model,
        ttft_ms=trace and trace.ttft_ms,
        duration_ms=trace and trace.duration_ms,
        prompt_tokens=trace and trace.prompt_tokens,
        completion_tokens=trace and trace.completion_tokens,
        cost_usd=trace and trace.cost_usd,
        citations=[
            CitationRow(chunk_id=c.chunk_id, label=c.label) for c in message.citations
        ],
    )


def message_from_row(
    row: MessageRow, citations: dict[int, Citation] | None = None
) -> Message:
    """`citations` maps a citation row id to its resolved passage; see the repo."""
    trace = None
    if row.prompt_id is not None and row.prompt_version is not None:
        trace = Trace(
            prompt_id=row.prompt_id,
            prompt_version=row.prompt_version,
            model=row.model,
            ttft_ms=row.ttft_ms,
            duration_ms=row.duration_ms,
            prompt_tokens=row.prompt_tokens,
            completion_tokens=row.completion_tokens,
            cost_usd=row.cost_usd,
        )
    return Message(
        id=row.id,
        conversation_id=row.conversation_id,
        role=Role(row.role),
        content=row.content,
        created_at=row.created_at,
        mode=Mode(row.mode),
        tool_label=row.tool_label,
        citations=tuple((citations or {})[c.id] for c in row.citations),
        trace=trace,
    )


def conversation_to_row(conversation: Conversation) -> ConversationRow:
    return ConversationRow(
        id=conversation.id,
        campaign_id=conversation.campaign_id,
        mode=conversation.mode.value,
        started_at=conversation.started_at,
        messages=[message_to_row(message) for message in conversation.messages],
    )


def conversation_from_row(
    row: ConversationRow, citations: dict[int, Citation] | None = None
) -> Conversation:
    return Conversation(
        id=row.id,
        campaign_id=row.campaign_id,
        mode=Mode(row.mode),
        started_at=row.started_at,
        messages=[message_from_row(m, citations) for m in row.messages],
    )


def document_to_row(document: Document) -> DocumentRow:
    return DocumentRow(
        id=document.id,
        campaign_id=document.campaign_id,
        filename=document.filename,
        kind=document.kind.value,
        page_count=document.page_count,
        meta=document.meta,
        status=document.status.value,
        progress=document.progress,
        error=document.error,
        storage_key=document.storage_key,
        source=document.source.value,
        source_ref=document.source_ref,
        sha256=document.sha256,
        uploaded_at=document.uploaded_at,
        owner_id=document.owner_id,
        systems=list(document.systems),
        attribution=document.attribution,
    )


def document_from_row(row: DocumentRow) -> Document:
    return Document(
        id=row.id,
        campaign_id=row.campaign_id,
        filename=row.filename,
        kind=DocumentKind(row.kind),
        page_count=row.page_count,
        meta=row.meta,
        status=DocumentStatus(row.status),
        progress=row.progress,
        error=row.error,
        storage_key=row.storage_key,
        source=DocumentSource(row.source),
        source_ref=row.source_ref,
        sha256=row.sha256,
        uploaded_at=row.uploaded_at,
        owner_id=row.owner_id,
        systems=tuple(row.systems),
        attribution=row.attribution,
    )


def campaign_to_row(campaign: Campaign) -> CampaignRow:
    return CampaignRow(
        id=campaign.id,
        owner_id=campaign.owner_id,
        name=campaign.name,
        system_id=campaign.system.id,
        tint=campaign.tint,
        image_path=campaign.image_key,
        last_played_at=campaign.last_played_at,
        created_at=campaign.created_at,
    )


def campaign_from_row(row: CampaignRow) -> Campaign:
    if row.owner_id is None:
        raise ValueError(f"campaign {row.id} has no owner")  # queries filter these out
    return Campaign(
        id=row.id,
        owner_id=row.owner_id,
        name=row.name,
        system=System(row.system.id, row.system.name),
        tint=row.tint,
        created_at=row.created_at,
        image_key=row.image_path,
        last_played_at=row.last_played_at,
    )
