import json
from enum import StrEnum
from typing import Any

from app.domain.shared import ValidationFailed

MAX_TAGS = 20
MAX_TAG = 40
MAX_LEVEL = 99
# shortcut: a size cap stands in for shape checks until sheets validate stats (#126).
MAX_STATS_BYTES = 20_000


class Relationship(StrEnum):
    """How a character or faction stands toward the party; drives its colour."""

    ALLY = "ally"
    ENEMY = "enemy"
    FAMILY = "family"
    PROFESSIONAL = "professional"
    NEUTRAL = "neutral"


def clean_text(value: str | None) -> str | None:
    """Trimmed text, or None when nothing is left."""
    if value is None:
        return None
    return value.strip() or None


def clean_tags(tags: list[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for tag in tags:
        tag = " ".join(tag.split())
        if len(tag) > MAX_TAG:
            raise ValidationFailed(f"a tag is longer than {MAX_TAG} characters")
        if tag and tag not in cleaned:
            cleaned.append(tag)
    if len(cleaned) > MAX_TAGS:
        raise ValidationFailed(f"a character has at most {MAX_TAGS} tags")
    return tuple(cleaned)


def check_level(level: int | None) -> int | None:
    if level is not None and not 0 <= level <= MAX_LEVEL:
        raise ValidationFailed(f"level must be between 0 and {MAX_LEVEL}")
    return level


def check_stats(stats: dict[str, Any]) -> dict[str, Any]:
    if len(json.dumps(stats)) > MAX_STATS_BYTES:
        raise ValidationFailed(f"stats are larger than {MAX_STATS_BYTES} bytes")
    return stats
