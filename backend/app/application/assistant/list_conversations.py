from app.application.dto import ConversationView
from app.ports.repositories import ConversationRepo


class ListConversations:
    def __init__(self, repo: ConversationRepo) -> None:
        self._repo = repo

    def execute(self, *, campaign_id: str) -> list[ConversationView]:
        """Newest first. The caller has already shown it owns the campaign."""
        return [
            ConversationView(
                id=conversation.id,
                campaign_id=conversation.campaign_id,
                mode=conversation.mode,
                started_at=conversation.started_at,
            )
            for conversation in self._repo.list_for_campaign(campaign_id)
        ]
