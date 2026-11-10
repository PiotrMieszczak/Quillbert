from app.application.cast.views import character_view
from app.application.dto import CharacterView
from app.domain.shared import NotFound
from app.ports.repositories import CharacterRepo


class GetCharacter:
    def __init__(self, repo: CharacterRepo) -> None:
        self._repo = repo

    def execute(self, *, campaign_id: str, character_id: int) -> CharacterView:
        character = self._repo.get(campaign_id, character_id)
        if character is None:
            raise NotFound("character not found")
        return character_view(character)
