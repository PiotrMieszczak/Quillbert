from dataclasses import dataclass
from typing import Protocol


class InvalidToken(Exception):
    """The bearer token is missing, malformed, expired, or not ours."""


@dataclass(frozen=True)
class Identity:
    user_id: str
    email: str | None


class TokenVerifier(Protocol):
    def verify(self, token: str) -> Identity:
        """Return the caller, or raise InvalidToken."""
        ...
