import dataclasses
from typing import BinaryIO

from app.application.cast.views import character_view
from app.application.dto import CampaignImage, CharacterView
from app.domain.campaigns import SNIFF_BYTES, image_type
from app.domain.shared import NotFound
from app.ports.files import FileStore
from app.ports.repositories import CharacterRepo


class SetCharacterPortrait:
    """Stores the image and points the character at it, replacing any earlier one."""

    def __init__(
        self, files: FileStore, repo: CharacterRepo, *, max_bytes: int
    ) -> None:
        self._files = files
        self._repo = repo
        self._max_bytes = max_bytes

    def execute(
        self, *, campaign_id: str, character_id: int, content: BinaryIO
    ) -> CharacterView:
        character = self._repo.get(campaign_id, character_id)
        if character is None:
            raise NotFound("character not found")
        image_type(content.read(SNIFF_BYTES), "portrait")
        content.seek(0)

        stored = self._files.put(content, max_bytes=self._max_bytes)
        previous = character.portrait_key
        character = dataclasses.replace(character, portrait_key=stored.key)
        try:
            self._repo.update(character)
        except Exception:
            # Deleted meanwhile, or the write failed: do not leave an orphan file.
            self._files.delete(stored.key)
            raise
        if previous is not None:
            self._files.delete(previous)
        return character_view(character)


class GetCharacterPortrait:
    def __init__(self, files: FileStore, repo: CharacterRepo) -> None:
        self._files = files
        self._repo = repo

    def execute(self, *, campaign_id: str, character_id: int) -> CampaignImage:
        character = self._repo.get(campaign_id, character_id)
        if character is None or character.portrait_key is None:
            raise NotFound("portrait not found")
        data = self._files.read(character.portrait_key)
        return CampaignImage(
            data=data, media_type=image_type(data[:SNIFF_BYTES], "portrait")
        )
