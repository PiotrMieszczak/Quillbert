import json
import logging
from collections.abc import Iterable, Iterator

from ag_ui.core import (
    BaseEvent,
    CustomEvent,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder

from app.application.dto import (
    TurnCited,
    TurnDelta,
    TurnEvent,
    TurnFailed,
    TurnFinished,
    TurnSearched,
    TurnStarted,
)

logger = logging.getLogger(__name__)

SEARCH_TOOL = "search_documents"


def _events(turn: Iterable[TurnEvent]) -> Iterator[BaseEvent]:
    thread_id = run_id = ""
    open_message: str | None = None
    for event in turn:
        # A text message opens on its first delta and closes before anything else.
        if open_message and not isinstance(event, TurnDelta):
            yield TextMessageEndEvent(message_id=open_message)
            open_message = None
        match event:
            case TurnStarted():
                thread_id, run_id = str(event.conversation_id), event.run_id
                yield RunStartedEvent(thread_id=thread_id, run_id=run_id)
            case TurnSearched():
                # The server, not the model, runs the search; the chip is a tool call.
                call = f"search-{run_id}"
                yield ToolCallStartEvent(tool_call_id=call, tool_call_name=SEARCH_TOOL)
                yield ToolCallArgsEvent(
                    tool_call_id=call, delta=json.dumps({"query": event.query})
                )
                yield ToolCallEndEvent(tool_call_id=call)
                yield ToolCallResultEvent(
                    message_id=f"{call}-result", tool_call_id=call, content=event.result
                )
            case TurnDelta():
                message_id = str(event.message_id)
                if open_message is None:
                    open_message = message_id
                    yield TextMessageStartEvent(message_id=message_id, role="assistant")
                yield TextMessageContentEvent(message_id=message_id, delta=event.text)
            case TurnCited():
                c = event.citation
                yield CustomEvent(
                    name="dm.citation",
                    value={
                        "label": c.label,
                        "chunkId": c.chunk_id,
                        "documentId": c.document_id,
                        "filename": c.filename,
                        "pageFrom": c.page_from,
                        "heading": c.heading,
                        "attribution": None,
                    },
                )
            case TurnFinished():
                yield RunFinishedEvent(thread_id=thread_id, run_id=run_id)
            case TurnFailed():
                yield RunErrorEvent(message=event.message, code=event.code)


def ag_ui_frames(turn: Iterable[TurnEvent]) -> Iterator[str]:
    """Turn events as AG-UI SSE frames (ADR-0009); the SDK owns schema and framing."""
    encoder = EventEncoder()
    try:
        for event in _events(turn):
            yield encoder.encode(event)
    except Exception:
        # The use case reports its own failures as TurnFailed; this is the last net,
        # so a stream never just stops.
        logger.exception("turn stream broke")
        yield encoder.encode(
            RunErrorEvent(
                message="The assistant could not answer.", code="internal_error"
            )
        )
