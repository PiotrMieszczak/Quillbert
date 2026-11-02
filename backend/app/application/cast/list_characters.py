import base64
import binascii
import json

from app.application.cast.views import character_view
from app.application.dto import CharacterPage
from app.domain.cast import Relationship, clean_text
from app.domain.shared import ValidationFailed
from app.ports.repositories import CharacterRepo


class ListCharacters:
    """One page of a campaign's characters, by name. Campaigns hold many NPCs, so the
    list is paged by a keyset cursor rather than returned whole."""

    def __init__(self, repo: CharacterRepo) -> None:
        self._repo = repo

    def execute(
        self,
        *,
        campaign_id: str,
        is_player: bool | None = None,
        relationship: Relationship | None = None,
        q: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CharacterPage:
        # One extra row tells whether another page follows.
        rows = self._repo.page(
            campaign_id,
            is_player=is_player,
            relationship=relationship,
            name_contains=clean_text(q),
            after=None if cursor is None else _decode(cursor),
            limit=limit + 1,
        )
        items = rows[:limit]
        more = len(rows) > limit
        return CharacterPage(
            items=tuple(character_view(c) for c in items),
            next_cursor=_encode(items[-1].sort_key) if more else None,
        )


def _encode(key: tuple[str, int]) -> str:
    return base64.urlsafe_b64encode(json.dumps(list(key)).encode()).decode()


def _decode(cursor: str) -> tuple[str, int]:
    try:
        name, ident = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    except (binascii.Error, ValueError, TypeError) as error:
        raise ValidationFailed("invalid cursor") from error
    if not isinstance(name, str) or not isinstance(ident, int):
        raise ValidationFailed("invalid cursor")
    return (name, ident)
