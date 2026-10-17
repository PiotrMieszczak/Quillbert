import time
from types import SimpleNamespace

import jwt
import pytest
from app.adapters.auth.deny_all import DenyAllVerifier
from app.adapters.auth.supabase_jwt import SupabaseJwtVerifier
from app.ports.auth import InvalidToken
from cryptography.hazmat.primitives.asymmetric import ec

PROJECT = "https://abc.supabase.co"
ISSUER = f"{PROJECT}/auth/v1"


class _Jwks:
    def __init__(self, public_key) -> None:
        self._key = SimpleNamespace(key=public_key)

    def get_signing_key_from_jwt(self, _token: str):
        return self._key


@pytest.fixture(scope="module")
def private_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture
def verifier(private_key) -> SupabaseJwtVerifier:
    return SupabaseJwtVerifier(PROJECT, _Jwks(private_key.public_key()))


def _token(key, **overrides) -> str:
    claims = {
        "sub": "user-1",
        "email": "gm@ashfall.table",
        "aud": "authenticated",
        "iss": ISSUER,
        "exp": int(time.time()) + 60,
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="ES256")


def test_valid_token_yields_identity(verifier, private_key) -> None:
    identity = verifier.verify(_token(private_key))
    assert identity.user_id == "user-1"
    assert identity.email == "gm@ashfall.table"


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 10},
        {"aud": "anon"},
        {"iss": "https://evil.example/auth/v1"},
    ],
)
def test_bad_claims_are_rejected(verifier, private_key, overrides) -> None:
    token = _token(private_key, **overrides)
    with pytest.raises(InvalidToken):
        verifier.verify(token)


def test_token_without_subject_is_rejected(verifier, private_key) -> None:
    claims = {"aud": "authenticated", "iss": ISSUER, "exp": int(time.time()) + 60}
    token = jwt.encode(claims, private_key, algorithm="ES256")
    with pytest.raises(InvalidToken):
        verifier.verify(token)


def test_token_signed_by_another_key_is_rejected(verifier) -> None:
    other = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(InvalidToken):
        verifier.verify(_token(other))


def test_garbage_is_rejected(verifier) -> None:
    with pytest.raises(InvalidToken):
        verifier.verify("not-a-jwt")


def test_deny_all_rejects_everything() -> None:
    with pytest.raises(InvalidToken):
        DenyAllVerifier().verify("anything")
