"""Claims domain service — manages claim lifecycle and pipeline dispatch."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import ResourceNotFoundError
from backend.core.logging import get_logger
from backend.core.serialization import to_json_safe
from backend.domain.claims.models import (
    Claim,
    ClaimDocument,
    ClaimEvent,
    ClaimLineItem,
    ClaimProcessingStep,
    ClaimRetryAttempt,
)

logger = get_logger(__name__)


class ClaimsService:
    """Manages the full claim lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_claim(
        self,
        member_id: str,
        policy_id: str,
        claim_category: str,
        treatment_date: date,
        claimed_amount: Decimal,
        hospital_name: str | None = None,
    ) -> Claim:
        """Create a new claim in SUBMITTED status."""
        claim = Claim(
            member_id=member_id,
            policy_id=policy_id,
            claim_category=claim_category.upper(),
            treatment_date=treatment_date,
            claimed_amount=claimed_amount,
            hospital_name=hospital_name,
            status="SUBMITTED",
            manual_review_recommended=False,
            degraded_components=[],
            processing_trace={},
            submitted_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.session.add(claim)
        await self.session.flush()
        logger.info(
            "claim_created",
            claim_id=claim.claim_id,
            member_id=member_id,
            category=claim_category,
        )
        return claim

    async def add_documents(
        self,
        claim_id: int,
        documents: list[dict[str, Any]],
    ) -> list[ClaimDocument]:
        """Attach document metadata to a claim."""
        doc_objs = []
        for doc in documents:
            cd = ClaimDocument(
                claim_id=claim_id,
                file_name=doc.get("file_name", f"doc_{doc.get('file_id', 'unknown')}"),
                file_path=doc.get("file_path", f"/uploads/{doc.get('file_id', 'unknown')}"),
                file_size_bytes=doc.get("file_size_bytes"),
                content_type=doc.get("content_type", "application/octet-stream"),
                document_type=doc.get("actual_type"),
                detected_type=doc.get("actual_type"),
                extraction_data=to_json_safe(doc.get("content") or {}),
                quality_score=Decimal("1.0")
                if doc.get("quality", "GOOD") == "GOOD"
                else Decimal("0.0"),
                verification_status="PENDING",
                patient_name_on_doc=doc.get("patient_name_on_doc"),
                created_at=datetime.now(UTC),
            )
            self.session.add(cd)
            doc_objs.append(cd)
        await self.session.flush()
        return doc_objs

    async def update_document_verification_status(
        self,
        claim_id: int,
        document_statuses: list[dict[str, Any]],
    ) -> None:
        """Persist verification status for documents after verification step.

        Args:
            claim_id: The claim ID.
            document_statuses: List of dicts with file_id (str) and verification_result.
                               file_id maps to ClaimDocument.document_id (cast to int).
        """
        for ds in document_statuses:
            file_id_str = ds.get("file_id", "")
            try:
                doc_id = int(file_id_str)
            except (ValueError, TypeError):
                logger.warning(
                    "invalid_document_id_for_verification_update",
                    file_id=file_id_str,
                    claim_id=claim_id,
                )
                continue

            doc = await self.session.get(ClaimDocument, doc_id)
            if doc is None:
                logger.warning(
                    "document_not_found_for_verification_update",
                    document_id=doc_id,
                    claim_id=claim_id,
                )
                continue

            is_verified = ds.get("is_verified", False)
            new_status = "VERIFIED" if is_verified else "FAILED"

            # Check for specific error types from the verification result
            # (these are available on the full errors list, not per-document)
            doc.verification_status = new_status
            logger.info(
                "document_verification_updated",
                document_id=doc_id,
                file_name=doc.file_name,
                old_status="PENDING",
                new_status=new_status,
            )

        await self.session.flush()

    async def add_line_items(
        self,
        claim_id: int,
        line_items: list[dict[str, Any]],
    ) -> list[ClaimLineItem]:
        """Add line items to a claim."""
        items = []
        for li in line_items:
            item = ClaimLineItem(
                claim_id=claim_id,
                description=li.get("description", ""),
                quantity=li.get("quantity", 1),
                unit_rate=Decimal(str(li.get("unit_rate", 0))) if li.get("unit_rate") else None,
                amount=Decimal(str(li.get("amount", 0))),
                approved_amount=(
                    Decimal(str(li.get("approved_amount", 0)))
                    if li.get("approved_amount") is not None
                    else None
                ),
                is_covered=li.get("is_covered"),
                rejection_reason=li.get("rejection_reason"),
                category_match=li.get("category_match"),
                created_at=datetime.now(UTC),
            )
            self.session.add(item)
        await self.session.flush()
        return items

    async def add_processing_step(
        self,
        claim_id: int,
        step_index: int,
        step_name: str,
        agent_name: str,
        status: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        error_message: str | None = None,
        confidence_score: float | None = None,
        checks_performed: list[dict[str, Any]] | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        duration_ms: int | None = None,
    ) -> ClaimProcessingStep:
        """Record a processing step in the audit trail."""
        step = ClaimProcessingStep(
            claim_id=claim_id,
            step_index=step_index,
            step_name=step_name,
            agent_name=agent_name,
            status=status,
            input_data=to_json_safe(input_data) if input_data else {},
            output_data=to_json_safe(output_data) if output_data else {},
            error_message=error_message,
            confidence_score=(
                Decimal(str(confidence_score)) if confidence_score is not None else None
            ),
            checks_performed=to_json_safe(checks_performed) if checks_performed else [],
            started_at=started_at or datetime.now(UTC),
            completed_at=completed_at or datetime.now(UTC),
            duration_ms=duration_ms,
            created_at=datetime.now(UTC),
        )
        self.session.add(step)
        await self.session.flush()
        return step

    async def update_claim_status(
        self,
        claim_id: int,
        status: str,
        decision: str | None = None,
        approved_amount: Decimal | None = None,
        decision_reason: str | None = None,
        confidence_score: float | None = None,
        processing_trace: dict[str, Any] | None = None,
        manual_review_recommended: bool = False,
        degraded_components: list[str] | None = None,
    ) -> Claim:
        """Update a claim's status and decision."""
        claim = await self.session.get(Claim, claim_id)
        if claim is None:
            raise ResourceNotFoundError("Claim", claim_id)

        claim.status = status
        if decision:
            claim.decision = decision
        if approved_amount is not None:
            claim.approved_amount = approved_amount
        if decision_reason:
            claim.decision_reason = decision_reason
        if confidence_score is not None:
            claim.confidence_score = Decimal(str(round(confidence_score, 2)))
        if processing_trace:
            claim.processing_trace = to_json_safe(processing_trace)
        claim.manual_review_recommended = manual_review_recommended
        if degraded_components is not None:
            claim.degraded_components = to_json_safe(degraded_components)
        claim.processed_at = datetime.now(UTC)
        claim.updated_at = datetime.now(UTC)

        await self.session.flush()
        logger.info(
            "claim_updated",
            claim_id=claim_id,
            status=status,
            decision=decision,
        )
        return claim

    async def get_claim(self, claim_id: int) -> Claim | None:
        """Get a claim by ID."""
        result = await self.session.execute(select(Claim).where(Claim.claim_id == claim_id))
        return result.scalar_one_or_none()

    async def get_claim_with_details(self, claim_id: int) -> dict[str, Any]:
        """Get full claim details including documents, line items, and processing trace."""
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(Claim)
            .options(
                selectinload(Claim.documents),
                selectinload(Claim.line_items),
                selectinload(Claim.processing_steps),
            )
            .where(Claim.claim_id == claim_id)
        )
        claim = result.scalar_one_or_none()
        if claim is None:
            raise ResourceNotFoundError("Claim", claim_id)

        return self._claim_to_dict(claim)

    async def list_claims(
        self,
        member_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """List claims with optional filters."""
        from sqlalchemy.orm import selectinload

        query = select(Claim).options(
            selectinload(Claim.documents),
            selectinload(Claim.line_items),
        )
        count_query = select(Claim)

        if member_id:
            query = query.where(Claim.member_id == member_id)
            count_query = count_query.where(Claim.member_id == member_id)
        if status:
            query = query.where(Claim.status == status)
            count_query = count_query.where(Claim.status == status)

        query = query.order_by(Claim.submitted_at.desc()).offset(offset).limit(limit)

        from sqlalchemy import func

        count_result = await self.session.execute(
            select(func.count()).select_from(count_query.subquery())
        )
        total = count_result.scalar() or 0

        result = await self.session.execute(query)
        claims = [self._claim_to_dict(c) for c in result.scalars().all()]

        return claims, total

    async def create_event(
        self,
        claim_id: int,
        event_type: str,
        actor_type: str = "SYSTEM",
        actor_id: str | None = None,
        comment: str | None = None,
        previous_status: str | None = None,
        new_status: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ClaimEvent:
        """Record an audit event for a claim."""
        event = ClaimEvent(
            claim_id=claim_id,
            event_type=event_type,
            previous_status=previous_status,
            new_status=new_status,
            actor_type=actor_type,
            actor_id=actor_id,
            comment=comment,
            event_metadata=to_json_safe(metadata) if metadata else {},
            created_at=datetime.now(UTC),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def get_events(self, claim_id: int) -> list[dict[str, Any]]:
        """Get all events for a claim ordered by created_at."""
        result = await self.session.execute(
            select(ClaimEvent)
            .where(ClaimEvent.claim_id == claim_id)
            .order_by(ClaimEvent.created_at.asc())
        )
        events = result.scalars().all()
        return [
            {
                "event_id": e.event_id,
                "claim_id": e.claim_id,
                "event_type": e.event_type,
                "previous_status": e.previous_status,
                "new_status": e.new_status,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "comment": e.comment,
                "metadata": e.event_metadata,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    async def create_retry_attempt(
        self,
        claim_id: int,
        retry_reason: str | None = None,
        failed_step_index: int | None = None,
        new_documents: list[dict[str, Any]] | None = None,
        requested_by: str = "unknown",
    ) -> ClaimRetryAttempt:
        """Create a retry attempt record for a claim."""
        # Get the next attempt number
        result = await self.session.execute(
            select(ClaimRetryAttempt)
            .where(ClaimRetryAttempt.claim_id == claim_id)
            .order_by(ClaimRetryAttempt.attempt_number.desc())
            .limit(1)
        )
        last_attempt = result.scalar_one_or_none()
        next_number = (last_attempt.attempt_number + 1) if last_attempt else 1

        retry = ClaimRetryAttempt(
            claim_id=claim_id,
            attempt_number=next_number,
            retry_reason=retry_reason,
            failed_step_index=failed_step_index,
            new_documents=to_json_safe(new_documents) if new_documents else None,
            requested_by=requested_by,
            requested_at=datetime.now(UTC),
            result_status="PENDING",
        )
        self.session.add(retry)
        await self.session.flush()
        return retry

    async def get_retry_attempts(self, claim_id: int) -> list[dict[str, Any]]:
        """Get all retry attempts for a claim."""
        result = await self.session.execute(
            select(ClaimRetryAttempt)
            .where(ClaimRetryAttempt.claim_id == claim_id)
            .order_by(ClaimRetryAttempt.attempt_number.asc())
        )
        retries = result.scalars().all()
        return [
            {
                "retry_id": r.retry_id,
                "claim_id": r.claim_id,
                "attempt_number": r.attempt_number,
                "retry_reason": r.retry_reason,
                "failed_step_index": r.failed_step_index,
                "new_documents": r.new_documents,
                "requested_by": r.requested_by,
                "requested_at": r.requested_at.isoformat() if r.requested_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "result_status": r.result_status,
            }
            for r in retries
        ]

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """Get aggregate dashboard statistics for admin."""
        from sqlalchemy import func

        # Total claims by status
        status_result = await self.session.execute(
            select(Claim.status, func.count(Claim.claim_id))
            .group_by(Claim.status)
        )
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # Decision counts
        decision_result = await self.session.execute(
            select(Claim.decision, func.count(Claim.claim_id))
            .where(Claim.decision.isnot(None))
            .group_by(Claim.decision)
        )
        decision_counts = {row[0]: row[1] for row in decision_result.all()}

        # Average confidence
        avg_result = await self.session.execute(
            select(func.avg(Claim.confidence_score))
            .where(Claim.confidence_score.isnot(None))
        )
        avg_confidence = float(avg_result.scalar() or 0)

        # Total claims
        total_result = await self.session.execute(select(func.count(Claim.claim_id)))
        total_claims = total_result.scalar() or 0

        # Recent events (last 10)
        recent_events_result = await self.session.execute(
            select(ClaimEvent)
            .order_by(ClaimEvent.created_at.desc())
            .limit(10)
        )
        recent_events = [
            {
                "event_id": e.event_id,
                "claim_id": e.claim_id,
                "event_type": e.event_type,
                "actor_type": e.actor_type,
                "comment": e.comment,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent_events_result.scalars().all()
        ]

        # Manual review count
        review_result = await self.session.execute(
            select(func.count(Claim.claim_id))
            .where(Claim.manual_review_recommended == True)
        )
        manual_review_count = review_result.scalar() or 0

        return {
            "total_claims": total_claims,
            "status_counts": status_counts,
            "decision_counts": decision_counts,
            "avg_confidence": round(avg_confidence, 2),
            "manual_review_count": manual_review_count,
            "recent_events": recent_events,
        }

    async def reset_claim_for_retry(self, claim_id: int) -> Claim:
        """Reset a claim for retry processing."""
        claim = await self.session.get(Claim, claim_id)
        if claim is None:
            raise ResourceNotFoundError("Claim", claim_id)

        claim.status = "SUBMITTED"
        claim.decision = None
        claim.decision_reason = None
        claim.confidence_score = None
        claim.approved_amount = None
        claim.processed_at = None
        claim.manual_review_recommended = False
        claim.degraded_components = []
        claim.processing_trace = {}
        claim.updated_at = datetime.now(UTC)

        # Delete old processing steps and line items
        from sqlalchemy import delete

        await self.session.execute(
            delete(ClaimProcessingStep).where(ClaimProcessingStep.claim_id == claim_id)
        )
        await self.session.execute(
            delete(ClaimLineItem).where(ClaimLineItem.claim_id == claim_id)
        )

        await self.session.flush()
        return claim

    def _claim_to_dict(self, claim: Claim) -> dict[str, Any]:
        """Convert a Claim ORM object to a dictionary."""
        trace = claim.processing_trace or {}
        return {
            "claim_id": claim.claim_id,
            "member_id": claim.member_id,
            "policy_id": claim.policy_id,
            "claim_category": claim.claim_category,
            "treatment_date": claim.treatment_date.isoformat() if claim.treatment_date else None,
            "claimed_amount": float(claim.claimed_amount) if claim.claimed_amount is not None else None,
            "approved_amount": float(claim.approved_amount) if claim.approved_amount is not None else None,
            "decision": claim.decision,
            "decision_reason": claim.decision_reason,
            "confidence_score": float(claim.confidence_score) if claim.confidence_score is not None else None,
            "status": claim.status,
            "hospital_name": claim.hospital_name,
            "manual_review_recommended": claim.manual_review_recommended,
            "degraded_components": claim.degraded_components,
            "processing_trace": trace,
            "document_errors": trace.get("document_errors"),
            "error_messages": trace.get("error_messages"),
            "submitted_at": claim.submitted_at.isoformat() if claim.submitted_at else None,
            "processed_at": claim.processed_at.isoformat() if claim.processed_at else None,
            "documents": [
                {
                    "document_id": d.document_id,
                    "file_name": d.file_name,
                    "document_type": d.document_type,
                    "detected_type": d.detected_type,
                    "verification_status": d.verification_status,
                    "quality_score": float(d.quality_score) if d.quality_score is not None else None,
                    "patient_name_on_doc": d.patient_name_on_doc,
                    "error_message": d.error_message,
                }
                for d in (claim.documents if hasattr(claim, "documents") else [])
            ],
            "line_items": [
                {
                    "line_item_id": li.line_item_id,
                    "description": li.description,
                    "amount": float(li.amount),
                    "approved_amount": float(li.approved_amount) if li.approved_amount is not None else None,
                    "is_covered": li.is_covered,
                    "rejection_reason": li.rejection_reason,
                }
                for li in (claim.line_items if hasattr(claim, "line_items") else [])
            ],
        }
