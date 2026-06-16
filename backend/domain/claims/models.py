"""SQLAlchemy models for the Claims bounded context."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.providers.db.session import Base


class Claim(Base):
    """Core claims table."""

    __tablename__ = "claims"

    claim_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    member_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    policy_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    claim_category: Mapped[str] = mapped_column(Text, nullable=False)
    treatment_date: Mapped[date] = mapped_column(Date, nullable=False)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    decision: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="SUBMITTED")
    hospital_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    manual_review_recommended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    degraded_components: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    processing_trace: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    documents: Mapped[list[ClaimDocument]] = relationship(
        "ClaimDocument", back_populates="claim", cascade="all, delete-orphan"
    )
    line_items: Mapped[list[ClaimLineItem]] = relationship(
        "ClaimLineItem", back_populates="claim", cascade="all, delete-orphan"
    )
    processing_steps: Mapped[list[ClaimProcessingStep]] = relationship(
        "ClaimProcessingStep", back_populates="claim", cascade="all, delete-orphan"
    )
    events: Mapped[list[ClaimEvent]] = relationship(
        "ClaimEvent", back_populates="claim", cascade="all, delete-orphan"
    )
    retry_attempts: Mapped[list[ClaimRetryAttempt]] = relationship(
        "ClaimRetryAttempt", back_populates="claim", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "claim_category IN ('CONSULTATION','DIAGNOSTIC','PHARMACY','DENTAL','VISION','ALTERNATIVE_MEDICINE')",
            name="ck_claim_category",
        ),
        CheckConstraint(
            "status IN ('SUBMITTED','VALIDATING','PROCESSING','DECIDED','DOCUMENT_ERROR','ERROR','CLOSED')",
            name="ck_claim_status",
        ),
        CheckConstraint(
            "decision IS NULL OR decision IN ('APPROVED','PARTIAL','REJECTED','MANUAL_REVIEW')",
            name="ck_claim_decision",
        ),
        CheckConstraint("claimed_amount > 0", name="ck_claimed_amount_positive"),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1)",
            name="ck_confidence_range",
        ),
        Index("idx_claims_member_date", "member_id", "treatment_date"),
    )


class ClaimDocument(Base):
    """Documents attached to a claim."""

    __tablename__ = "claim_documents"

    document_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    claim_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("claims.claim_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    quality_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    verification_status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")
    patient_name_on_doc: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    claim: Mapped[Claim] = relationship("Claim", back_populates="documents")

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('PENDING','VERIFIED','WRONG_TYPE','UNREADABLE','PATIENT_MISMATCH','FAILED')",
            name="ck_doc_verification_status",
        ),
        CheckConstraint(
            "quality_score IS NULL OR (quality_score >= 0 AND quality_score <= 1)",
            name="ck_quality_range",
        ),
    )


class ClaimLineItem(Base):
    """Line items extracted from claim documents."""

    __tablename__ = "claim_line_items"

    line_item_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    claim_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("claims.claim_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    is_covered: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_match: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    claim: Mapped[Claim] = relationship("Claim", back_populates="line_items")

    __table_args__ = (CheckConstraint("amount >= 0", name="ck_line_item_amount_nonnegative"),)


class ClaimProcessingStep(Base):
    """Audit trail for each processing step in the pipeline."""

    __tablename__ = "claim_processing_steps"

    step_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    claim_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("claims.claim_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    input_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    output_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Numeric(3, 2), nullable=True)
    checks_performed: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    claim: Mapped[Claim] = relationship("Claim", back_populates="processing_steps")

    __table_args__ = (
        CheckConstraint(
            "status IN ('STARTED','COMPLETED','FAILED','SKIPPED')",
            name="ck_step_status",
        ),
        UniqueConstraint("claim_id", "step_index", name="uq_claim_step"),
    )


class ClaimEvent(Base):
    """Full audit trail for every state change on a claim."""

    __tablename__ = "claim_events"

    event_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    claim_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("claims.claim_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    previous_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_type: Mapped[str] = mapped_column(Text, nullable=False, default="SYSTEM")
    actor_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    claim: Mapped[Claim] = relationship("Claim", back_populates="events")

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('SUBMITTED','PROCESSING_STARTED','STEP_COMPLETED','STEP_FAILED',"
            "'RETRY_REQUESTED','RETRY_STARTED','DECISION_MADE','ADMIN_OVERRIDE','COMMENT_ADDED')",
            name="ck_event_type",
        ),
        CheckConstraint(
            "actor_type IN ('USER','SYSTEM','ADMIN')",
            name="ck_actor_type",
        ),
    )


class ClaimRetryAttempt(Base):
    """Tracks each retry of a claim."""

    __tablename__ = "claim_retry_attempts"

    retry_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    claim_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("claims.claim_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_step_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    new_documents: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    requested_by: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result_status: Mapped[str] = mapped_column(Text, nullable=False, default="PENDING")

    claim: Mapped[Claim] = relationship("Claim", back_populates="retry_attempts")

    __table_args__ = (
        CheckConstraint(
            "result_status IN ('PENDING','PROCESSING','SUCCEEDED','FAILED')",
            name="ck_retry_result_status",
        ),
    )
