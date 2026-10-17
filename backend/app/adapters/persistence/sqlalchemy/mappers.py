"""Row <-> entity translation. The domain never sees a row."""

from app.adapters.persistence.sqlalchemy.tables import (
    ConversationRow,
    DocumentRow,
    MessageRow,
)
from app.domain.assistant import Conversation, Message, Mode, Role
from app.domain.documents import Document, DocumentKind, DocumentSource, DocumentStatus


def message_to_row(message: Message) -> MessageRow:
    return MessageRow(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role.value,
        content=message.content,
        mode=message.mode.value,
        tool_label=message.tool_label,
        created_at=message.created_at,
    )


def message_from_row(row: MessageRow) -> Message:
    return Message(
        id=row.id,
        conversation_id=row.conversation_id,
        role=Role(row.role),
        content=row.content,
        created_at=row.created_at,
        mode=Mode(row.mode),
        tool_label=row.tool_label,
    )


def conversation_to_row(conversation: Conversation) -> ConversationRow:
    return ConversationRow(
        id=conversation.id,
        campaign_id=conversation.campaign_id,
        mode=conversation.mode.value,
        started_at=conversation.started_at,
        messages=[message_to_row(message) for message in conversation.messages],
    )


def conversation_from_row(row: ConversationRow) -> Conversation:
    return Conversation(
        id=row.id,
        campaign_id=row.campaign_id,
        mode=Mode(row.mode),
        started_at=row.started_at,
        messages=[message_from_row(message) for message in row.messages],
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
    )
