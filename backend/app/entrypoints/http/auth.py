from fastapi import HTTPException, Request

from app.ports.auth import Identity, InvalidToken, TokenVerifier


def require_identity(request: Request) -> Identity:
    """Dependency: the authenticated caller, or 401."""
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("missing bearer token")
    verifier: TokenVerifier = request.app.state.token_verifier
    try:
        return verifier.verify(token)
    except InvalidToken as error:
        raise _unauthorized("invalid token") from error


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})
