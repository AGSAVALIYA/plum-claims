"""Pydantic request/response schemas for the Claims API."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ── Enums ───────────────────────────────────────────────────


class ClaimCategory(str, Enum):
    CONSULTATION = "CONSULTATION"
    DIAGNOSTIC = "DIAGNOSTIC"
    PHARMACY = "PHARMACY"
    DENTAL = "DENTAL"
    VISION = "VISION"
    ALTERNATIVE_MEDICINE = "ALTERNATIVE_MEDICINE"


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    VALIDATING = "VALIDATING"
    PROCESSING = "PROCESSING"
    DECIDED = "DECIDED"
    DOCUMENT_ERROR = "DOCUMENT_ERROR"
    ERROR = "ERROR"
    CLOSED = "CLOSED"


class Decision(str, Enum):
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


# ── Request Schemas ─────────────────────────────────────────


class DocumentMeta(BaseModel):
    """Metadata about an uploaded document (for JSON-based test mode).

    content can be:
    - A dict with pre-extracted structured data (skips LLM extraction)
    - A string with raw text (triggers LLM extraction via Gemini)
    - None (no content to extract)
    """

    file_id: str
    file_name: str
    actual_type: str
    quality: str = "GOOD"
    patient_name_on_doc: str | None = None
    content: dict[str, Any] | str | None = None


class ClaimSubmitRequest(BaseModel):
    """Request to submit a new claim."""

    member_id: str = Field(..., description="Member ID (e.g., EMP001)")
    policy_id: str = Field(default="PLUM_GHI_2024")
    claim_category: ClaimCategory
    treatment_date: date
    claimed_amount: Decimal = Field(..., gt=0)
    hospital_name: str | None = None
    ytd_claims_amount: Decimal = Field(default=Decimal("0"))
    documents: list[DocumentMeta] = Field(default_factory=list)
    claims_history: list[dict[str, Any]] | None = None
    simulate_component_failure: bool = False


# ── Response Schemas ────────────────────────────────────────


class DocumentErrorResponse(BaseModel):
    error_type: str
    document_id: int | str | None = None
    file_name: str | None = None
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class LineItemResponse(BaseModel):
    description: str
    amount: float
    approved_amount: float | None = None
    is_covered: bool | None = None
    rejection_reason: str | None = None


class ProcessingStepResponse(BaseModel):
    step_index: int
    step_name: str
    agent_name: str
    status: str
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    confidence_score: float | None = None
    checks_performed: list[dict[str, Any]] = Field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None


class ProcessingTraceResponse(BaseModel):
    claim_id: int
    steps: list[ProcessingStepResponse] = Field(default_factory=list)
    started_at: str | None = None
    completed_at: str | None = None
    failed_components: list[str] = Field(default_factory=list)
    degraded: bool = False
    all_agents_failed: bool = False


class DocumentResponse(BaseModel):
    document_id: int
    file_name: str
    document_type: str | None = None
    detected_type: str | None = None
    verification_status: str
    quality_score: float | None = None
    patient_name_on_doc: str | None = None
    error_message: str | None = None


class ClaimResponse(BaseModel):
    claim_id: int
    member_id: str
    policy_id: str
    claim_category: str
    treatment_date: str | None = None
    claimed_amount: float | None = None
    approved_amount: float | None = None
    decision: str | None = None
    decision_reason: str | None = None
    confidence_score: float | None = None
    status: str
    hospital_name: str | None = None
    manual_review_recommended: bool = False
    degraded_components: list[str] = Field(default_factory=list)
    processing_trace: dict[str, Any] | None = None
    submitted_at: str | None = None
    processed_at: str | None = None
    documents: list[DocumentResponse] = Field(default_factory=list)
    line_items: list[LineItemResponse] = Field(default_factory=list)
    document_errors: list[DocumentErrorResponse] | None = None
    error_messages: list[str] | None = None


class ClaimListResponse(BaseModel):
    claims: list[ClaimResponse] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


class ErrorResponse(BaseModel):
    error: dict[str, Any]


class ClaimSubmitAsyncResponse(BaseModel):
    """Response for async claim submission (202 Accepted)."""

    claim_id: int
    status: str = "SUBMITTED"
    message: str = "Claim submitted and is being processed."


class ClaimEventResponse(BaseModel):
    event_id: int
    claim_id: int
    event_type: str
    previous_status: str | None = None
    new_status: str | None = None
    actor_type: str
    actor_id: str | None = None
    comment: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None


class ClaimRetryAttemptResponse(BaseModel):
    retry_id: int
    claim_id: int
    attempt_number: int
    retry_reason: str | None = None
    failed_step_index: int | None = None
    new_documents: list[dict[str, Any]] | None = None
    requested_by: str
    requested_at: str | None = None
    completed_at: str | None = None
    result_status: str


class ClaimRetryRequest(BaseModel):
    """Request to retry a failed claim."""

    comment: str | None = None
    documents: list[DocumentMeta] = Field(default_factory=list)


class AdminOverrideRequest(BaseModel):
    """Admin override of a claim decision."""

    decision: str = Field(..., description="APPROVED, REJECTED, or MANUAL_REVIEW")
    comment: str | None = None
    approved_amount: Decimal | None = None


class AdminCommentRequest(BaseModel):
    """Admin comment on a claim."""

    comment: str


class AdminDashboardResponse(BaseModel):
    total_claims: int
    status_counts: dict[str, int] = Field(default_factory=dict)
    decision_counts: dict[str, int] = Field(default_factory=dict)
    avg_confidence: float = 0.0
    manual_review_count: int = 0
    recent_events: list[dict[str, Any]] = Field(default_factory=list)


class AdminClaimListResponse(BaseModel):
    claims: list[ClaimResponse] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


# ── Claim Categories ─────────────────────────────────────


class ClaimCategoryInfo(BaseModel):
    value: str
    label: str
    icon: str
    sub_limit: float
    copay_percent: float
    requires_prescription: bool = False
    requires_pre_auth: bool = False


# ── Admin: Member Detail ─────────────────────────────────


class MemberDependentResponse(BaseModel):
    member_id: str
    name: str
    relationship: str
    date_of_birth: str | None = None


class MemberClaimsSummaryResponse(BaseModel):
    year: int
    total_claims_count: int = 0
    total_claims_amount: float = 0
    approved_claims_count: int = 0
    approved_claims_amount: float = 0
    last_claim_date: str | None = None
    family_approved_amount: float = 0
    family_combined_limit: float = 0
    sessions_used_this_year: int = 0
    same_day_claim_count: int = 0


class MemberDetailResponse(BaseModel):
    member_id: str
    name: str
    date_of_birth: str | None = None
    gender: str | None = None
    relationship: str | None = None
    join_date: str | None = None
    primary_member_id: str | None = None
    role: str = "member"
    claims_summary: MemberClaimsSummaryResponse | None = None
    dependents: list[MemberDependentResponse] = Field(default_factory=list)


class AdminResetPasswordRequest(BaseModel):
    new_password: str = Field(..., min_length=4, description="New password (min 4 characters)")
