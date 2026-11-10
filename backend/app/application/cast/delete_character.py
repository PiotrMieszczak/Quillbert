from app.domain.shared import NotFound
from app.ports.repositories import CharacterRepo


class DeleteCharacter:
    def __init__(self, repo: CharacterRepo) -> None:
        self._repo = repo

    def execute(self, *, campaign_id: str, character_id: int) -> None:
        if self._repo.remove(campaign_id, character_id) is None:
            raise NotFound("character not found")
