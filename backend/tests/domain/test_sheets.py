import pytest
from app.domain.sheets import Sheet, StatsInvalid, validate_stats
from pydantic import ValidationError

TRAVELLER = {
    "sections": [
        {
            "key": "characteristics",
            "label": "Characteristics",
            "fields": [
                {"key": "STR", "label": "Strength", "type": "int", "min": 0, "max": 15},
                {"key": "homeworld", "label": "Homeworld", "type": "text"},
            ],
        },
        {
            "key": "skills",
            "label": "Skills",
            "fields": [
                {
                    "key": "skills",
                    "label": "Skills",
                    "type": "list",
                    "itemFields": [
                        {"key": "name", "label": "Skill", "type": "text"},
                        {
                            "key": "level",
                            "label": "Level",
                            "type": "int",
                            "min": 0,
                            "max": 4,
                        },
                    ],
                }
            ],
        },
    ]
}


@pytest.fixture
def sheet() -> Sheet:
    return Sheet.model_validate(TRAVELLER)


def _field(**fields) -> dict:
    return {"sections": [{"key": "s", "label": "S", "fields": [fields]}]}


@pytest.mark.parametrize(
    "broken",
    [
        {"sections": []},
        _field(key="a", label="A", type="list"),
        _field(key="a", label="A", type="text", max=3),
        _field(key="a", label="A", type="int", min=5, max=1),
        _field(key="a", label="A", type="int", itemFields=[]),
        _field(key="a", label="A", type="bool"),
        {"sections": TRAVELLER["sections"][:1] * 2},
    ],
)
def test_a_malformed_sheet_is_rejected(broken: dict) -> None:
    with pytest.raises(ValidationError):
        Sheet.model_validate(broken)


def test_a_sheet_survives_storage_by_field_name(sheet: Sheet) -> None:
    assert Sheet.model_validate(sheet.model_dump(exclude_none=True)) == sheet


def test_stats_that_fit_the_sheet_pass(sheet: Sheet) -> None:
    validate_stats(sheet, {})
    validate_stats(
        sheet,
        {
            "characteristics": {"STR": 15, "homeworld": None},
            "skills": {"skills": [{"name": "Pilot", "level": 2}, {"name": "Recon"}]},
        },
    )


@pytest.mark.parametrize(
    "stats",
    [
        {"abilities": {"WIS": 17}},
        {"characteristics": {"WIS": 17}},
        {"characteristics": {"STR": 16}},
        {"characteristics": {"STR": -1}},
        {"characteristics": {"STR": "7"}},
        {"characteristics": {"STR": True}},
        {"characteristics": {"homeworld": 4}},
        {"characteristics": [1, 2]},
        {"skills": {"skills": {"name": "Pilot"}}},
        {"skills": {"skills": [{"name": "Pilot", "level": 9}]}},
        {"skills": {"skills": [{"speciality": "Small craft"}]}},
        {"skills": {"skills": ["Pilot"]}},
    ],
)
def test_stats_that_do_not_fit_are_rejected(sheet: Sheet, stats: dict) -> None:
    with pytest.raises(StatsInvalid):
        validate_stats(sheet, stats)
