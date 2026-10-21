from app.application.dto import MessageView
from app.domain.shared import NotFound
from app.ports.repositories import ConversationRepo


class ListMessages:
    def __init__(self, repo: ConversationRepo) -> None:
        self._repo = repo

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
            )
            for message in conversation.messages
        ]
