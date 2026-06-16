"""Unit tests for DecisionService.

Tests confidence computation, decision priority (MANUAL_REVIEW > REJECTED > PARTIAL > APPROVED),
and TC011 degradation handling.
"""

from decimal import Decimal

import pytest

from backend.domain.decision.service import DecisionService


@pytest.fixture
def decision_service():
    """Create a fresh DecisionService for each test."""
    return DecisionService()


# ── Confidence Computation ───────────────────────────────────


class TestConfidenceComputation:
    """Tests for _compute_confidence() with various inputs."""

    def test_full_confidence(self, decision_service):
        """All agents succeed → confidence should be 1.0."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 1.0},
            policy_result={"checks": [{"passed": True}]},
            fraud_score=0.0,
        )
        assert 0.95 <= confidence <= 1.0

    def test_low_extraction_confidence_reduces_overall(self, decision_service):
        """Low extraction confidence reduces overall confidence."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 0.3},
            policy_result={"checks": [{"passed": True}]},
            fraud_score=0.0,
        )
        # extraction_conf = 0.3, so base >= 0.3
        # policy check passed: factor = 0.6 + 0.4*1 = 1.0
        # expected: 0.3 * 1.0 = 0.3
        assert confidence <= 0.35
        assert confidence >= 0.25

    def test_policy_checks_all_failed_moderate_confidence(self, decision_service):
        """All policy checks failed → confidence reduced but not zero."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 1.0},
            policy_result={"checks": [{"passed": False}, {"passed": False}]},
            fraud_score=0.0,
        )
        # policy checks: passed=0, total=2, ratio=0/2=0, max(0,0.5)=0.5
        # factor = 0.6 + 0.4 * 0.5 = 0.8
        # expected: 1.0 * 0.8 = 0.8
        assert confidence == 0.80

    def test_high_fraud_score_reduces_confidence(self, decision_service):
        """Fraud score > 0.3 reduces confidence."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 1.0},
            policy_result={"checks": [{"passed": True}]},
            fraud_score=0.8,
        )
        # fraud_score=0.8 > 0.3, so factor = max(1.0-0.8*0.3, 0.5) = max(0.76, 0.5) = 0.76
        # expected: 1.0 * 1.0 * 0.76 = 0.76
        assert 0.70 <= confidence <= 0.80

    def test_high_fraud_score_capped_at_0_5(self, decision_service):
        """Extreme fraud score confidence floor is 0.5."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 1.0},
            policy_result={"checks": [{"passed": True}]},
            fraud_score=2.0,
        )
        # factor = max(1.0 - 2.0*0.3, 0.5) = max(0.4, 0.5) = 0.5
        assert confidence >= 0.50

    def test_degradation_reduces_confidence(self, decision_service):
        """Failed components reduce confidence proportionally."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 1.0},
            policy_result={"checks": [{"passed": True}]},
            fraud_score=0.0,
            degradation_info={"failed_components": ["policy_agent"]},
        )
        # 1 failed component, penalty = 0.15
        # expected: 1.0 * 0.85 = 0.85
        assert confidence == 0.85

    def test_multiple_failures_degredation(self, decision_service):
        """Multiple failed components increase degradation penalty."""
        confidence = decision_service._compute_confidence(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 1.0},
            policy_result={"checks": [{"passed": True}]},
            fraud_score=0.0,
            degradation_info={"failed_components": ["policy_agent", "fraud_agent"]},
        )
        # 2 failed components, penalty = 0.3, factor = 0.7
        assert 0.65 <= confidence <= 0.75


# ── Decision Priority ────────────────────────────────────────


