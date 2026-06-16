"""FastAPI claims endpoints."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, TokenPayload
from backend.api.dependencies import get_db_session
from backend.api.schemas.requests import (
    ClaimCategoryInfo,
    ClaimEventResponse,
    ClaimListResponse,
    ClaimResponse,
    ClaimRetryAttemptResponse,
    ClaimRetryRequest,
    ClaimSubmitAsyncResponse,
    ClaimSubmitRequest,
    DocumentErrorResponse,
    ErrorResponse,
    ProcessingTraceResponse,
)
from backend.core.logging import get_logger
from backend.domain.claims.service import ClaimsService

logger = get_logger(__name__)

router = APIRouter(prefix="/claims", tags=["claims"])

CATEGORY_LABELS = {
    "consultation": ("Consultation", "🩺"),
    "diagnostic": ("Diagnostic", "🔬"),
    "pharmacy": ("Pharmacy", "💊"),
    "dental": ("Dental", "🦷"),
    "vision": ("Vision", "👁️"),
    "alternative_medicine": ("Alternative Medicine", "🌿"),
}


@router.get("/categories", response_model=list[ClaimCategoryInfo])
async def get_claim_categories() -> list[ClaimCategoryInfo]:
    """Return claim categories covered by the policy.

    Reads from policy_terms.json via PolicyService. Only categories
    with ``covered: true`` are returned.
    """
    from backend.domain.policy.service import PolicyService

    policy_service = PolicyService.get_instance()
    opd_categories = policy_service.policy.get("opd_categories", {})

    categories: list[ClaimCategoryInfo] = []
    for key, config in opd_categories.items():
        if not config.get("covered", False):
            continue
        label, icon = CATEGORY_LABELS.get(key, (key.title(), "📋"))
        categories.append(
            ClaimCategoryInfo(
                value=key.upper(),
                label=label,
                icon=icon,
                sub_limit=float(config.get("sub_limit", 0)),
                copay_percent=float(config.get("copay_percent", 0)),
                requires_prescription=config.get("requires_prescription", False),
                requires_pre_auth=config.get("requires_pre_auth", False),
            )
        )

    return categories


@router.post(
    "",
    response_model=ClaimSubmitAsyncResponse,
    status_code=202,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def submit_claim(
    request: ClaimSubmitRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> ClaimSubmitAsyncResponse:
    """Submit a new health insurance claim for async processing.

    Returns 202 Accepted immediately. The claim is processed in the background
    via Celery. Poll GET /claims/{id} to track progress.
    """
    claims_service = ClaimsService(session)

    # Create the claim
    claim = await claims_service.create_claim(
        member_id=request.member_id,
        policy_id=request.policy_id,
        claim_category=request.claim_category.value,
        treatment_date=request.treatment_date,
        claimed_amount=request.claimed_amount,
        hospital_name=request.hospital_name,
    )

    # Add documents
    await claims_service.add_documents(
        claim_id=claim.claim_id,
        documents=[d.model_dump() for d in request.documents],
    )

    # Record SUBMITTED event
    await claims_service.create_event(
        claim_id=claim.claim_id,
        event_type="SUBMITTED",
        new_status="SUBMITTED",
        actor_type="USER",
        actor_id=current_user.sub,
    )

    await session.commit()

    # Dispatch async processing
    from backend.orchestrator.tasks import process_claim_async

    process_claim_async.delay(
        claim.claim_id,
        simulate_component_failure=getattr(request, 'simulate_component_failure', False),
        claims_history=getattr(request, 'claims_history', None),
    )

    logger.info("claim_submitted_async", claim_id=claim.claim_id, member_id=request.member_id)

    return ClaimSubmitAsyncResponse(
        claim_id=claim.claim_id,
        status="SUBMITTED",
        message="Claim submitted and is being processed.",
    )


@router.get("/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ClaimResponse:
    """Get full details for a specific claim, including decision and processing trace."""
    claims_service = ClaimsService(session)
    try:
        claim_data = await claims_service.get_claim_with_details(claim_id)
        return ClaimResponse(**claim_data)
    except Exception as e:
        raise HTTPException(status_code=404, detail={"error": {"message": str(e)}})


@router.get("/{claim_id}/trace", response_model=ProcessingTraceResponse)
async def get_claim_trace(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> ProcessingTraceResponse:
    """Get the full processing trace for a claim — every check, every decision, fully explainable."""
    claims_service = ClaimsService(session)
    try:
        claim_data = await claims_service.get_claim_with_details(claim_id)
        trace = claim_data.get("processing_trace", {})
        return ProcessingTraceResponse(**trace)
    except Exception as e:
        raise HTTPException(status_code=404, detail={"error": {"message": str(e)}})


@router.get("", response_model=ClaimListResponse)
async def list_claims(
    member_id: str | None = Query(None, description="Filter by member ID"),
    status: str | None = Query(None, description="Filter by claim status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> ClaimListResponse:
    """List claims with optional filtering."""
    claims_service = ClaimsService(session)
    claims, total = await claims_service.list_claims(
        member_id=member_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return ClaimListResponse(
        claims=[ClaimResponse(**c) for c in claims],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/upload",
    response_model=ClaimSubmitAsyncResponse,
    status_code=202,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def submit_claim_with_upload(
    member_id: str = Form(...),
    claim_category: str = Form(...),
    treatment_date: str = Form(...),
    claimed_amount: float = Form(...),
    hospital_name: str = Form(""),
    ytd_claims_amount: float = Form(0),
    claims_history: str = Form("[]"),
    simulate_component_failure: bool = Form(False),
    document_types: str = Form("[]"),
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> ClaimSubmitAsyncResponse:
    """Submit a claim with actual file uploads (multipart/form-data).

    Returns 202 Accepted immediately. The claim is processed asynchronously.
    """
    from backend.api.v1.documents import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES, validate_file
    from backend.core.container import get_container

    storage = get_container().storage

    # Parse document types
    try:
        doc_types = json.loads(document_types)
    except json.JSONDecodeError:
        doc_types = []

    # Parse claims history
    try:
        history = json.loads(claims_history)
    except json.JSONDecodeError:
        history = None

    # Upload files and build document metadata
    documents: list[dict[str, Any]] = []
    for i, file in enumerate(files):
        content_type = file.content_type or "application/octet-stream"
        validate_file(content_type, 0)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "FILE_TOO_LARGE", "message": f"File {file.filename} too large"}},
            )

        stored = await storage.upload(
            file_name=file.filename or f"doc_{i}",
            content=content,
            content_type=content_type,
        )

        doc_type = doc_types[i] if i < len(doc_types) else "PRESCRIPTION"
        doc_meta: dict[str, Any] = {
            "file_id": stored.file_id,
            "file_name": file.filename or f"doc_{i}",
            "actual_type": doc_type,
            "quality": "GOOD",
            "content_type": content_type,
            "file_path": stored.file_path,
            "file_size_bytes": stored.size_bytes,
        }

        if content_type.startswith("text/") or content_type == "application/json":
            try:
                doc_meta["content"] = content.decode("utf-8")
            except UnicodeDecodeError:
                pass

        documents.append(doc_meta)

    # Create claim
    claims_service = ClaimsService(session)

    claim = await claims_service.create_claim(
        member_id=member_id,
        policy_id="PLUM_GHI_2024",
        claim_category=claim_category.upper(),
        treatment_date=date.fromisoformat(treatment_date),
        claimed_amount=Decimal(str(claimed_amount)),
        hospital_name=hospital_name or None,
    )

    await claims_service.add_documents(
        claim_id=claim.claim_id,
        documents=documents,
    )

    # Record SUBMITTED event
    await claims_service.create_event(
        claim_id=claim.claim_id,
        event_type="SUBMITTED",
        new_status="SUBMITTED",
        actor_type="USER",
        actor_id=current_user.sub,
    )

    await session.commit()

    # Dispatch async processing
    from backend.orchestrator.tasks import process_claim_async

    process_claim_async.delay(
        claim.claim_id,
        simulate_component_failure=simulate_component_failure,
        claims_history=history,
    )

    logger.info("claim_submitted_async", claim_id=claim.claim_id, member_id=member_id)

    return ClaimSubmitAsyncResponse(
        claim_id=claim.claim_id,
        status="SUBMITTED",
        message="Claim submitted and is being processed.",
    )


@router.post(
    "/{claim_id}/retry",
    response_model=ClaimResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Claim not in retryable state"},
        404: {"model": ErrorResponse, "description": "Claim not found"},
    },
)
async def retry_claim(
    claim_id: int,
    request: ClaimRetryRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> ClaimResponse:
    """Retry a failed claim.

    Claim must be in DOCUMENT_ERROR, ERROR, or REJECTED status.
    Optionally attach new documents and a comment explaining the retry.
    """
    claims_service = ClaimsService(session)

    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    retryable_statuses = {"DOCUMENT_ERROR", "ERROR", "REJECTED"}
    if claim.status not in retryable_statuses:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": f"Claim is in '{claim.status}' status and cannot be retried"}},
        )

    # Add new documents if provided
    if request.documents:
        await claims_service.add_documents(
            claim_id=claim_id,
            documents=[d.model_dump() for d in request.documents],
        )

    # Create retry attempt record
    await claims_service.create_retry_attempt(
        claim_id=claim_id,
        retry_reason=request.comment,
        new_documents=[d.model_dump() for d in request.documents] if request.documents else None,
        requested_by=current_user.sub,
    )

    # Record RETRY_REQUESTED event
    await claims_service.create_event(
        claim_id=claim_id,
        event_type="RETRY_REQUESTED",
        previous_status=claim.status,
        new_status="SUBMITTED",
        actor_type="USER",
        actor_id=current_user.sub,
        comment=request.comment,
    )

    # Reset claim for retry
    await claims_service.reset_claim_for_retry(claim_id)

    await session.commit()

    # Dispatch async processing
    from backend.orchestrator.tasks import process_claim_async

    process_claim_async.delay(claim_id)

    logger.info("claim_retry_submitted", claim_id=claim_id, user=current_user.sub)

    claim_data = await claims_service.get_claim_with_details(claim_id)
    return ClaimResponse(**claim_data)


@router.post(
    "/{claim_id}/retry/upload",
    response_model=ClaimResponse,
    status_code=202,
    responses={
        400: {"model": ErrorResponse, "description": "Claim not in retryable state"},
        404: {"model": ErrorResponse, "description": "Claim not found"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)
async def retry_claim_with_upload(
    claim_id: int,
    files: list[UploadFile] = File(default_factory=list),
    document_types: str = Form("[]"),
    comment: str = Form(""),
    session: AsyncSession = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> ClaimResponse:
    """Retry a failed claim with new file uploads (multipart/form-data).

    Accepts new document files, uploads them to storage, and re-processes
    the claim. Claim must be in DOCUMENT_ERROR, ERROR, or REJECTED status.
    """
    from backend.api.v1.documents import ALLOWED_MIME_TYPES, MAX_FILE_SIZE_BYTES, validate_file
    from backend.core.container import get_container

    claims_service = ClaimsService(session)
    storage = get_container().storage

    # Verify claim exists and is retryable
    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    retryable_statuses = {"DOCUMENT_ERROR", "ERROR", "REJECTED"}
    if claim.status not in retryable_statuses:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": f"Claim is in '{claim.status}' status and cannot be retried"}},
        )

    # Parse document types
    try:
        doc_types = json.loads(document_types)
    except json.JSONDecodeError:
        doc_types = []

    # Upload files and build document metadata
    documents: list[dict[str, Any]] = []
    for i, file in enumerate(files):
        content_type = file.content_type or "application/octet-stream"
        validate_file(content_type, 0)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "FILE_TOO_LARGE", "message": f"File {file.filename} too large"}},
            )

        stored = await storage.upload(
            file_name=file.filename or f"doc_{i}",
            content=content,
            content_type=content_type,
        )

        doc_type = doc_types[i] if i < len(doc_types) else "PRESCRIPTION"
        doc_meta: dict[str, Any] = {
            "file_id": stored.file_id,
            "file_name": file.filename or f"doc_{i}",
            "actual_type": doc_type,
            "quality": "GOOD",
            "content_type": content_type,
            "file_path": stored.file_path,
            "file_size_bytes": stored.size_bytes,
        }

        if content_type.startswith("text/") or content_type == "application/json":
            try:
                doc_meta["content"] = content.decode("utf-8")
            except UnicodeDecodeError:
                pass

        documents.append(doc_meta)

    # Add new documents
    if documents:
        await claims_service.add_documents(
            claim_id=claim_id,
            documents=documents,
        )

    # Create retry attempt record
    await claims_service.create_retry_attempt(
        claim_id=claim_id,
        retry_reason=comment or None,
        new_documents=documents if documents else None,
        requested_by=current_user.sub,
    )

    # Record RETRY_REQUESTED event
    await claims_service.create_event(
        claim_id=claim_id,
        event_type="RETRY_REQUESTED",
        previous_status=claim.status,
        new_status="SUBMITTED",
        actor_type="USER",
        actor_id=current_user.sub,
        comment=comment or None,
    )

    # Reset claim for retry
    await claims_service.reset_claim_for_retry(claim_id)

    await session.commit()

    # Dispatch async processing
    from backend.orchestrator.tasks import process_claim_async

    process_claim_async.delay(claim_id)

    logger.info("claim_retry_upload_submitted", claim_id=claim_id, user=current_user.sub, file_count=len(files))

    claim_data = await claims_service.get_claim_with_details(claim_id)
    return ClaimResponse(**claim_data)


@router.get(
    "/{claim_id}/events",
    response_model=list[ClaimEventResponse],
)
async def get_claim_events(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> list[ClaimEventResponse]:
    """Get the full audit trail of events for a claim."""
    claims_service = ClaimsService(session)

    # Verify claim exists
    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    events = await claims_service.get_events(claim_id)
    return [ClaimEventResponse(**e) for e in events]


@router.get(
    "/{claim_id}/retries",
    response_model=list[ClaimRetryAttemptResponse],
)
async def get_claim_retries(
    claim_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> list[ClaimRetryAttemptResponse]:
    """Get the retry history for a claim."""
    claims_service = ClaimsService(session)

    # Verify claim exists
    claim = await claims_service.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail={"error": {"message": f"Claim {claim_id} not found"}})

    retries = await claims_service.get_retry_attempts(claim_id)
    return [ClaimRetryAttemptResponse(**r) for r in retries]
