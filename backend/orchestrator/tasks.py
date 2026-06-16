"""Celery tasks for async claims processing."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from celery import Task

from backend.core.celery_app import celery_app
from backend.core.logging import get_logger, setup_logging
from backend.domain.claims.models import Claim
from backend.domain.claims.service import ClaimsService
from backend.domain.member.service import MemberService
from backend.orchestrator.engine import ClaimOrchestrator
from backend.providers.db.session import DatabaseSession

logger = get_logger(__name__)


def _run_async(coro):
    """Run an async coroutine in a sync Celery task context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="backend.orchestrator.tasks.process_claim_async",
    max_retries=0,
    acks_late=True,
)
def process_claim_async(
    self: Task,
    claim_id: int,
    simulate_component_failure: bool = False,
    claims_history: list[dict] | None = None,
) -> dict[str, Any]:
    """Process a claim through the multi-agent pipeline asynchronously.

    Creates its own DB session, runs the pipeline, and records events.
    """
    setup_logging()
    logger.info("async_processing_started", claim_id=claim_id)

    try:
        result = _run_async(_process_claim(claim_id, simulate_component_failure, claims_history))
        logger.info("async_processing_completed", claim_id=claim_id, status=result.get("status"))
        return result
    except Exception as e:
        logger.error("async_processing_failed", claim_id=claim_id, error=str(e))
        # Try to record the failure
        try:
            _run_async(_record_failure(claim_id, str(e)))
        except Exception:
            logger.error("failed_to_record_error", claim_id=claim_id)
        raise


