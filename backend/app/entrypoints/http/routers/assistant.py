from collections.abc import Iterator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.application.dto import ConversationView, MessageView
from app.entrypoints.http.auth import require_campaign
from app.entrypoints.http.schemas.assistant import (
    ConversationOut,
    CreateConversationBody,
    MessageOut,
    SendMessageBody,
)
from app.entrypoints.http.streaming import ag_ui_frame

router = APIRouter(
    prefix="/api/v1/campaigns/{campaign_id}", dependencies=[Depends(require_campaign)]
)


def _start(request: Request) -> StartConversation:
    return request.app.state.start_conversation


def _run(request: Request) -> RunAssistantTurn:
    return request.app.state.run_turn


def _list(request: Request) -> ListMessages:
    return request.app.state.list_messages


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
    )


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
    body: SendMessageBody,
    request: Request,
) -> StreamingResponse:
    events = _run(request).execute(
        campaign_id=campaign_id,
        conversation_id=conversation_id,
        content=body.content,
    )
    first = next(events)

    def frames() -> Iterator[str]:
        yield ag_ui_frame(first)
        for event in events:
            yield ag_ui_frame(event)

    return StreamingResponse(frames(), media_type="text/event-stream")
