import pytest
from app.adapters.llm.fake import FakeLLM
from app.adapters.llm.prompts import research
from app.adapters.persistence.memory.conversations import InMemoryConversationRepo
from app.adapters.persistence.memory.documents import InMemoryDocumentRepo
from app.application.assistant import ListMessages, RunAssistantTurn, StartConversation
from app.application.dto import (
    TurnCited,
    TurnDelta,
    TurnFailed,
    TurnFinished,
    TurnSearched,
    TurnStarted,
)
from app.domain.assistant import Mode, Role
from app.domain.shared import NotFound, ValidationFailed
from app.ports.llm import LLMError
from tests.conftest import FROZEN, index_document

QUESTION = "How does grappling work?"


def _conversation(start: StartConversation) -> int:
    return start.execute(campaign_id="ashfall", mode=Mode.RESEARCH).id


def _ask(run_turn: RunAssistantTurn, conversation_id: int, content: str = QUESTION):
    return list(
        run_turn.execute(
            campaign_id="ashfall", conversation_id=conversation_id, content=content
        )
    )


def test_start_records_research_mode(start: StartConversation) -> None:
    view = start.execute(campaign_id="ashfall", mode=Mode.RESEARCH)
    assert view.id == 1
    assert view.campaign_id == "ashfall"
    assert view.mode is Mode.RESEARCH
    assert view.started_at == FROZEN


def test_a_grounded_turn_streams_cites_and_stores_the_trace(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    list_messages: ListMessages,
    document_repo: InMemoryDocumentRepo,
    fake_llm: FakeLLM,
) -> None:
    index_document(
        document_repo, "ashfall", "SRD.pdf", "Grappling uses an Athletics check."
    )
    conversation_id = _conversation(start)

    events = _ask(run_turn, conversation_id)

    assert isinstance(events[0], TurnStarted)
    assert events[1] == TurnSearched(QUESTION, "Searched 1 document · 1 passage")
    assert any(isinstance(event, TurnDelta) for event in events)
    assert isinstance(events[-2], TurnCited)
    assert isinstance(events[-1], TurnFinished)

    user, assistant = list_messages.execute(
        campaign_id="ashfall", conversation_id=conversation_id
    )
    assert [user.role, assistant.role] == [Role.USER, Role.ASSISTANT]
    assert assistant.content.endswith("[S1].")
    assert assistant.tool_label == "Searched 1 document · 1 passage"
    (citation,) = assistant.citations
    assert (citation.label, citation.filename, citation.page_from) == (
        "S1",
        "SRD.pdf",
        1,
    )
    assert user.citations == ()

    (call,) = fake_llm.calls
    assert call.messages[0] == {"role": "system", "content": research.SYSTEM}
    assert "Grappling uses an Athletics check." in call.messages[-1]["content"]


def test_the_assistant_message_stores_the_trace_and_the_user_message_none(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    repo: InMemoryConversationRepo,
    document_repo: InMemoryDocumentRepo,
) -> None:
    index_document(document_repo, "ashfall", "SRD.pdf", "Grappling rules")
    conversation_id = _conversation(start)
    _ask(run_turn, conversation_id)

    user, assistant = repo.get(conversation_id).messages
    assert user.trace is None
    trace = assistant.trace
    assert (trace.prompt_id, trace.prompt_version) == ("research", research.VERSION)
    assert len(trace.prompt_version) == 12
    assert (trace.model, trace.prompt_tokens, trace.completion_tokens) == (
        "fake",
        10,
        5,
    )
    assert trace.cost_usd == 0.0
    assert trace.ttft_ms is not None and trace.duration_ms is not None


