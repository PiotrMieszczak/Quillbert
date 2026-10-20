from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class System:
    """A game system campaigns are played in (DEC-013). Reference data."""

    id: str
    name: str


@dataclass
class Campaign:
    """Mirrors docs/data-model.md `campaign`. Owned by one user (DEC-005)."""

    id: str
    owner_id: str
    name: str
    system: System
    tint: str
    created_at: datetime
    # Opaque FileStore key of the banner; None falls back to the tint.
    image_key: str | None = None
    last_played_at: date | None = None
