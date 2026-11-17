from app.domain.shared import NotFound
from app.domain.sheets import Sheet
from app.ports.clock import Clock
from app.ports.repositories import SheetRepo

__all__ = ["GetSheet", "SaveSheet"]


class GetSheet:
    def __init__(self, repo: SheetRepo) -> None:
        self._repo = repo

    def execute(self, *, system_id: str) -> Sheet:
        sheet = self._repo.get(system_id)
        if sheet is None:
            raise NotFound("no sheet is saved for this system")
        return sheet


class SaveSheet:
    """The admin's reviewed sheet replaces the system's one sheet (ADR-0030). The
    route has already checked the caller is an admin."""

    def __init__(self, repo: SheetRepo, clock: Clock) -> None:
        self._repo = repo
        self._clock = clock

    def execute(self, *, system_id: str, sheet: Sheet, saved_by: str) -> Sheet:
        self._repo.save(system_id, sheet, saved_by=saved_by, saved_at=self._clock.now())
        return sheet
