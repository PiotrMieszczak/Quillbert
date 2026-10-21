from app.domain.assistant import Conversation, Message
from app.domain.shared import NotFound


class InMemoryConversationRepo:
    def __init__(self, campaigns: set[str] | None = None) -> None:
        # None accepts any campaign id. A set mirrors the SQL foreign key, for the
        # contract suite.
        self._campaigns = campaigns
        self._conversations: dict[int, Conversation] = {}
        self._next_conversation_id = 1
        self._next_message_id = 1

    def next_conversation_id(self) -> int:
        ident = self._next_conversation_id
        self._next_conversation_id += 1
        return ident

    def next_message_id(self) -> int:
        ident = self._next_message_id
        self._next_message_id += 1
        return ident

    def save(self, conversation: Conversation) -> None:
        if (
            self._campaigns is not None
            and conversation.campaign_id not in self._campaigns
        ):
            raise NotFound("campaign not found")
        self._conversations[conversation.id] = conversation

    def get(self, conversation_id: int) -> Conversation | None:
        return self._conversations.get(conversation_id)

    def add_message(self, message: Message) -> None:
        conversation = self._conversations.get(message.conversation_id)
        if conversation is None:
            raise NotFound("conversation not found")
        conversation.messages.append(message)

    def list_for_campaign(self, campaign_id: str) -> list[Conversation]:
        return [
            conversation
            for conversation in reversed(self._conversations.values())
            if conversation.campaign_id == campaign_id
        ]
