"""One suite, every ConversationRepo. If both pass, swapping them changes nothing."""

from datetime import UTC, datetime, timedelta

import pytest
from app.adapters.persistence.sqlalchemy.engine import create_session_factory
from app.adapters.persistence.sqlalchemy.repositories import SqlConversationRepo
from app.domain.assistant import Citation, Conversation, Message, Mode, Role, Trace
from app.domain.shared import NotFound
from app.ports.repositories import ConversationRepo
from sqlalchemy import text

T0 = datetime(2026, 10, 10, 18, 0, tzinfo=UTC)


def _conversation(repo: ConversationRepo, campaign_id: str = "ashfall") -> Conversation:
    conversation = Conversation(
        id=repo.next_conversation_id(),
        campaign_id=campaign_id,
        mode=Mode.RESEARCH,
        started_at=T0,
    )
    repo.save(conversation)
    return conversation


def _message(
    repo: ConversationRepo, conversation: Conversation, role: Role, content: str
) -> Message:
    message = Message(
        id=repo.next_message_id(),
        conversation_id=conversation.id,
        role=role,
        content=content,
        created_at=T0 + timedelta(seconds=1),
        mode=conversation.mode,
    )
    repo.add_message(message)
    return message


def test_ids_are_unique(conversation_repo: ConversationRepo) -> None:
    assert conversation_repo.next_message_id() != conversation_repo.next_message_id()
    assert (
        conversation_repo.next_conversation_id()
        != conversation_repo.next_conversation_id()
    )


def test_saved_conversation_reads_back(conversation_repo: ConversationRepo) -> None:
    saved = _conversation(conversation_repo)
    loaded = conversation_repo.get(saved.id)
    assert loaded == saved


def test_messages_read_back_in_order_with_mode(
    conversation_repo: ConversationRepo,
) -> None:
    conversation = _conversation(conversation_repo)
    asked = _message(conversation_repo, conversation, Role.USER, "Who is Doran Vey?")
    answered = _message(
        conversation_repo, conversation, Role.ASSISTANT, "Not in your material."
    )

    loaded = conversation_repo.get(conversation.id)
    assert loaded is not None
    assert loaded.messages == [asked, answered]
    assert all(message.mode is Mode.RESEARCH for message in loaded.messages)


def test_unknown_conversation_is_none(conversation_repo: ConversationRepo) -> None:
    assert conversation_repo.get(424242) is None


def test_list_is_scoped_to_campaign(conversation_repo: ConversationRepo) -> None:
    """BND-003: another campaign's conversations are never returned."""
    mine = _conversation(conversation_repo, "ashfall")
    _conversation(conversation_repo, "other")
    assert [c.id for c in conversation_repo.list_for_campaign("ashfall")] == [mine.id]


def test_list_is_newest_first(conversation_repo: ConversationRepo) -> None:
    older = _conversation(conversation_repo)
    newer = _conversation(conversation_repo)
    assert [c.id for c in conversation_repo.list_for_campaign("ashfall")] == [
        newer.id,
        older.id,
    ]


def test_trace_reads_back_and_a_user_message_has_none(
    conversation_repo: ConversationRepo,
) -> None:
    conversation = _conversation(conversation_repo)
    trace = Trace(
        "research", "b443b9246d38", "google/m", 310, 2400, 812, 96, 0.00012345
    )
    reply = Message(
        id=conversation_repo.next_message_id(),
        conversation_id=conversation.id,
        role=Role.ASSISTANT,
        content="A grapple is a hold.",
        created_at=T0,
        mode=Mode.RESEARCH,
        trace=trace,
    )
    conversation_repo.add_message(reply)
    asked = _message(conversation_repo, conversation, Role.USER, "q")

    loaded = conversation_repo.get(conversation.id)
    assert loaded is not None
    assert loaded.messages == [reply, asked]
    assert loaded.messages[0].trace == trace
    assert loaded.messages[1].trace is None


def test_unknown_campaign_is_not_found(conversation_repo: ConversationRepo) -> None:
    with pytest.raises(NotFound):
        _conversation(conversation_repo, "no-such-campaign")


def test_message_for_unknown_conversation_is_not_found(
    conversation_repo: ConversationRepo,
) -> None:
    ghost = Conversation(
        id=424242, campaign_id="ashfall", mode=Mode.RESEARCH, started_at=T0
    )
    with pytest.raises(NotFound):
        _message(conversation_repo, ghost, Role.USER, "hello")


def test_conversation_survives_a_new_process(sessions, migrated: str) -> None:
    """AC-005 pattern: a second engine, like a restarted backend, sees prior writes."""
    first = SqlConversationRepo(sessions)
    conversation = _conversation(first)
    _message(first, conversation, Role.USER, "Still here?")

    restarted = SqlConversationRepo(create_session_factory(migrated))
    loaded = restarted.get(conversation.id)
    assert loaded is not None
    assert [m.content for m in loaded.messages] == ["Still here?"]


def test_citations_resolve_to_their_passage(sessions, migrated: str) -> None:
    """Postgres only: a citation stores a chunk id; the passage is joined on read."""
    from app.adapters.persistence.sqlalchemy.repositories import SqlDocumentRepo
    from app.domain.documents import Chunk, Document, DocumentKind, DocumentStatus

    documents = SqlDocumentRepo(sessions)
    document = Document(
        id=documents.next_document_id(),
        campaign_id="ashfall",
        filename="SRD.pdf",
        kind=DocumentKind.PDF,
        sha256="1" * 64,
        storage_key="0" * 32,
        uploaded_at=T0,
    )
    documents.add(document)
    document.status = DocumentStatus.INDEXED
    documents.index(document, [Chunk(0, "A grapple is a hold.", 177, 177, "Grappled")])
    with sessions() as session:
        chunk_id = session.execute(text("SELECT id FROM chunk")).scalar_one()

    repo = SqlConversationRepo(sessions)
    conversation = _conversation(repo)
    citation = Citation("S1", chunk_id, document.id, "SRD.pdf", 177, "Grappled")
    reply = Message(
        id=repo.next_message_id(),
        conversation_id=conversation.id,
        role=Role.ASSISTANT,
        content="A grapple is a hold [S1].",
        created_at=T0,
        mode=Mode.RESEARCH,
        citations=(citation,),
    )
    repo.add_message(reply)

    assert repo.get(conversation.id).messages == [reply]
    assert repo.list_for_campaign("ashfall")[0].messages == [reply]

    # Deleting the document deletes its chunks, and the citations to them go too.
    documents.remove("ashfall", document.id)
    assert repo.get(conversation.id).messages[0].citations == ()
