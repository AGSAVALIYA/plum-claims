"""Claim Orchestrator Engine — sequences agent execution with graceful degradation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.core.telemetry import (
    get_tracer,
    record_claim_decided,
    record_claim_submitted,
    record_agent_execution,
    record_fraud_score,
)
from backend.domain.claims.models import Claim
from backend.domain.claims.service import ClaimsService
from backend.domain.member.service import MemberService
from backend.domain.policy.service import PolicyService
from backend.orchestrator.agents.decision_agent import DecisionAgent
from backend.orchestrator.agents.extraction_agent import ExtractionAgent
from backend.orchestrator.agents.fraud_agent import FraudAgent
from backend.orchestrator.agents.policy_agent import PolicyAgent
from backend.orchestrator.agents.verification_agent import VerificationAgent
from backend.orchestrator.state import ProcessingStep, ProcessingTrace

logger = get_logger(__name__)


class ClaimOrchestrator:
    """Orchestrates the multi-agent claims processing pipeline.

    Flow:
    1. Document Verification → stop if invalid docs
    2. Document Extraction
    3. Policy Evaluation
    4. Fraud Detection
    5. Decision Aggregation
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.claims_service = ClaimsService(session)
        self.member_service = MemberService(session)
        self.policy_service = PolicyService.get_instance()
        self.verification_agent = VerificationAgent(session)
        self.extraction_agent = ExtractionAgent(session)
        self.policy_agent = PolicyAgent(session)
        self.fraud_agent = FraudAgent(session)
        self.decision_agent = DecisionAgent(session)

    async def process_claim(
        self,
        claim: Claim,
        uploaded_documents: list[dict[str, Any]],
        claims_history: list[dict[str, Any]] | None = None,
        ytd_claims_amount: Decimal | None = None,
        simulate_component_failure: bool = False,
    ) -> dict[str, Any]:
        """Process a claim through the full multi-agent pipeline.

        Returns the processing result including decision, amounts, and trace.
        """
        # Record claim submission metric
        record_claim_submitted(claim.claim_category)

        tracer = get_tracer()

        trace_obj = ProcessingTrace(claim_id=claim.claim_id)
        degradation_info: dict[str, Any] = {
            "failed_components": [],
            "manual_review_recommended": False,
            "all_agents_failed": False,
        }

        context = {
            "claim_id": claim.claim_id,
            "member_id": claim.member_id,
            "claim_category": claim.claim_category,
            "treatment_date": claim.treatment_date.isoformat(),
            "claimed_amount": claim.claimed_amount,
            "hospital_name": claim.hospital_name,
            "documents": uploaded_documents,
            "claims_history": claims_history,
            "ytd_claims_amount": ytd_claims_amount or Decimal("0"),
            "simulate_component_failure": simulate_component_failure,
        }

        # ── Step 1: Document Verification ───────────────────
        with tracer.start_as_current_span("claim.verification") as span:
            span.set_attribute("claim_id", claim.claim_id)
            step1 = ProcessingStep(
                step_index=0,
                step_name="Document Verification",
                agent_name="verification_agent",
            )
            step1.input_data = {
                "claim_category": claim.claim_category,
                "document_count": len(uploaded_documents),
            }

            verification_result = await self._execute_agent(
                self.verification_agent, context, step1, trace_obj
            )
            span.set_attribute("is_valid", verification_result.get("is_valid", False))

        # Persist verification status to the claim_documents table
        verified_docs = verification_result.get("documents", [])
        await self.claims_service.update_document_verification_status(
            claim_id=claim.claim_id,
            document_statuses=verified_docs,
        )

        await self.claims_service.add_processing_step(
            claim_id=claim.claim_id,
            step_index=step1.step_index,
            step_name=step1.step_name,
            agent_name=step1.agent_name,
            status=step1.status,
            input_data=step1.input_data,
            output_data=step1.output_data if step1.status == "COMPLETED" else {},
            error_message=step1.error_message,
            confidence_score=step1.confidence_score,
            checks_performed=verification_result.get("checks", []),
            started_at=step1.started_at,
            completed_at=step1.completed_at,
            duration_ms=step1.duration_ms,
        )

        # Stop pipeline if documents are invalid
        if not verification_result.get("is_valid", False):
            errors = verification_result.get("errors", [])
            error_messages = [e.get("message", "") for e in errors]
            # Persist document_errors and error_messages inside the processing_trace
            # so they survive the async task boundary and are visible in the API response.
            trace_dict = trace_obj.to_dict()
            trace_dict["document_errors"] = errors
            trace_dict["error_messages"] = error_messages
            await self.claims_service.update_claim_status(
                claim_id=claim.claim_id,
                status="DOCUMENT_ERROR",
                processing_trace=trace_dict,
            )
            return {
                "status": "DOCUMENT_ERROR",
                "document_errors": errors,
                "error_messages": error_messages,
                "processing_trace": trace_dict,
            }

        context["verification_result"] = verification_result

        # ── Step 2: Document Extraction ─────────────────────
        with tracer.start_as_current_span("claim.extraction") as span:
            span.set_attribute("claim_id", claim.claim_id)
            span.set_attribute("simulate_failure", simulate_component_failure)
            step2 = ProcessingStep(
                step_index=1,
                step_name="Document Extraction",
                agent_name="extraction_agent",
            )
            step2.input_data = {
                "document_count": len(uploaded_documents),
                "simulate_failure": simulate_component_failure,
            }

            extraction_result = await self._execute_agent(
                self.extraction_agent,
                context,
                step2,
                trace_obj,
                degrade_on_failure=True,
                degradation_info=degradation_info,
            )
            span.set_attribute("confidence", extraction_result.get("confidence", 0.0))
            span.set_attribute("degraded", trace_obj.degraded)
        await self.claims_service.add_processing_step(
            claim_id=claim.claim_id,
            step_index=step2.step_index,
            step_name=step2.step_name,
            agent_name=step2.agent_name,
            status=step2.status,
            input_data=step2.input_data,
            output_data=step2.output_data if step2.status == "COMPLETED" else {},
            error_message=step2.error_message,
            confidence_score=step2.confidence_score,
            checks_performed=extraction_result.get("checks", []),
            started_at=step2.started_at,
            completed_at=step2.completed_at,
            duration_ms=step2.duration_ms,
        )
        context["extraction_result"] = extraction_result

        # ── Steps 3 & 4: Policy Evaluation + Fraud Detection (parallel) ──
        step3 = ProcessingStep(
            step_index=2,
            step_name="Policy Evaluation",
            agent_name="policy_agent",
        )
        step3.input_data = {
            "claim_category": claim.claim_category,
            "claimed_amount": str(claim.claimed_amount),
            "hospital_name": claim.hospital_name,
        }

        step4 = ProcessingStep(
            step_index=3,
            step_name="Fraud Detection",
            agent_name="fraud_agent",
        )
        step4.input_data = {
            "member_id": claim.member_id,
            "treatment_date": claim.treatment_date.isoformat(),
            "claimed_amount": str(claim.claimed_amount),
        }

        async def _run_policy():
            with tracer.start_as_current_span("claim.policy_evaluation") as span:
                span.set_attribute("claim_id", claim.claim_id)
                result = await self._execute_agent(
                    self.policy_agent, context, step3, trace_obj,
                    degrade_on_failure=True, degradation_info=degradation_info,
                )
                span.set_attribute("decision", result.get("decision", "UNKNOWN"))
                span.set_attribute("degraded", trace_obj.degraded)
                return result

        async def _run_fraud():
            with tracer.start_as_current_span("claim.fraud_detection") as span:
                span.set_attribute("claim_id", claim.claim_id)
                result = await self._execute_agent(
                    self.fraud_agent, context, step4, trace_obj,
                    degrade_on_failure=True, degradation_info=degradation_info,
                )
                span.set_attribute("fraud_score", result.get("fraud_score", 0.0))
                span.set_attribute("degraded", trace_obj.degraded)
                return result

        policy_result, fraud_result = await asyncio.gather(
            _run_policy(),
            _run_fraud(),
            return_exceptions=True,
        )

        # Handle exceptions properly
        if isinstance(policy_result, Exception):
            logger.error("policy_agent_failed", error=str(policy_result))
            policy_result = {"agent": self.policy_agent.name, "checks": [], "confidence": 0.0, "decision": "PROCEED", "approved_amount": 0.0, "rejection_reasons": [], "line_items": []}
            degradation_info["failed_components"].append("policy_agent")
            degradation_info["manual_review_recommended"] = True
            step3.mark_failed(str(policy_result))

        if isinstance(fraud_result, Exception):
            logger.error("fraud_agent_failed", error=str(fraud_result))
            fraud_result = {"agent": self.fraud_agent.name, "fraud_score": 0.0, "signals": [], "recommendation": "PROCEED", "checks": []}
            degradation_info["failed_components"].append("fraud_agent")
            degradation_info["manual_review_recommended"] = True
            step4.mark_failed(str(fraud_result))

        await self.claims_service.add_processing_step(
            claim_id=claim.claim_id,
            step_index=step3.step_index,
            step_name=step3.step_name,
            agent_name=step3.agent_name,
            status=step3.status,
            input_data=step3.input_data,
            output_data=step3.output_data if step3.status == "COMPLETED" else {},
            error_message=step3.error_message,
            confidence_score=step3.confidence_score,
            checks_performed=policy_result.get("checks", []),
            started_at=step3.started_at,
            completed_at=step3.completed_at,
            duration_ms=step3.duration_ms,
        )
        context["policy_result"] = policy_result

        await self.claims_service.add_processing_step(
            claim_id=claim.claim_id,
            step_index=step4.step_index,
            step_name=step4.step_name,
            agent_name=step4.agent_name,
            status=step4.status,
            input_data=step4.input_data,
            output_data=step4.output_data if step4.status == "COMPLETED" else {},
            error_message=step4.error_message,
            confidence_score=step4.confidence_score,
            checks_performed=fraud_result.get("checks", []),
            started_at=step4.started_at,
            completed_at=step4.completed_at,
            duration_ms=step4.duration_ms,
        )
        context["fraud_result"] = fraud_result

        # ── Step 5: Decision Aggregation ────────────────────
        with tracer.start_as_current_span("claim.decision") as span:
            span.set_attribute("claim_id", claim.claim_id)
            step5 = ProcessingStep(
                step_index=4,
                step_name="Decision Aggregation",
                agent_name="decision_agent",
            )
            step5.input_data = {
                "verification": verification_result.get("is_valid"),
                "policy_decision": policy_result.get("decision"),
                "fraud_recommendation": fraud_result.get("recommendation"),
            }

            context["degradation_info"] = degradation_info
            decision_result = await self._execute_agent(
                self.decision_agent,
                context,
                step5,
                trace_obj,
                degrade_on_failure=False,
                degradation_info=degradation_info,
            )
            span.set_attribute("final_decision", decision_result.get("decision", "MANUAL_REVIEW"))
            span.set_attribute("confidence", decision_result.get("confidence_score", 0.0))
        await self.claims_service.add_processing_step(
            claim_id=claim.claim_id,
            step_index=step5.step_index,
            step_name=step5.step_name,
            agent_name=step5.agent_name,
            status=step5.status,
            input_data=step5.input_data,
            output_data=step5.output_data if step5.status == "COMPLETED" else {},
            error_message=step5.error_message,
            confidence_score=step5.confidence_score,
            checks_performed=decision_result.get("checks", []),
            started_at=step5.started_at,
            completed_at=step5.completed_at,
            duration_ms=step5.duration_ms,
        )

        # ── Update Claim ────────────────────────────────────
        trace_obj.completed_at = datetime.now(UTC)

        # Check if all agents failed
        if trace_obj.all_agents_failed:
            degradation_info["all_agents_failed"] = True

        manual_review = decision_result.get("manual_review_recommended", False)
        if degradation_info.get("all_agents_failed"):
            manual_review = True

        await self.claims_service.update_claim_status(
            claim_id=claim.claim_id,
            status="DECIDED",
            decision=decision_result.get("decision", "MANUAL_REVIEW"),
            approved_amount=Decimal(str(decision_result.get("approved_amount", 0))),
            decision_reason=decision_result.get("decision_reason", ""),
            confidence_score=decision_result.get("confidence_score", 0.0),
            processing_trace=trace_obj.to_dict(),
            manual_review_recommended=manual_review,
            degraded_components=degradation_info["failed_components"],
        )

        # Record decision metric
        record_claim_decided(decision_result.get("decision", "UNKNOWN"))

        # Record fraud score metric
        fraud_score = context.get("fraud_result", {}).get("fraud_score", 0)
        if fraud_score > 0:
            record_fraud_score(fraud_score)

        # Add line items to claim
        line_items = decision_result.get("line_items", [])
        if line_items:
            await self.claims_service.add_line_items(claim.claim_id, line_items)

        # Update member claims summary
        try:
            sessions_count = context.get("policy_result", {}).get("sessions_count", 0)
            await self.member_service.update_on_claim_decision(
                member_id=claim.member_id,
                approved_amount=Decimal(str(decision_result.get("approved_amount", 0))),
                treatment_date=claim.treatment_date,
                claim_category=claim.claim_category,
                sessions_count=sessions_count,
            )
        except Exception as e:
            logger.warning("member_summary_update_failed", error=str(e))

        return {
            "status": "DECIDED",
            "decision": decision_result,
            "processing_trace": trace_obj.to_dict(),
        }

    async def _execute_agent(
        self,
        agent,
        context: dict[str, Any],
        step: ProcessingStep,
        trace: ProcessingTrace,
        degrade_on_failure: bool = False,
        degradation_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an agent with graceful error handling."""
        import time

        empty_result = {
            "agent": agent.name,
            "checks": [],
            "confidence": 0.0,
            "overall_confidence": 0.0,  # Required by policy_agent graceful degradation check
        }
        start_time = time.monotonic()
        try:
            result = await agent.execute(context)
            step.complete(result)
            trace.add_step(step)

            # Track LLM cost per agent call
            llm_usage = result.get("llm_usage", {})
            llm_cost = result.get("llm_cost", 0.0)
            if llm_usage:
                input_tokens = llm_usage.get("input_tokens", 0)
                output_tokens = llm_usage.get("output_tokens", 0)
                trace.total_llm_tokens += input_tokens + output_tokens
            trace.total_llm_cost += llm_cost

            # Record agent execution metrics
            duration_s = time.monotonic() - start_time
            confidence = result.get("confidence", 0.0)
            record_agent_execution(agent.name, duration_s, confidence, success=True)

            return result
        except Exception as e:
            logger.error(
                "agent_failed",
                agent=agent.name,
                error=str(e),
                claim_id=context.get("claim_id"),
            )
            step.fail(str(e))
            trace.add_step(step)

            # Record failed agent execution
            duration_s = time.monotonic() - start_time
            record_agent_execution(agent.name, duration_s, 0.0, success=False)

            if degrade_on_failure and degradation_info is not None:
                trace.mark_degraded(agent.name)
                degradation_info["failed_components"].append(agent.name)
                degradation_info["manual_review_recommended"] = True

            return empty_result