async def _process_claim(
    claim_id: int,
    simulate_component_failure: bool = False,
    claims_history: list[dict] | None = None,
) -> dict[str, Any]:
    """Async implementation of claim processing.

    Creates its own DatabaseSession to avoid event loop conflicts
    with the FastAPI process's connection pool.
    """
    from backend.core.config import settings

    db = DatabaseSession(settings.database_url)
    try:
        async with db.session_factory() as session:
            claims_service = ClaimsService(session)

            # Load the claim
            claim = await claims_service.get_claim(claim_id)
            if claim is None:
                logger.error("claim_not_found", claim_id=claim_id)
                return {"status": "ERROR", "error": "Claim not found"}

            # Fetch YTD claims amount from member summary (auto-maintained by the system)
            member_service = MemberService(session)
            summary = await member_service.get_claims_summary(claim.member_id)
            ytd_claims_amount = summary.approved_claims_amount if summary else Decimal("0")

            # Guard against concurrent processing of the same claim
            if claim.status not in ("SUBMITTED", "DOCUMENT_ERROR", "ERROR"):
                logger.warning(
                    "claim_already_processing_or_decided",
                    claim_id=claim_id,
                    current_status=claim.status,
                )
                return {"status": claim.status, "error": f"Claim is already in '{claim.status}' status"}

            # Record PROCESSING_STARTED event
            await claims_service.create_event(
                claim_id=claim_id,
                event_type="PROCESSING_STARTED",
                previous_status=claim.status,
                new_status="PROCESSING",
                actor_type="SYSTEM",
                actor_id="celery_worker",
            )

            # Update claim status to PROCESSING
            claim.status = "PROCESSING"
            claim.updated_at = datetime.now(UTC)
            await session.commit()

            # Load documents from the claim
            from sqlalchemy.orm import selectinload
            from sqlalchemy import select

            result = await session.execute(
                select(Claim)
                .options(selectinload(Claim.documents))
                .where(Claim.claim_id == claim_id)
            )
            claim_with_docs = result.scalar_one()

            # Read actual file bytes from storage so extraction can process them
            from backend.core.container import get_container
            storage = get_container().storage

            documents = []
            for doc in claim_with_docs.documents:
                doc_dict: dict[str, Any] = {
                    "file_id": str(doc.document_id),
                    "file_name": doc.file_name,
                    "actual_type": doc.document_type or doc.detected_type,
                    "quality": "GOOD" if doc.quality_score and doc.quality_score >= 0.5 else "UNREADABLE",
                    "content_type": doc.content_type,
                    "file_path": doc.file_path,
                    "file_size_bytes": doc.file_size_bytes,
                    "patient_name_on_doc": doc.patient_name_on_doc,
                }

                # Check for pre-extracted content in extraction_data first
                extraction_data = doc.extraction_data or {}
                if extraction_data and isinstance(extraction_data, dict) and extraction_data:
                    doc_dict["content"] = extraction_data
                    documents.append(doc_dict)
                    continue

                # Read file bytes from storage for extraction
                try:
                    file_bytes = await storage.download(doc.file_path)
                    content_type = doc.content_type or ""

                    if content_type.startswith("text/") or content_type == "application/json":
                        # Text content: decode as UTF-8 string
                        try:
                            doc_dict["content"] = file_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            doc_dict["content"] = file_bytes.decode("latin-1", errors="replace")
                    elif content_type.startswith("image/"):
                        # Image content: base64-encode for vision LLM processing
                        import base64
                        doc_dict["content"] = {
                            "_image_base64": base64.b64encode(file_bytes).decode("ascii"),
                            "_image_mime": content_type,
                            "_file_name": doc.file_name,
                        }
                    elif content_type == "application/pdf":
                        # PDF: base64-encode for vision/PDF-capable LLM
                        import base64
                        doc_dict["content"] = {
                            "_pdf_base64": base64.b64encode(file_bytes).decode("ascii"),
                            "_file_name": doc.file_name,
                        }
                    else:
                        # Unknown type: try to treat as text
                        try:
                            doc_dict["content"] = file_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            logger.warning(
                                "unreadable_document_content",
                                file_name=doc.file_name,
                                content_type=content_type,
                            )
                except Exception as e:
                    logger.warning(
                        "document_read_failed",
                        file_name=doc.file_name,
                        file_path=doc.file_path,
                        error=str(e),
                    )

                documents.append(doc_dict)

            # Run the orchestrator pipeline
            orchestrator = ClaimOrchestrator(session)
            try:
                pipeline_result = await orchestrator.process_claim(
                    claim=claim,
                    uploaded_documents=documents,
                    claims_history=claims_history,
                    ytd_claims_amount=ytd_claims_amount,
                    simulate_component_failure=simulate_component_failure,
                )
            except Exception as pipeline_error:
                # Commit partial pipeline state (flushed processing steps) before re-raising
                logger.error("pipeline_failed_committing_partial_state", claim_id=claim_id, error=str(pipeline_error))
                claim.status = "ERROR"
                claim.updated_at = datetime.now(UTC)
                await claims_service.create_event(
                    claim_id=claim_id,
                    event_type="STEP_FAILED",
                    previous_status="PROCESSING",
                    new_status="ERROR",
                    actor_type="SYSTEM",
                    actor_id="orchestrator",
                    comment=str(pipeline_error),
                )
                await session.commit()
                raise

            # Record DECISION_MADE event
            final_status = pipeline_result.get("status", "DECIDED")
            await claims_service.create_event(
                claim_id=claim_id,
                event_type="DECISION_MADE",
                previous_status="PROCESSING",
                new_status=final_status,
                actor_type="SYSTEM",
                actor_id="orchestrator",
                metadata={
                    "decision": pipeline_result.get("decision", {}).get("decision"),
                    "status": final_status,
                },
            )

            await session.commit()

            return {
                "status": final_status,
                "claim_id": claim_id,
            }
    finally:
        await db.close()


async def _record_failure(claim_id: int, error_message: str) -> None:
    """Record a processing failure event and update claim status."""
    from backend.core.config import settings

    db = DatabaseSession(settings.database_url)
    try:
        async with db.session_factory() as session:
            claims_service = ClaimsService(session)

            claim = await claims_service.get_claim(claim_id)
            previous_status = claim.status if claim else "UNKNOWN"

            await claims_service.create_event(
                claim_id=claim_id,
                event_type="STEP_FAILED",
                previous_status=previous_status,
                new_status="ERROR",
                actor_type="SYSTEM",
                actor_id="celery_worker",
                comment=error_message,
            )

            if claim:
                claim.status = "ERROR"
                claim.updated_at = datetime.now(UTC)

            await session.commit()
    finally:
        await db.close()