def test_no_hits_writes_the_refusal_and_never_calls_the_model(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    repo: InMemoryConversationRepo,
    fake_llm: FakeLLM,
) -> None:
    conversation_id = _conversation(start)

    events = _ask(run_turn, conversation_id, "Tell me about starships")

    assert fake_llm.calls == []
    assert events[1] == TurnSearched(
        "Tell me about starships", "Searched 0 documents · 0 passages"
    )
    assert [e.text for e in events if isinstance(e, TurnDelta)] == [research.REFUSAL]
    assert not any(isinstance(e, TurnCited) for e in events)
    assistant = repo.get(conversation_id).messages[-1]
    assert assistant.content == research.REFUSAL
    assert assistant.citations == ()
    trace = assistant.trace
    assert (trace.prompt_id, trace.prompt_version) == ("research", research.VERSION)
    assert (trace.model, trace.ttft_ms) == (None, None)
    assert (trace.prompt_tokens, trace.completion_tokens, trace.cost_usd) == (
        None,
        None,
        None,
    )


def test_only_this_campaigns_documents_are_searched(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    document_repo: InMemoryDocumentRepo,
    fake_llm: FakeLLM,
) -> None:
    index_document(document_repo, "other", "Secret.pdf", "Grappling secrets")
    _ask(run_turn, _conversation(start))
    assert fake_llm.calls == []


def test_a_label_the_model_made_up_is_not_a_citation(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    document_repo: InMemoryDocumentRepo,
    fake_llm: FakeLLM,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index_document(document_repo, "ashfall", "SRD.pdf", "Grappling rules")

    def invented(self, **_):
        yield "See [S1, S9] and [S4]."

    monkeypatch.setattr(fake_llm.__class__, "stream", invented)
    events = _ask(run_turn, _conversation(start))
    cited = [e.citation.label for e in events if isinstance(e, TurnCited)]
    assert cited == ["S1"]


def test_a_failure_mid_stream_stores_no_assistant_message(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    repo: InMemoryConversationRepo,
    document_repo: InMemoryDocumentRepo,
    fake_llm: FakeLLM,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index_document(document_repo, "ashfall", "SRD.pdf", "Grappling rules")

    def broken(self, **_):
        yield "A grapple is "
        raise LLMError("provider fell over")

    monkeypatch.setattr(fake_llm.__class__, "stream", broken)
    conversation_id = _conversation(start)

    events = _ask(run_turn, conversation_id)

    assert isinstance(events[-1], TurnFailed)
    assert events[-1].code == "provider_error"
    assert not any(isinstance(e, TurnFinished) for e in events)
    assert [m.role for m in repo.get(conversation_id).messages] == [Role.USER]


def test_history_window_keeps_the_recent_messages_and_opens_on_a_user_turn(
    start: StartConversation,
    run_turn: RunAssistantTurn,
    document_repo: InMemoryDocumentRepo,
    fake_llm: FakeLLM,
) -> None:
    index_document(document_repo, "ashfall", "SRD.pdf", "Grappling rules")
    conversation_id = _conversation(start)
    for n in range(4):
        _ask(run_turn, conversation_id, f"Grappling question {n}")

    roles = [m["role"] for m in fake_llm.calls[-1].messages]
    # system + the last 6 messages (u a u a u a u -> window starts mid-pair).
    assert roles[0] == "system"
    assert roles[1] == "user"
    assert len(roles) <= 1 + 6


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


def test_the_campaigns_owner_and_system_reach_search_and_the_layer_reaches_the_citation(
    fake_llm: FakeLLM,
) -> None:
    from app.adapters.clock.frozen import FrozenClock
    from app.ports.search import Hit

    calls = []

    class Search:
        def search(self, campaign_id, owner_id, system_id, text, vector, k):
            calls.append((campaign_id, owner_id, system_id))
            return [Hit(7, 3, "Mine.md", 2, None, "Speed is 0.", 1.0, "My library")]

    repo = InMemoryConversationRepo()
    clock = FrozenClock(FROZEN)
    conversation_id = (
        StartConversation(repo, clock)
        .execute(campaign_id="ashfall", mode=Mode.RESEARCH)
        .id
    )
    turn = RunAssistantTurn(repo, fake_llm, clock, Search(), None)

    events = list(
        turn.execute(
            campaign_id="ashfall",
            conversation_id=conversation_id,
            content=QUESTION,
            owner_id="gm-a",
            system_id="dnd-2024",
        )
    )

    assert calls == [("ashfall", "gm-a", "dnd-2024")]
    (cited,) = [event for event in events if isinstance(event, TurnCited)]
    assert cited.citation.attribution == "My library"
