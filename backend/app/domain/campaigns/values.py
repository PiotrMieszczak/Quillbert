import re

from app.domain.shared import DomainError, ValidationFailed

MAX_NAME = 120
DEFAULT_TINT = "#E8B87A"
_TINT = re.compile(r"#[0-9A-Fa-f]{6}")


class UnknownSystem(DomainError):
    """The campaign names a system that is not in the system table (422)."""


def clean_name(name: str) -> str:
    cleaned = " ".join(name.split())
    if not cleaned:
        raise ValidationFailed("a campaign name is required")
    if len(cleaned) > MAX_NAME:
        raise ValidationFailed(f"campaign name is longer than {MAX_NAME} characters")
    return cleaned


def check_tint(tint: str) -> str:
    # The tint is written into CSS by the client, so only a plain hex colour passes.
    if not _TINT.fullmatch(tint):
        raise ValidationFailed("tint must be a hex colour like #E8B87A")
    return tint
