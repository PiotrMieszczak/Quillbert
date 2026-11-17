from datetime import datetime

from app.adapters.persistence.memory.campaigns import SYSTEMS
from app.domain.shared import NotFound
from app.domain.sheets import Sheet


class InMemorySheetRepo:
    def __init__(self) -> None:
        self._sheets: dict[str, Sheet] = {}

    def get(self, system_id: str) -> Sheet | None:
        sheet = self._sheets.get(system_id)
        return None if sheet is None else sheet.model_copy(deep=True)

    def save(
        self, system_id: str, sheet: Sheet, *, saved_by: str, saved_at: datetime
    ) -> None:
        if all(system.id != system_id for system in SYSTEMS):
            raise NotFound("system not found")
        self._sheets[system_id] = sheet.model_copy(deep=True)
