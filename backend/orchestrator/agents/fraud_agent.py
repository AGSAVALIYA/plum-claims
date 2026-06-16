"""Fraud Detection Agent — assesses fraud risk signals with AI analysis."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.container import get_container
from backend.core.logging import get_logger
from backend.domain.fraud.service import FraudService
from backend.orchestrator.agents.base import BaseAgent
from backend.providers.llm.interface import LLMRequest

logger = get_logger(__name__)


class FraudAgent(BaseAgent):
    """Agent that detects fraud signals in a claim."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__("fraud_agent")
        self.session = session
        self.fraud_service = FraudService(session)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Assess fraud risk for the claim.

        Context must include:
        - member_id: str
        - treatment_date: str
        - claimed_amount: Decimal
        - claims_history: list (optional)
        """
        member_id = context.get("member_id", "")
        treatment_date_str = context.get("treatment_date", "")
        claimed_amount = Decimal(str(context.get("claimed_amount", 0)))
        claims_history = context.get("claims_history")

        treatment_date = date.fromisoformat(treatment_date_str)

        result = await self.fraud_service.assess_fraud(
            claim_id=context.get("claim_id", 0),
            member_id=member_id,
            treatment_date=treatment_date,
            claimed_amount=claimed_amount,
            claims_history=claims_history,
        )

        checks = []
        for signal in result.get("signals", []):
            checks.append(
                {
                    "check": signal.get("signal", "UNKNOWN"),
                    "passed": False,
                    "reason": signal.get("detail", ""),
                }
            )
        if not result.get("signals"):
            checks.append(
                {
                    "check": "NO_FRAUD_SIGNALS",
                    "passed": True,
                    "reason": "No fraud signals detected.",
                }
            )

        logger.info(
            "fraud_agent_done",
            claim_id=context.get("claim_id"),
            score=result["fraud_score"],
            recommendation=result["recommendation"],
        )

        # ── AI-Powered Fraud Analysis ───────────────────────────
        ai_score = result["fraud_score"]
        ai_flags: list[str] = []
        llm_usage: dict[str, int] = {}
        llm_cost = 0.0
        try:
            llm = get_container().llm
            ai_request = LLMRequest(
                messages=[
                    {"role": "system", "content": "You are a fraud detection expert for health insurance. Analyze this claim for fraud indicators. Return valid JSON with: {\"fraud_score\": 0-1, \"risk_level\": \"LOW|MEDIUM|HIGH\", \"indicators\": [\"list of fraud indicators\"], \"recommendation\": \"PROCEED|INVESTIGATE|BLOCK\"}"},
                    {"role": "user", "content": f"Claim: member={member_id}, amount=₹{claimed_amount}, date={treatment_date_str}, category={context.get('claim_category','')}, history={claims_history}, rule_signals={result.get('signals',[])}, rule_score={result['fraud_score']}"}
                ],
                response_schema={
                    "type": "object",
                    "properties": {
                        "fraud_score": {"type": "number"},
                        "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH"]},
                        "indicators": {"type": "array", "items": {"type": "string"}},
                        "recommendation": {"type": "string", "enum": ["PROCEED", "INVESTIGATE", "BLOCK"]}
                    },
                    "required": ["fraud_score", "risk_level", "recommendation"]
                },
                temperature=0.1,
                max_tokens=500,
            )
            ai_result = await llm.extract_structured(ai_request)
            # Track LLM usage/cost from the AI result
            if isinstance(ai_result, dict):
                llm_usage = ai_result.pop("_llm_usage", {})
                llm_cost = ai_result.pop("_llm_cost", 0.0)
            ai_score = max(result["fraud_score"], ai_result.get("fraud_score", 0))
            ai_flags = ai_result.get("indicators", [])
            checks.append({
                "check": "AI_FRAUD_ANALYSIS",
                "passed": ai_result.get("recommendation") == "PROCEED",
                "reason": f"AI risk: {ai_result.get('risk_level','?')}, score: {ai_result.get('fraud_score',0)}",
                "ai_recommendation": ai_result.get("recommendation"),
            })
        except Exception as e:
            logger.warning("ai_fraud_analysis_failed", error=str(e))

        return {
            "agent": self.name,
            "fraud_score": ai_score,
            "signals": result["signals"],
            "recommendation": result["recommendation"],
            "priority": result["priority"],
            "checks": checks,
            "confidence": 1.0 - ai_score,
            "ai_flags": ai_flags,
            "llm_usage": llm_usage,
            "llm_cost": llm_cost,
        }
