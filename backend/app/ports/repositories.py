from collections.abc import Sequence
from typing import Protocol

from app.domain.assistant import Conversation, Message
from app.domain.campaigns import Campaign, System
from app.domain.documents import Chunk, Document, Shelf


class ConversationRepo(Protocol):
    def next_conversation_id(self) -> int: ...

    def next_message_id(self) -> int: ...

    def save(self, conversation: Conversation) -> None: ...

    def get(self, conversation_id: int) -> Conversation | None: ...

    def add_message(self, message: Message) -> None:
        """Store the message with its citations and trace, in one transaction."""
        ...

    def list_for_campaign(self, campaign_id: str) -> list[Conversation]:
        """Newest first."""
        ...


class DocumentRepo(Protocol):
    """Every read takes a shelf: a document shows only on its own shelf (ADR-0027)."""

    def next_document_id(self) -> int: ...

    def add(self, document: Document) -> None:
        """Raises NotFound when its campaign does not exist."""
        ...

    def get(self, shelf: Shelf, document_id: int) -> Document | None: ...

    def list_shelf(self, shelf: Shelf) -> list[Document]:
        """Oldest first."""
        ...

    def find_by_sha256(self, shelf: Shelf, sha256: str) -> Document | None: ...

    def remove(self, shelf: Shelf, document_id: int) -> Document | None:
        """Delete and return the document, or None when that shelf has no such id."""
        ...

    def claim_queued(self) -> Document | None:
        """Mark the oldest queued document `processing` and return it, or None when
        nothing waits. Two workers never claim the same document."""
        ...

    def requeue_processing(self) -> int:
        """Return every `processing` document to `queued`; how many there were.

        For worker start-up: a document left `processing` was interrupted.
        """
        ...

    def update(self, document: Document) -> None:
        """Persist status, progress, page_count, meta and error."""
        ...

    def index(self, document: Document, chunks: Sequence[Chunk]) -> None:
        """Replace the document's chunks and save the document, in one transaction.

        Every chunk carries its embedding and the model that made it. Keyword vectors
        use the document's language.
        """
        ...


class CampaignRepo(Protocol):
    """Every campaign read takes the owner id (DEC-005, BND-003): another user's
    campaign is indistinguishable from a missing one."""

    def systems(self) -> list[System]:
        """Every system a campaign may be played in, by name."""
        ...

    def add(self, campaign: Campaign) -> None: ...

    def get(self, owner_id: str, campaign_id: str) -> Campaign | None: ...

    def list_for_owner(self, owner_id: str) -> list[Campaign]:
        """Most recently played first, then newest."""
        ...

    def set_image(
        self, owner_id: str, campaign_id: str, image_key: str | None
    ) -> str | None:
        """Replace the banner key and return the previous one. Raises NotFound."""
        ...
