import logging

from fastapi import Depends, HTTPException, Request

from app.ports.auth import Identity, InvalidToken, TokenVerifier

logger = logging.getLogger(__name__)


def require_identity(request: Request) -> Identity:
    """Dependency: the authenticated caller, or 401."""
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized("missing bearer token")
    verifier: TokenVerifier = request.app.state.token_verifier
    try:
        return verifier.verify(token)
    except InvalidToken as error:
        logger.warning("rejected bearer token: %s", error)
        raise _unauthorized("invalid token") from error


def require_campaign(
    campaign_id: str, request: Request, identity: Identity = Depends(require_identity)
) -> Identity:
    """Dependency for routes under /campaigns/{campaign_id}: the caller must own it,
    or the route answers 404 as if it did not exist (DEC-005)."""
    request.app.state.get_campaign.execute(
        owner_id=identity.user_id, campaign_id=campaign_id
    )
    return identity


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})