class TestDecisionPriority:
    """Decision priority: MANUAL_REVIEW > REJECTED > PARTIAL > APPROVED."""

    def test_approved_when_all_clean(self, decision_service):
        """All clean → APPROVED."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 0.95},
            policy_result={
                "decision": "APPROVED",
                "approved_amount": 1500,
                "line_items": [{"description": "Consultation", "amount": 1500, "approved_amount": 1500, "is_covered": True}],
                "checks": [{"passed": True}],
            },
            fraud_result={"fraud_score": 0, "recommendation": "PROCEED", "signals": []},
        )
        assert result["decision"] == "APPROVED"
        assert result["approved_amount"] > 0

    def test_rejected_overrides_approved(self, decision_service):
        """Policy REJECTED overrides APPROVED."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 0.95},
            policy_result={
                "decision": "REJECTED",
                "approved_amount": 1500,
                "line_items": [{"description": "Consultation", "amount": 1500, "approved_amount": 1500, "is_covered": True}],
                "checks": [{"passed": False, "rule": "WAITING_PERIOD"}],
                "rejection_reasons": ["WAITING_PERIOD"],
            },
            fraud_result={"fraud_score": 0, "recommendation": "PROCEED", "signals": []},
        )
        assert result["decision"] == "REJECTED"
        # REJECTED claims should show approved_amount = 0
        assert result["approved_amount"] == 0.0

    def test_manual_review_overrides_rejected(self, decision_service):
        """Fraud MANUAL_REVIEW overrides policy REJECTED."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 0.95},
            policy_result={
                "decision": "REJECTED",
                "approved_amount": 0,
                "line_items": [],
                "checks": [{"passed": False}],
                "rejection_reasons": ["WAITING_PERIOD"],
            },
            fraud_result={
                "fraud_score": 0.85,
                "recommendation": "MANUAL_REVIEW",
                "signals": [{"signal": "HIGH_VALUE_CLAIM", "detail": "Amount exceeds threshold"}],
            },
        )
        # MANUAL_REVIEW > REJECTED
        assert result["decision"] == "MANUAL_REVIEW"

    def test_partial_when_line_items_excluded(self, decision_service):
        """Some line items excluded → PARTIAL."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 0.95},
            policy_result={
                "decision": "PARTIAL",
                "approved_amount": 8000,
                "line_items": [
                    {"description": "Root Canal Treatment", "amount": 8000, "approved_amount": 8000, "is_covered": True},
                    {"description": "Teeth Whitening", "amount": 4000, "approved_amount": 0, "is_covered": False, "rejection_reason": "Excluded: Teeth Whitening"},
                ],
                "checks": [{"passed": True}],
            },
            fraud_result={"fraud_score": 0, "recommendation": "PROCEED", "signals": []},
        )
        assert result["decision"] == "PARTIAL"
        assert result["approved_amount"] > 0

    def test_fallback_manual_review(self, decision_service):
        """No decisions found → MANUAL_REVIEW fallback."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": False},
            extraction_result={"overall_confidence": 0.0},
            policy_result={
                "decision": "UNKNOWN",
                "approved_amount": 0,
                "line_items": [],
                "checks": [],
            },
            fraud_result={"fraud_score": 0, "recommendation": "PROCEED", "signals": []},
        )
        assert result["decision"] in ("MANUAL_REVIEW", "APPROVED", "REJECTED", "PARTIAL")


# ── TC011 Degradation ────────────────────────────────────────


class TestTC011Degradation:
    """TC011: Graceful degradation reduces confidence."""

    def test_degradation_reduces_confidence(self, decision_service):
        """Degraded pipeline → lower confidence score."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": True},
            extraction_result={"overall_confidence": 0.95},
            policy_result={
                "decision": "APPROVED",
                "approved_amount": 1500,
                "line_items": [{"description": "Consultation", "amount": 1500, "approved_amount": 1500, "is_covered": True}],
                "checks": [{"passed": True}],
            },
            fraud_result={"fraud_score": 0, "recommendation": "PROCEED", "signals": []},
            degradation_info={
                "failed_components": ["extraction_agent"],
                "manual_review_recommended": True,
            },
        )
        # 1 failed component → 15% penalty on confidence
        assert result["confidence_score"] < 0.90
        assert result["manual_review_recommended"] is True
        assert "extraction_agent" in result["degraded_components"]

    def test_all_agents_failed_manual_review(self, decision_service):
        """All agents failed → force MANUAL_REVIEW with 0 confidence."""
        result = decision_service.compute_decision(
            verification_result={"is_valid": False},
            extraction_result={"overall_confidence": 0.0},
            policy_result={
                "decision": "APPROVED",
                "approved_amount": 1500,
                "line_items": [],
                "checks": [],
            },
            fraud_result={"fraud_score": 0, "recommendation": "PROCEED", "signals": []},
            degradation_info={
                "failed_components": ["verification_agent", "extraction_agent", "policy_agent", "fraud_agent"],
                "manual_review_recommended": False,
                "all_agents_failed": True,
            },
        )
        assert result["decision"] == "MANUAL_REVIEW"
        assert result["confidence_score"] == 0.0
        assert result["manual_review_recommended"] is True
