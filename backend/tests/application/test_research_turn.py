import pytest
from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.application.dto import TurnDelta, TurnFinished, TurnStarted
from app.domain.assistant import Mode, Role
from app.domain.shared import NotFound, ValidationFailed
from tests.conftest import FROZEN


def test_start_records_research_mode(start: StartConversation) -> None:
    view = start.execute(campaign_id="ashfall", mode=Mode.RESEARCH)
    assert view.id == 1
    assert view.campaign_id == "ashfall"
    assert view.mode is Mode.RESEARCH
    assert view.started_at == FROZEN


def test_turn_persists_user_and_assistant(
    start: StartConversation, run_turn: RunAssistantTurn, list_messages: ListMessages
) -> None:
    conversation = start.execute(campaign_id="ashfall", mode=Mode.RESEARCH)
    events = list(
        run_turn.execute(
            campaign_id="ashfall",
            conversation_id=conversation.id,
            content="What did we establish about Doran Vey?",
        )
    )

    assert isinstance(events[0], TurnStarted)
    assert any(isinstance(event, TurnDelta) for event in events)
    assert isinstance(events[-1], TurnFinished)

    messages = list_messages.execute(
        campaign_id="ashfall", conversation_id=conversation.id
    )
    assert [message.role for message in messages] == [Role.USER, Role.ASSISTANT]
    assert all(message.mode is Mode.RESEARCH for message in messages)
    assert messages[0].content == "What did we establish about Doran Vey?"
    assert "scripted Research reply" in messages[1].content


def test_unknown_conversation_is_not_found(run_turn: RunAssistantTurn) -> None:
    with pytest.raises(NotFound):
        next(
            run_turn.execute(campaign_id="ashfall", conversation_id=99, content="hello")
        )


def test_campaign_scope_hides_other_campaigns(
    start: StartConversation, list_messages: ListMessages
) -> None:
    conversation = start.execute(campaign_id="ashfall", mode=Mode.RESEARCH)
    with pytest.raises(NotFound):
        list_messages.execute(campaign_id="other", conversation_id=conversation.id)


def test_empty_content_is_rejected(
    start: StartConversation, run_turn: RunAssistantTurn
) -> None:
    conversation = start.execute(campaign_id="ashfall", mode=Mode.RESEARCH)
    with pytest.raises(ValidationFailed):
        next(
            run_turn.execute(
                campaign_id="ashfall", conversation_id=conversation.id, content="  "
            )
        )
