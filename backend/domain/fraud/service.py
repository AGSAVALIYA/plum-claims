"""Fraud detection domain service."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger

logger = get_logger(__name__)


class FraudService:
    """Evaluates fraud signals on a claim using configurable thresholds."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def assess_fraud(
        self,
        claim_id: int,
        member_id: str,
        treatment_date: date,
        claimed_amount: Decimal,
        claims_history: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Assess fraud risk for a claim.

        Returns a fraud assessment with score and signals.
        """
        from backend.core.container import get_container

        policy = get_container().policy_data
        fraud_thresholds = policy.get("fraud_thresholds", {})

        same_day_limit = int(fraud_thresholds.get("same_day_claims_limit", 2))
        monthly_limit = int(fraud_thresholds.get("monthly_claims_limit", 6))
        high_value_threshold = Decimal(
            str(fraud_thresholds.get("high_value_claim_threshold", 25000))
        )
        auto_manual_review_above = Decimal(
            str(fraud_thresholds.get("auto_manual_review_above", 25000))
        )
        fraud_score_threshold = Decimal(
            str(fraud_thresholds.get("fraud_score_manual_review_threshold", 0.80))
        )

        signals: list[dict[str, Any]] = []
        weights: dict[str, Decimal] = {
            "same_day_excess": Decimal("0.35"),
            "monthly_excess": Decimal("0.25"),
            "high_value": Decimal("0.20"),
            "alteration": Decimal("0.15"),
            "provider_concentration": Decimal("0.05"),
        }

        score = Decimal("0.0")

        # Signal 1: Same-day claims
        same_day_count = 0
        if claims_history:
            for hist in claims_history:
                hist_date = (
                    hist.get("date")
                    if isinstance(hist.get("date"), date)
                    else date.fromisoformat(str(hist["date"]))
                )
                if hist_date == treatment_date:
                    same_day_count += 1
            same_day_count += 1  # include current claim

            if same_day_count > same_day_limit:
                signals.append(
                    {
                        "signal": "SAME_DAY_CLAIMS_EXCEEDED",
                        "detail": (
                            f"Member has {same_day_count} claims on {treatment_date}. "
                            f"Limit is {same_day_limit} per day."
                        ),
                        "count": same_day_count,
                        "limit": same_day_limit,
                    }
                )
                score += weights["same_day_excess"]

        # Signal 2: Monthly claims
        if claims_history:
            monthly_count = sum(
                1
                for h in claims_history
                if date.fromisoformat(str(h["date"])).month == treatment_date.month
                and date.fromisoformat(str(h["date"])).year == treatment_date.year
            )
            monthly_count += 1
            if monthly_count > monthly_limit:
                signals.append(
                    {
                        "signal": "MONTHLY_CLAIMS_EXCEEDED",
                        "detail": (
                            f"Member has {monthly_count} claims this month. "
                            f"Limit is {monthly_limit} per month."
                        ),
                        "count": monthly_count,
                        "limit": monthly_limit,
                    }
                )
                score += weights["monthly_excess"]

        # Signal 3: High-value claim
        if claimed_amount > high_value_threshold:
            signals.append(
                {
                    "signal": "HIGH_VALUE_CLAIM",
                    "detail": (
                        f"Claimed amount ₹{claimed_amount} exceeds high-value "
                        f"threshold of ₹{high_value_threshold}."
                    ),
                    "claimed_amount": str(claimed_amount),
                    "threshold": str(high_value_threshold),
                }
            )
            score += weights["high_value"]

        # Signal 4: Auto manual review for very high claims
        if claimed_amount > auto_manual_review_above:
            signals.append(
                {
                    "signal": "AUTO_MANUAL_REVIEW",
                    "detail": (
                        f"Claimed amount ₹{claimed_amount} exceeds auto-review "
                        f"threshold of ₹{auto_manual_review_above}."
                    ),
                }
            )

        # Determine recommendation
        if score >= fraud_score_threshold:
            recommendation = "MANUAL_REVIEW"
            priority = "HIGH" if score > Decimal("0.90") else "NORMAL"
        elif score >= Decimal("0.30"):
            recommendation = "MANUAL_REVIEW"
            priority = "NORMAL"
        else:
            recommendation = "PROCEED"
            priority = "NONE"

        logger.info(
            "fraud_assessment_done",
            claim_id=claim_id,
            score=float(score),
            recommendation=recommendation,
            signal_count=len(signals),
        )

        return {
            "fraud_score": float(score),
            "signals": signals,
            "recommendation": recommendation,
            "priority": priority,
            "same_day_count": same_day_count if claims_history else 0,
        }
