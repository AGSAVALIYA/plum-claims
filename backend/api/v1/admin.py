"""Admin API endpoints for claims management."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import TokenPayload, get_current_admin
from backend.api.dependencies import get_db_session
from backend.api.schemas.requests import (
    AdminClaimListResponse,
    AdminCommentRequest,
    AdminDashboardResponse,
    AdminOverrideRequest,
    AdminResetPasswordRequest,
    ClaimEventResponse,
    ClaimResponse,
    ClaimRetryAttemptResponse,
    ErrorResponse,
    MemberDependentResponse,
    MemberDetailResponse,
    MemberClaimsSummaryResponse,
)
from backend.core.logging import get_logger
from backend.domain.claims.models import Claim
from backend.domain.claims.service import ClaimsService
from backend.domain.member.models import Member
from backend.domain.member.service import MemberService
from backend.domain.policy.service import PolicyService

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
async def get_dashboard(
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> AdminDashboardResponse:
    """Get dashboard statistics for admin."""
    claims_service = ClaimsService(session)
    stats = await claims_service.get_dashboard_stats()
    return AdminDashboardResponse(**stats)


@router.get("/claims", response_model=AdminClaimListResponse)
async def list_all_claims(
    member_id: str | None = Query(None, description="Filter by member ID"),
    status: str | None = Query(None, description="Filter by claim status"),
    decision: str | None = Query(None, description="Filter by decision"),
    date_from: str | None = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: str | None = Query(None, description="Filter to date (YYYY-MM-DD)"),
    claim_category: str | None = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> AdminClaimListResponse:
    """List all claims across all members with filters."""
    from sqlalchemy.orm import selectinload

    query = select(Claim).options(
        selectinload(Claim.documents),
        selectinload(Claim.line_items),
    )
    count_query = select(func.count(Claim.claim_id))

    if member_id:
        query = query.where(Claim.member_id == member_id)
        count_query = count_query.where(Claim.member_id == member_id)
    if status:
        query = query.where(Claim.status == status)
        count_query = count_query.where(Claim.status == status)
    if decision:
        query = query.where(Claim.decision == decision)
        count_query = count_query.where(Claim.decision == decision)
    if claim_category:
        query = query.where(Claim.claim_category == claim_category)
        count_query = count_query.where(Claim.claim_category == claim_category)
    if date_from:
        query = query.where(Claim.treatment_date >= date.fromisoformat(date_from))
        count_query = count_query.where(Claim.treatment_date >= date.fromisoformat(date_from))
    if date_to:
        query = query.where(Claim.treatment_date <= date.fromisoformat(date_to))
        count_query = count_query.where(Claim.treatment_date <= date.fromisoformat(date_to))

    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    query = query.order_by(Claim.submitted_at.desc()).offset(offset).limit(limit)
    result = await session.execute(query)
    claims = result.scalars().all()

    claims_service = ClaimsService(session)
    claim_dicts = [claims_service._claim_to_dict(c) for c in claims]

    return AdminClaimListResponse(
        claims=[ClaimResponse(**c) for c in claim_dicts],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_admin_claim_detail(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> ClaimResponse:
    """Get full claim detail including events and retries."""
    claims_service = ClaimsService(session)
    try:
        claim_data = await claims_service.get_claim_with_details(claim_id)
        return ClaimResponse(**claim_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail={"error": {"message": str(e)}})


@router.post(
    "/claims/{claim_id}/override",
    response_model=ClaimResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
    },
)
async def override_decision(
    claim_id: int,
    request: AdminOverrideRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> ClaimResponse:
    """Admin override of a claim decision."""
    claims_service = ClaimsService(session)

    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    previous_status = claim.status
    previous_decision = claim.decision

    # Update the claim decision
    claim.decision = request.decision
    claim.status = "DECIDED"
    claim.updated_at = datetime.now(UTC)
    if request.approved_amount is not None:
        claim.approved_amount = request.approved_amount
    if request.comment:
        claim.decision_reason = request.comment
    claim.processed_at = datetime.now(UTC)

    # Record ADMIN_OVERRIDE event
    await claims_service.create_event(
        claim_id=claim_id,
        event_type="ADMIN_OVERRIDE",
        previous_status=previous_status,
        new_status="DECIDED",
        actor_type="ADMIN",
        actor_id=admin.sub,
        comment=request.comment,
        metadata={
            "previous_decision": previous_decision,
            "new_decision": request.decision,
            "approved_amount": str(request.approved_amount) if request.approved_amount else None,
        },
    )

    await session.commit()

    claim_data = await claims_service.get_claim_with_details(claim_id)
    return ClaimResponse(**claim_data)


@router.post(
    "/claims/{claim_id}/comment",
    response_model=dict,
)
async def add_admin_comment(
    claim_id: int,
    request: AdminCommentRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> dict:
    """Add an admin comment to a claim."""
    claims_service = ClaimsService(session)

    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    await claims_service.create_event(
        claim_id=claim_id,
        event_type="COMMENT_ADDED",
        actor_type="ADMIN",
        actor_id=admin.sub,
        comment=request.comment,
    )

    await session.commit()

    return {"message": "Comment added", "claim_id": claim_id}


@router.get(
    "/claims/{claim_id}/events",
    response_model=list[ClaimEventResponse],
)
async def get_admin_claim_events(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> list[ClaimEventResponse]:
    """Get full audit trail for a claim (admin view)."""
    claims_service = ClaimsService(session)

    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    events = await claims_service.get_events(claim_id)
    return [ClaimEventResponse(**e) for e in events]


@router.get(
    "/claims/{claim_id}/retries",
    response_model=list[ClaimRetryAttemptResponse],
)
async def get_admin_claim_retries(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> list[ClaimRetryAttemptResponse]:
    """Get retry history for a claim (admin view)."""
    claims_service = ClaimsService(session)

    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    retries = await claims_service.get_retry_attempts(claim_id)
    return [ClaimRetryAttemptResponse(**r) for r in retries]


@router.post(
    "/claims/{claim_id}/rerun",
    response_model=ClaimResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def rerun_claim(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> ClaimResponse:
    """Rerun the full processing pipeline for a claim.

    Resets the claim to SUBMITTED, clears prior processing data,
    and dispatches async re-processing. Admin-only action.
    """
    claims_service = ClaimsService(session)

    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    # Prevent rerunning claims that are already in-flight
    if claim.status in ("SUBMITTED", "PROCESSING", "VALIDATING"):
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": f"Claim is currently in '{claim.status}' status and cannot be rerun until processing completes"}},
        )

    previous_status = claim.status
    previous_decision = claim.decision

    # Record the rerun event before resetting
    await claims_service.create_event(
        claim_id=claim_id,
        event_type="RETRY_REQUESTED",
        previous_status=previous_status,
        new_status="SUBMITTED",
        actor_type="ADMIN",
        actor_id=admin.sub,
        comment=f"Admin rerun requested. Previous status: {previous_status}, previous decision: {previous_decision}",
        metadata={
            "previous_decision": previous_decision,
            "previous_approved_amount": str(claim.approved_amount) if claim.approved_amount else None,
            "rerun_requested_by": admin.sub,
        },
    )

    # Reset claim for retry (clears processing steps, resets status)
    await claims_service.reset_claim_for_retry(claim_id)

    # Create a retry attempt record
    await claims_service.create_retry_attempt(
        claim_id=claim_id,
        retry_reason=f"Admin rerun by {admin.sub}",
        requested_by=admin.sub,
    )

    await session.commit()

    # Dispatch async processing
    from backend.orchestrator.tasks import process_claim_async
    process_claim_async.delay(claim_id)

    logger.info("admin_rerun_dispatched", claim_id=claim_id, admin=admin.sub, previous_status=previous_status)

    claim_data = await claims_service.get_claim_with_details(claim_id)
    return ClaimResponse(**claim_data)


@router.get("/members")
async def list_members(
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> list[dict[str, Any]]:
    """List all members with claim counts."""
    # Get all members
    result = await session.execute(select(Member).order_by(Member.member_id))
    members = result.scalars().all()

    # Get claim counts per member
    count_result = await session.execute(
        select(Claim.member_id, func.count(Claim.claim_id))
        .group_by(Claim.member_id)
    )
    claim_counts = {row[0]: row[1] for row in count_result.all()}

    return [
        {
            "member_id": m.member_id,
            "name": m.name,
            "role": m.role,
            "claim_count": claim_counts.get(m.member_id, 0),
        }
        for m in members
    ]


@router.get("/members/{member_id}", response_model=MemberDetailResponse)
async def get_member_detail(
    member_id: str,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> MemberDetailResponse:
    """Get detailed member profile with claims summary."""
    member_service = MemberService(session)

    member = await member_service.get_member(member_id)
    if member is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Member {member_id} not found"}})

    # Get claims summary for current year
    summary = await member_service.get_claims_summary(member_id)
    claims_summary = None
    if summary:
        claims_summary = MemberClaimsSummaryResponse(
            year=summary.year,
            total_claims_count=summary.total_claims_count or 0,
            total_claims_amount=float(summary.total_claims_amount or 0),
            approved_claims_count=summary.approved_claims_count or 0,
            approved_claims_amount=float(summary.approved_claims_amount or 0),
            last_claim_date=str(summary.last_claim_date) if summary.last_claim_date else None,
            family_approved_amount=float(summary.family_approved_amount or 0),
            family_combined_limit=float(summary.family_combined_limit or 0),
            sessions_used_this_year=summary.sessions_used_this_year or 0,
            same_day_claim_count=summary.same_day_claim_count or 0,
        )

    # Get dependents if this is a primary member
    dependents: list[MemberDependentResponse] = []
    if member.relationship == "SELF":
        dep_result = await session.execute(
            select(Member).where(Member.primary_member_id == member_id).order_by(Member.member_id)
        )
        for dep in dep_result.scalars().all():
            dependents.append(
                MemberDependentResponse(
                    member_id=dep.member_id,
                    name=dep.name,
                    relationship=dep.relationship,
                    date_of_birth=str(dep.date_of_birth) if dep.date_of_birth else None,
                )
            )

    return MemberDetailResponse(
        member_id=member.member_id,
        name=member.name,
        date_of_birth=str(member.date_of_birth) if member.date_of_birth else None,
        gender=member.gender,
        relationship=member.relationship,
        join_date=str(member.join_date) if member.join_date else None,
        primary_member_id=member.primary_member_id,
        role=member.role,
        claims_summary=claims_summary,
        dependents=dependents,
    )


@router.post("/members/{member_id}/reset-password")
async def reset_member_password(
    member_id: str,
    request: AdminResetPasswordRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: TokenPayload = Depends(get_current_admin),
) -> dict:
    """Reset a member's password. Admin-only."""
    member_service = MemberService(session)

    success = await member_service.set_password(member_id, request.new_password)
    if not success:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Member {member_id} not found"}})

    await session.commit()
    logger.info("admin_password_reset", member_id=member_id, admin=admin.sub)

    return {"message": f"Password reset for {member_id}", "member_id": member_id}


@router.get("/policy")
async def get_policy_config(
    admin: TokenPayload = Depends(get_current_admin),
) -> dict:
    """Return the full policy configuration from policy_terms.json."""
    policy_service = PolicyService.get_instance()
    return policy_service.policy
