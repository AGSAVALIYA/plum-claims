"""JWT authentication middleware for the API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.core.config import settings

security_scheme = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """Decoded JWT token payload."""

    sub: str  # member_id
    role: str = "member"
    exp: int | None = None
    iat: int | None = None


def create_access_token(member_id: str, role: str = "member") -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": member_id,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiry_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "TOKEN_EXPIRED", "message": "Token has expired."}},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "INVALID_TOKEN", "message": "Invalid token."}},
        )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> TokenPayload:
    """Dependency: extract and validate the current user from JWT.

    In development mode (APP_ENV=development), allows unauthenticated requests
    with a default 'dev-user' identity.
    """
    if settings.app_env == "development" and settings.app_debug:
        if credentials is None:
            return TokenPayload(sub="dev-user", role="member")

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {"code": "MISSING_TOKEN", "message": "Authorization header required."}
            },
        )

    return decode_access_token(credentials.credentials)


async def get_current_admin(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Dependency: require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "FORBIDDEN", "message": "Admin role required."}},
        )
    return current_user
