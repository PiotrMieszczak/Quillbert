"""A system's character sheet: what its stat block holds (ADR-0030).

Pydantic, unlike the rest of the domain: the same model validates a sheet an admin
saves and, later, supplies the JSON Schema a drafted sheet must follow.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.shared import DomainError

MAX_TEXT = 2_000
MAX_ROWS = 200


class StatsInvalid(DomainError):
    """A character's stats do not fit the system's sheet (422)."""


class _Model(BaseModel):
    # Wire names are camelCase; the stored JSON keeps the field names.
    model_config = ConfigDict(populate_by_name=True, extra="forbid")


def _unique_keys(items: list[Any], what: str) -> None:
    keys = [item.key for item in items]
    repeated = sorted({key for key in keys if keys.count(key) > 1})
    if repeated:
        raise ValueError(f"{what} keys repeat: {', '.join(repeated)}")


class SheetField(_Model):
    key: str = Field(min_length=1, max_length=60)
    label: str = Field(min_length=1, max_length=120)
    type: Literal["int", "text", "list"]
    min: int | None = None
    max: int | None = None
    # Columns of a repeating row, such as a Traveller skill with its speciality.
    item_fields: list["SheetField"] | None = Field(None, alias="itemFields")

    @model_validator(mode="after")
    def _coherent(self) -> "SheetField":
        if self.type == "list":
            if not self.item_fields:
                raise ValueError("a list field needs itemFields")
            if any(field.type == "list" for field in self.item_fields):
                raise ValueError("a list cannot hold another list")
            _unique_keys(self.item_fields, "itemFields")
        elif self.item_fields is not None:
            raise ValueError("only a list field has itemFields")
        if self.type != "int" and (self.min is not None or self.max is not None):
            raise ValueError("only an int field has min and max")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min is greater than max")
        return self


class SheetSection(_Model):
    key: str = Field(min_length=1, max_length=60)
    label: str = Field(min_length=1, max_length=120)
    fields: list[SheetField] = Field(min_length=1)

    @model_validator(mode="after")
    def _distinct(self) -> "SheetSection":
        _unique_keys(self.fields, "field")
        return self


class SheetSource(_Model):
    """The rule heading a section was drafted from."""

    document_id: str = Field(alias="documentId")
    heading_path: list[str] = Field(alias="headingPath")


class Sheet(_Model):
    sections: list[SheetSection] = Field(min_length=1)
    sources: list[SheetSource] = Field(default_factory=list)

    @model_validator(mode="after")
    def _distinct(self) -> "Sheet":
        _unique_keys(self.sections, "section")
        return self


def validate_stats(sheet: Sheet, stats: dict[str, Any]) -> None:
    """Raise StatsInvalid unless `stats` is `{section: {field: value}}` with only keys
    the sheet has, each value of its field's type and range. A field may be left out
    or null: a sheet is filled in over time."""
    sections = {section.key: section for section in sheet.sections}
    for key, values in stats.items():
        section = sections.get(key)
        if section is None:
            raise StatsInvalid(f"stats.{key} is not a section of this system's sheet")
        _check(section.fields, values, f"stats.{key}")


def _check(fields: list[SheetField], values: Any, path: str) -> None:
    if not isinstance(values, dict):
        raise StatsInvalid(f"{path} must be an object")
    known = {field.key: field for field in fields}
    for key, value in values.items():
        where = f"{path}.{key}"
        field = known.get(key)
        if field is None:
            raise StatsInvalid(f"{where} is not on this system's sheet")
        if value is None:
            continue
        if field.type == "int":
            # bool is an int in Python; true is not a characteristic.
            if isinstance(value, bool) or not isinstance(value, int):
                raise StatsInvalid(f"{where} must be a whole number")
            if field.min is not None and value < field.min:
                raise StatsInvalid(f"{where} must be at least {field.min}")
            if field.max is not None and value > field.max:
                raise StatsInvalid(f"{where} must be at most {field.max}")
        elif field.type == "text":
            if not isinstance(value, str) or len(value) > MAX_TEXT:
                raise StatsInvalid(
                    f"{where} must be text of at most {MAX_TEXT} characters"
                )
        else:
            if not isinstance(value, list) or len(value) > MAX_ROWS:
                raise StatsInvalid(f"{where} must be a list of at most {MAX_ROWS} rows")
            for index, row in enumerate(value):
                _check(field.item_fields or [], row, f"{where}[{index}]")
