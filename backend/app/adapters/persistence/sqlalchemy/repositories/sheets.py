from datetime import datetime

from sqlalchemy.orm import Session, sessionmaker

from app.adapters.persistence.sqlalchemy.tables import SheetTemplateRow, SystemRow
from app.domain.shared import NotFound
from app.domain.sheets import Sheet


class SqlSheetRepo:
    """SheetRepo over PostgreSQL: one row per system (ADR-0030 IMP-001)."""

    def __init__(self, sessions: sessionmaker[Session]) -> None:
        self._sessions = sessions

    def get(self, system_id: str) -> Sheet | None:
        with self._sessions() as session:
            row = session.get(SheetTemplateRow, system_id)
            return None if row is None else Sheet.model_validate(row.sheet)

    def save(
        self, system_id: str, sheet: Sheet, *, saved_by: str, saved_at: datetime
    ) -> None:
        with self._sessions.begin() as session:
            if session.get(SystemRow, system_id) is None:
                raise NotFound("system not found")
            session.merge(
                SheetTemplateRow(
                    system_id=system_id,
                    sheet=sheet.model_dump(exclude_none=True),
                    saved_by=saved_by,
                    saved_at=saved_at,
                )
            )
