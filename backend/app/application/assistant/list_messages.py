from app.application.dto import MessageView
from app.domain.assistant import Role
from app.domain.shared import NotFound
from app.ports.llm import LLMProvider
from app.ports.repositories import ConversationRepo


class ListMessages:
    def __init__(self, repo: ConversationRepo, llm: LLMProvider) -> None:
        self._repo = repo
        self._llm = llm

    def execute(self, *, campaign_id: str, conversation_id: int) -> list[MessageView]:
        conversation = self._repo.get(conversation_id)
        if conversation is None or conversation.campaign_id != campaign_id:
            raise NotFound("conversation not found")
        return [
            MessageView(
                id=message.id,
                role=message.role,
                content=message.content,
                created_at=message.created_at,
                mode=message.mode,
                tool_label=message.tool_label,
                citations=message.citations,
                refused=message.role is Role.ASSISTANT
                and self._llm.profile(message.mode).refused(message.content),
            )
            for message in conversation.messages
        ]
