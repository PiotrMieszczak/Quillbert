from app.ports.auth import Identity, InvalidToken


class DenyAllVerifier:
    """Fail-closed stand-in used when Supabase is not configured."""

    def verify(self, token: str) -> Identity:
        raise InvalidToken("authentication is not configured")
