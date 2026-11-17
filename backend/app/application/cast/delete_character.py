from app.domain.shared import NotFound
from app.ports.files import FileStore
from app.ports.repositories import CharacterRepo


class DeleteCharacter:
    def __init__(self, repo: CharacterRepo, files: FileStore) -> None:
        self._repo = repo
        self._files = files

    def execute(self, *, campaign_id: str, character_id: int) -> None:
        removed = self._repo.remove(campaign_id, character_id)
        if removed is None:
            raise NotFound("character not found")
        # The row is gone first, so a failure here leaves a stray file, never a
        # character pointing at a missing one.
        if removed.portrait_key is not None:
            self._files.delete(removed.portrait_key)
