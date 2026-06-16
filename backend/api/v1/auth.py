"""Authentication endpoints — login and register."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import create_access_token
from backend.api.dependencies import get_db_session
from backend.core.logging import get_logger
from backend.domain.member.service import MemberService

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    member_id: str
    password: str


class RegisterRequest(BaseModel):
    member_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    member_id: str
    member_name: str
    role: str = "member"


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Authenticate a member and return a JWT token."""
    member_service = MemberService(session)
    member = await member_service.authenticate(request.member_id, request.password)

    if member is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid member ID or password.",
                }
            },
        )

    token = create_access_token(member_id=member.member_id, role=member.role or "member")
    logger.info("member_login", member_id=member.member_id)

    return TokenResponse(
        access_token=token,
        member_id=member.member_id,
        member_name=member.name,
        role=member.role or "member",
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TokenResponse:
    """Register a member with a password (member must exist in policy)."""
    if len(request.password) < 4:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "WEAK_PASSWORD",
                    "message": "Password must be at least 4 characters.",
                }
            },
        )

    member_service = MemberService(session)
    member = await member_service.register_member(request.member_id, request.password)

    if member is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "MEMBER_NOT_FOUND",
                    "message": f"Member '{request.member_id}' not found in the policy roster.",
                }
            },
        )

    token = create_access_token(member_id=member.member_id, role="member")
    logger.info("member_registered", member_id=member.member_id)

    return TokenResponse(
        access_token=token,
        member_id=member.member_id,
        member_name=member.name,
        role="member",
    )
