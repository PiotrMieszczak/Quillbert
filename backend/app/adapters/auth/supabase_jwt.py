from typing import Any

import jwt
from jwt import PyJWKClient

from app.ports.auth import Identity, InvalidToken

# Supabase signs with an asymmetric key; the public half is served at the JWKS URL.
ALGORITHMS = ["ES256", "RS256"]
AUDIENCE = "authenticated"


class SupabaseJwtVerifier:
    """Verifies Supabase Auth access tokens. Issues none (ADR-0020)."""

    def __init__(self, project_url: str, jwks_client: Any = None) -> None:
        base = project_url.rstrip("/")
        self._issuer = f"{base}/auth/v1"
        self._jwks = jwks_client or PyJWKClient(f"{self._issuer}/.well-known/jwks.json")

    def verify(self, token: str) -> Identity:
        try:
            key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=ALGORITHMS,
                audience=AUDIENCE,
                issuer=self._issuer,
                options={"require": ["exp", "sub"]},
            )
        except jwt.PyJWTError as error:
            raise InvalidToken(str(error)) from error
        return Identity(user_id=claims["sub"], email=claims.get("email"))
