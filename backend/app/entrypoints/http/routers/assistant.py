from contextlib import closing
from itertools import chain

from ag_ui.core import RunAgentInput, UserMessage
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.application.assistant import (
    ListConversations,
    ListMessages,
    RunAssistantTurn,
    StartConversation,
)
from app.application.dto import ConversationView, MessageView
from app.domain.shared import ValidationFailed
from app.entrypoints.http.auth import require_campaign
from app.entrypoints.http.schemas.assistant import (
    CitationOut,
    ConversationOut,
    CreateConversationBody,
    MessageOut,
)
from app.entrypoints.http.streaming import ag_ui_frames
from app.ports.auth import Identity

router = APIRouter(
    prefix="/api/v1/campaigns/{campaign_id}", dependencies=[Depends(require_campaign)]
)


def _start(request: Request) -> StartConversation:
    return request.app.state.start_conversation


def _run(request: Request) -> RunAssistantTurn:
    return request.app.state.run_turn


def _list(request: Request) -> ListMessages:
    return request.app.state.list_messages


def _conversations(request: Request) -> ListConversations:
    return request.app.state.list_conversations


def _conversation_out(view: ConversationView) -> ConversationOut:
    return ConversationOut(
        id=view.id,
        campaign_id=view.campaign_id,
        mode=view.mode,
        started_at=view.started_at,
    )


def _message_out(view: MessageView) -> MessageOut:
    return MessageOut(
        id=view.id,
        role=view.role.value,
        content=view.content,
        created_at=view.created_at,
        mode=view.mode,
        tool_label=view.tool_label,
        refused=view.refused,
        citations=[
            CitationOut(
                label=c.label,
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                filename=c.filename,
                page_from=c.page_from,
                heading=c.heading,
                attribution=c.attribution,
            )
            for c in view.citations
        ],
    )


def _question(body: RunAgentInput, conversation_id: int) -> str:
    """The text of the last user message. History, tools, context and state in the body
    are the client's claim, not the server's record, and are ignored."""
    if body.thread_id != str(conversation_id):
        raise ValidationFailed("threadId must be the conversation id")
    user = next(
        (m for m in reversed(body.messages) if isinstance(m, UserMessage)), None
    )
    if user is None:
        raise ValidationFailed("a user message is required")
    if isinstance(user.content, str):
        return user.content
    return "\n".join(part.text for part in user.content if part.type == "text")


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(campaign_id: str, request: Request) -> list[ConversationOut]:
    return [
        _conversation_out(view)
        for view in _conversations(request).execute(campaign_id=campaign_id)
    ]


@router.post("/conversations", status_code=201, response_model=ConversationOut)
def create_conversation(
    campaign_id: str, body: CreateConversationBody, request: Request
) -> ConversationOut:
    view = _start(request).execute(campaign_id=campaign_id, mode=body.mode)
    return _conversation_out(view)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageOut],
)
def list_messages(
    campaign_id: str, conversation_id: int, request: Request
) -> list[MessageOut]:
    return [
        _message_out(view)
        for view in _list(request).execute(
            campaign_id=campaign_id, conversation_id=conversation_id
        )
    ]


@router.post("/conversations/{conversation_id}/messages")
def send_message(
    campaign_id: str,
    conversation_id: int,
    body: RunAgentInput,
    request: Request,
    identity: Identity = Depends(require_campaign),
) -> StreamingResponse:
    campaign = request.app.state.get_campaign.execute(
        owner_id=identity.user_id, campaign_id=campaign_id
    )
    events = _run(request).execute(
        campaign_id=campaign_id,
        conversation_id=conversation_id,
        content=_question(body, conversation_id),
        owner_id=identity.user_id,
        system_id=campaign.system.id,
    )
    # Validation and not-found errors surface here as HTTP errors, before streaming.
    first = next(events)

    def frames():
        # Closing the generator when the client leaves abandons the provider call.
        with closing(events):
            yield from ag_ui_frames(chain([first], events))

    return StreamingResponse(frames(), media_type="text/event-stream")
