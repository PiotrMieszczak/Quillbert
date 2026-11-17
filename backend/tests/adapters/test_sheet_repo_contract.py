from datetime import UTC, datetime

import pytest
from app.domain.shared import NotFound
from app.domain.sheets import Sheet
from app.ports.repositories import SheetRepo

NOW = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)


def _sheet(label: str = "Strength") -> Sheet:
    return Sheet.model_validate(
        {
            "sections": [
                {
                    "key": "abilities",
                    "label": "Abilities",
                    "fields": [
                        {
                            "key": "STR",
                            "label": label,
                            "type": "int",
                            "min": 1,
                            "max": 30,
                        },
                        {
                            "key": "feats",
                            "label": "Feats",
                            "type": "list",
                            "itemFields": [
                                {"key": "name", "label": "Feat", "type": "text"}
                            ],
                        },
                    ],
                }
            ],
            "sources": [{"documentId": "5dfa", "headingPath": ["Rules", "Abilities"]}],
        }
    )


def test_a_system_without_a_sheet_has_none(sheet_repo: SheetRepo) -> None:
    assert sheet_repo.get("dnd-2024") is None


def test_a_saved_sheet_round_trips_for_its_system_only(sheet_repo: SheetRepo) -> None:
    sheet_repo.save("dnd-2024", _sheet(), saved_by="admin-1", saved_at=NOW)
    assert sheet_repo.get("dnd-2024") == _sheet()
    assert sheet_repo.get("traveller-2e") is None


def test_saving_again_replaces_the_sheet(sheet_repo: SheetRepo) -> None:
    sheet_repo.save("dnd-2024", _sheet(), saved_by="admin-1", saved_at=NOW)
    sheet_repo.save("dnd-2024", _sheet("Might"), saved_by="admin-2", saved_at=NOW)
    assert sheet_repo.get("dnd-2024") == _sheet("Might")


def test_an_unknown_system_cannot_have_a_sheet(sheet_repo: SheetRepo) -> None:
    with pytest.raises(NotFound):
        sheet_repo.save("no-such-system", _sheet(), saved_by="admin-1", saved_at=NOW)
