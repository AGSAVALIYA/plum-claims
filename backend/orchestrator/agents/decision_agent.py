"""Decision Agent — aggregates all agent results with AI final decision."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.container import get_container
from backend.core.logging import get_logger
from backend.domain.decision.service import DecisionService
from backend.orchestrator.agents.base import BaseAgent
from backend.providers.llm.interface import LLMRequest

logger = get_logger(__name__)


class DecisionAgent(BaseAgent):
    """Agent that computes the final claim decision from all agent outputs."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__("decision_agent")
        self.session = session
        self.decision_service = DecisionService()

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Compute the final claim decision.

        Context must include:
        - verification_result: dict
        - extraction_result: dict
        - policy_result: dict
        - fraud_result: dict
        - degradation_info: dict (optional)
        """
        verification = context.get("verification_result", {})
        extraction = context.get("extraction_result", {})
        policy_result = context.get("policy_result", {})
        fraud_result = context.get("fraud_result", {})
        degradation_info = context.get("degradation_info")

        decision = self.decision_service.compute_decision(
            verification_result=verification,
            extraction_result=extraction,
            policy_result=policy_result,
            fraud_result=fraud_result,
            degradation_info=degradation_info,
        )

        checks = [
            {
                "check": "VERIFICATION",
                "passed": verification.get("is_valid", False),
                "reason": (
                    f"VERIFICATION check: Documents were {'verified successfully' if verification.get('is_valid') else 'NOT verified'}. "
                    f"Found {len(verification.get('errors', []))} error(s). "
                    f"Confidence: {verification.get('confidence', 0)}."
                ) if verification.get("is_valid") else (
                    f"VERIFICATION check FAILED: Document verification found {len(verification.get('errors', []))} error(s). "
                    f"Errors: {[e.get('error_type', 'UNKNOWN') for e in verification.get('errors', [])]}. "
                    f"Confidence: {verification.get('confidence', 0)}. "
                    f"Result: Pipeline should stop — document issues prevent processing."
                ),
            },
            {
                "check": "POLICY_EVALUATION",
                "passed": policy_result.get("decision") != "REJECTED",
                "reason": (
                    f"POLICY_EVALUATION check: Policy decision is '{policy_result.get('decision', 'UNKNOWN')}'. "
                    f"Approved amount: Rs.{policy_result.get('approved_amount', 0)}. "
                    f"Rejection reasons: {policy_result.get('rejection_reasons', [])}. "
                    f"Line items: {len(policy_result.get('line_items', []))} items processed."
                ),
            },
            {
                "check": "FRAUD_ASSESSMENT",
                "passed": fraud_result.get("recommendation") == "PROCEED",
                "reason": (
                    f"FRAUD_ASSESSMENT check: Recommendation is '{fraud_result.get('recommendation', 'UNKNOWN')}'. "
                    f"Fraud score: {fraud_result.get('fraud_score', 0)}. "
                    f"Signals: {fraud_result.get('signals', [])}. "
                    f"Confidence: {fraud_result.get('confidence', 0)}."
                ),
            },
        ]

        logger.info(
            "decision_agent_done",
            decision=decision["decision"],
            approved_amount=decision.get("approved_amount"),
            confidence=decision.get("confidence_score"),
        )

        # ── AI-Powered Final Decision ────────────────────────────
        ai_decision = decision["decision"]
        ai_reasoning = decision.get("decision_reason", "")
        llm_usage: dict[str, int] = {}
        llm_cost = 0.0
        try:
            llm = get_container().llm
            ai_request = LLMRequest(
                messages=[
                    {"role": "system", "content": "You are a senior health insurance claims adjudicator. Review all agent results and make a final decision. Return valid JSON with: {\"final_decision\": \"APPROVED|PARTIAL|REJECTED|MANUAL_REVIEW\", \"final_amount\": number, \"reasoning\": \"detailed explanation\", \"confidence\": 0-1, \"requires_human_review\": bool}"},
                    {"role": "user", "content": f"Verification: {verification}\nExtraction: {extraction}\nPolicy: {policy_result}\nFraud: {fraud_result}\nRule-based decision: {decision}"}
                ],
                response_schema={
                    "type": "object",
                    "properties": {
                        "final_decision": {"type": "string", "enum": ["APPROVED", "PARTIAL", "REJECTED", "MANUAL_REVIEW"]},
                        "final_amount": {"type": "number"},
                        "reasoning": {"type": "string"},
                        "confidence": {"type": "number"},
                        "requires_human_review": {"type": "boolean"}
                    },
                    "required": ["final_decision", "final_amount", "reasoning", "confidence"]
                },
                temperature=0.1,
                max_tokens=800,
            )
            ai_result = await llm.extract_structured(ai_request)
            # Track LLM usage/cost from the AI result
            if isinstance(ai_result, dict):
                llm_usage = ai_result.pop("_llm_usage", {})
                llm_cost = ai_result.pop("_llm_cost", 0.0)
            ai_decision = ai_result.get("final_decision", decision["decision"])
            ai_reasoning = ai_result.get("reasoning", "")
            checks.append({
                "check": "AI_FINAL_DECISION",
                "passed": ai_decision in ("APPROVED", "PARTIAL"),
                "reason": (
                    f"AI_FINAL_DECISION: AI proposes '{ai_decision}' with confidence "
                    f"{ai_result.get('confidence', 0.85)}. "
                    f"AI reasoning: {ai_reasoning[:300]}. "
                    f"Note: AI is strictly advisory — the rule-based decision "
                    f"('{rule_decision}') is authoritative."
                ),
                "ai_decision": ai_decision,
                "ai_confidence": ai_result.get("confidence", 0.85),
            })
        except Exception as e:
            logger.warning("ai_decision_failed", error=str(e))

        # ── Final decision: AI is strictly advisory ─────────────────
        # The rule-based pipeline produces the authoritative decision.
        # AI is used for additional reasoning and context, never to override.
        # The returned decision always comes from the deterministic rule pipeline.
        rule_decision = decision["decision"]

        # Build comprehensive decision reason summary
        reason_parts = []
        reason_parts.append(f"Final decision: {rule_decision}")
        reason_parts.append(f"Approved amount: Rs.{decision['approved_amount']}")
        reason_parts.append(f"Confidence: {decision['confidence_score']}")

        if decision.get("rejection_reasons"):
            reason_parts.append(f"Rejection reasons: {', '.join(decision['rejection_reasons'])}")

        if decision.get("manual_review_recommended"):
            reason_parts.append("Manual review recommended")

        if decision.get("degraded_components"):
            reason_parts.append(f"Degraded components: {', '.join(decision['degraded_components'])}")

        if decision.get("fraud_score", 0) > 0:
            reason_parts.append(f"Fraud score: {decision['fraud_score']}")

        # Add AI reasoning as supplementary context
        if ai_reasoning:
            reason_parts.append(f"AI analysis: {ai_reasoning[:200]}")

        reason_parts.append(f"Line items: {len(decision['line_items'])} processed")
        covered_items = sum(1 for li in decision['line_items'] if li.get('is_covered', False))
        reason_parts.append(f"Covered line items: {covered_items}/{len(decision['line_items'])}")

        combined_reason = " | ".join(reason_parts)

        return {
            "agent": self.name,
            "decision": rule_decision,
            "approved_amount": decision["approved_amount"],
            "confidence_score": decision["confidence_score"],
            "decision_reason": combined_reason,
            "line_items": decision["line_items"],
            "rejection_reasons": decision.get("rejection_reasons", []),
            "manual_review_recommended": decision.get("manual_review_recommended", False),
            "degraded_components": decision.get("degraded_components", []),
            "fraud_score": decision.get("fraud_score", 0),
            "checks": checks,
            "confidence": decision["confidence_score"],
            "llm_usage": llm_usage,
            "llm_cost": llm_cost,
        }
