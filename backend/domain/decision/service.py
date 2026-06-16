"""Decision domain service — computes the final claim decision."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from backend.core.logging import get_logger

logger = get_logger(__name__)


class DecisionService:
    """Aggregates all agent results and produces the final claim decision."""

    def compute_decision(
        self,
        verification_result: dict[str, Any],
        extraction_result: dict[str, Any],
        policy_result: dict[str, Any],
        fraud_result: dict[str, Any],
        degradation_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Compute the final decision by aggregating all agent outputs.

        Decision priority:
        1. Document errors → error (should be caught before reaching here)
        2. Policy violations (waiting period, exclusions, limits) → REJECTED
        3. Fraud → MANUAL_REVIEW
        4. Partial approvals → PARTIAL
        5. Clean approval → APPROVED
        6. Degraded processing → lower confidence, manual_review_recommended
        7. All agents failed → MANUAL_REVIEW
        """
        decisions_found: list[str] = []
        reasons: list[str] = []
        approved_amount = Decimal("0")
        line_items: list[dict[str, Any]] = []
        rejection_reasons: list[str] = []

        # Process policy evaluation first
        policy_checks = policy_result.get("checks", [])
        policy_decision = policy_result.get("decision", "PROCEED")
        policy_line_items = policy_result.get("line_items", [])
        policy_rejection_reasons = policy_result.get("rejection_reasons", [])

        # Check for policy rule violations
        rejection_reasons.extend(policy_rejection_reasons)

        # Determine base decision from policy
        if policy_decision == "REJECTED":
            decisions_found.append("REJECTED")
        elif policy_decision == "PARTIAL":
            decisions_found.append("PARTIAL")
        elif policy_decision == "APPROVED":
            decisions_found.append("APPROVED")

        # Calculate approved amount from policy evaluation
        approved_amount = Decimal(str(policy_result.get("approved_amount", 0)))

        # Line item details
        for li in policy_line_items:
            line_items.append(
                {
                    "description": li.get("description", ""),
                    "amount": float(li.get("amount", 0)),
                    "approved_amount": float(li.get("approved_amount", 0)),
                    "is_covered": li.get("is_covered", True),
                    "rejection_reason": li.get("rejection_reason"),
                }
            )

        # Fraud assessment
        fraud_score = fraud_result.get("fraud_score", 0)
        fraud_recommendation = fraud_result.get("recommendation", "PROCEED")
        if fraud_recommendation == "MANUAL_REVIEW":
            decisions_found.append("MANUAL_REVIEW")

        # Compute final decision
        if "MANUAL_REVIEW" in decisions_found:
            final_decision = "MANUAL_REVIEW"
        elif "REJECTED" in decisions_found:
            final_decision = "REJECTED"
        elif "PARTIAL" in decisions_found:
            final_decision = "PARTIAL"
        elif "APPROVED" in decisions_found:
            final_decision = "APPROVED"
        else:
            final_decision = "MANUAL_REVIEW"  # Fallback

        # Fix TC005: REJECTED claims must show approved_amount = 0
        # (not the hypothetical calculated amount)
        if final_decision == "REJECTED":
            approved_amount = Decimal("0")
            # Also zero out line item approved amounts for rejected claims
            for li in line_items:
                li["approved_amount"] = 0.0

        # Compute confidence score
        confidence = self._compute_confidence(
            verification_result=verification_result,
            extraction_result=extraction_result,
            policy_result=policy_result,
            fraud_score=fraud_score,
            degradation_info=degradation_info,
        )

        # Build comprehensive reason
        reason_parts = []
        if reasons:
            reason_parts.extend(reasons)
        if fraud_recommendation == "MANUAL_REVIEW":
            fraud_signals = fraud_result.get("signals", [])
            for signal in fraud_signals:
                reason_parts.append(signal.get("detail", str(signal)))

        # Degradation handling
        manual_review_recommended = False
        degraded_components: list[str] = []
        if degradation_info:
            degraded_components = degradation_info.get("failed_components", [])
            manual_review_recommended = degradation_info.get("manual_review_recommended", False)

        # All agents failed → force MANUAL_REVIEW
        all_failed = degradation_info and degradation_info.get("all_agents_failed", False)
        if all_failed:
            final_decision = "MANUAL_REVIEW"
            confidence = 0.0
            manual_review_recommended = True
            reason_parts.append("All processing agents failed. Manual review required.")

        return {
            "decision": final_decision,
            "approved_amount": float(approved_amount),
            "confidence_score": confidence,
            "decision_reason": "; ".join(reason_parts)
            if reason_parts
            else ("Claim processed successfully" if final_decision == "APPROVED" else ""),
            "line_items": line_items,
            "rejection_reasons": rejection_reasons,
            "manual_review_recommended": manual_review_recommended,
            "degraded_components": degraded_components,
            "fraud_score": fraud_score,
        }

    def _compute_confidence(
        self,
        verification_result: dict[str, Any],
        extraction_result: dict[str, Any],
        policy_result: dict[str, Any],
        fraud_score: float = 0.0,
        degradation_info: dict[str, Any] | None = None,
    ) -> float:
        """Compute an overall confidence score (0.0-1.0)."""
        base = 1.0

        # Extraction confidence
        extraction_conf = extraction_result.get("overall_confidence", 1.0)
        base *= max(extraction_conf, 0.1)

        # Policy checks passed ratio — if rejection is due to policy rule (not error), keep confidence high
        checks = policy_result.get("checks", [])
        if checks:
            passed = sum(1 for c in checks if c.get("passed", True))
            # If ALL checks are for the same rejection (like excluded condition), don't penalize heavily
            check_ratio = max(passed / len(checks), 0.5)
            base *= 0.6 + 0.4 * check_ratio

        # Fraud score penalty
        if fraud_score > 0.3:
            base *= max(1.0 - fraud_score * 0.3, 0.5)

        # Degradation penalty
        if degradation_info:
            failed_count = len(degradation_info.get("failed_components", []))
            if failed_count > 0:
                # Each failed component reduces confidence
                degradation_penalty = 0.15 * failed_count
                base *= max(1.0 - degradation_penalty, 0.3)

        return round(max(min(base, 1.0), 0.0), 2)
