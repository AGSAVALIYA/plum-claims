"""Unit tests for FraudService.

Tests fraud signal detection in isolation: same-day claims, high-value claims,
monthly excess, and empty history edge cases.
"""

from datetime import date
from decimal import Decimal

import pytest

from backend.domain.fraud.service import FraudService


@pytest.mark.asyncio
class TestFraudService:
    """Tests for FraudService.assess_fraud()."""

    async def test_same_day_claims_triggers_flag(self, db_session):
        """3+ claims on the same day should trigger SAME_DAY_CLAIMS_EXCEEDED."""
        service = FraudService(db_session)
        claims_history = [
            {"claim_id": 1, "date": date(2026, 6, 4), "amount": 100.0},
            {"claim_id": 2, "date": date(2026, 6, 4), "amount": 200.0},
            {"claim_id": 3, "date": date(2026, 6, 4), "amount": 300.0},
        ]

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("150"),
            claims_history=claims_history,
        )

        signals = result.get("signals", [])
        signal_types = [s["signal"] for s in signals]
        assert "SAME_DAY_CLAIMS_EXCEEDED" in signal_types, (
            f"Expected SAME_DAY_CLAIMS_EXCEEDED signal. Got: {signal_types}"
        )
        assert result["fraud_score"] > 0

    async def test_same_day_below_threshold_no_flag(self, db_session):
        """2 claims on the same day should NOT trigger SAME_DAY_CLAIMS_EXCEEDED."""
        service = FraudService(db_session)
        claims_history = [
            {"claim_id": 1, "date": date(2026, 6, 4), "amount": 100.0},
            {"claim_id": 2, "date": date(2026, 6, 5), "amount": 200.0},
        ]

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("150"),
            claims_history=claims_history,
        )

        signal_types = [s["signal"] for s in result.get("signals", [])]
        assert "SAME_DAY_CLAIMS_EXCEEDED" not in signal_types

    async def test_high_value_claim_triggers_review(self, db_session):
        """Claim amount > 25000 should trigger HIGH_VALUE_CLAIM signal."""
        service = FraudService(db_session)

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("30000"),
            claims_history=[],
        )

        signals = result.get("signals", [])
        signal_types = [s["signal"] for s in signals]
        assert "HIGH_VALUE_CLAIM" in signal_types, (
            f"Expected HIGH_VALUE_CLAIM signal for Rs.30000. Got: {signal_types}"
        )
        assert result["fraud_score"] > 0

    async def test_high_value_below_threshold_no_flag(self, db_session):
        """Claim amount <= 25000 should NOT trigger HIGH_VALUE_CLAIM."""
        service = FraudService(db_session)

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("25000"),
            claims_history=[],
        )

        signal_types = [s["signal"] for s in result.get("signals", [])]
        assert "HIGH_VALUE_CLAIM" not in signal_types

    async def test_empty_history_no_fraud_signals(self, db_session):
        """Empty claims history should result in no fraud signals."""
        service = FraudService(db_session)

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("500"),
            claims_history=None,
        )

        assert result["fraud_score"] == 0.0
        assert result["recommendation"] == "PROCEED"
        assert len(result.get("signals", [])) == 0

    async def test_recommendation_proceed_for_low_risk(self, db_session):
        """Low-value, single-day claim should get PROCEED recommendation."""
        service = FraudService(db_session)

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("1500"),
            claims_history=[{"claim_id": 1, "date": date(2026, 6, 1), "amount": 500.0}],
        )

        assert result["recommendation"] == "PROCEED"
        assert result["priority"] == "NONE"

    async def test_monthly_excess_triggers_flag(self, db_session):
        """More than 6 claims in a month should trigger MONTHLY_CLAIMS_EXCEEDED."""
        service = FraudService(db_session)
        # 7 previous claims in the same month
        claims_history = [
            {"claim_id": i, "date": date(2026, 6, d), "amount": 100.0}
            for i, d in enumerate(range(1, 8), start=1)
        ]

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 10),
            claimed_amount=Decimal("150"),
            claims_history=claims_history,
        )

        signal_types = [s["signal"] for s in result.get("signals", [])]
        assert "MONTHLY_CLAIMS_EXCEEDED" in signal_types, (
            f"Expected MONTHLY_CLAIMS_EXCEEDED. Got: {signal_types}"
        )

    async def test_fraud_score_aggregation(self, db_session):
        """Multiple signals should accumulate fraud score."""
        service = FraudService(db_session)
        # Same-day + high-value should produce a higher score
        claims_history = [
            {"claim_id": 1, "date": date(2026, 6, 4), "amount": 100.0},
            {"claim_id": 2, "date": date(2026, 6, 4), "amount": 200.0},
            {"claim_id": 3, "date": date(2026, 6, 4), "amount": 300.0},
        ]

        result = await service.assess_fraud(
            claim_id=100,
            member_id="EMP001",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("30000"),
            claims_history=claims_history,
        )

        # Both signals should be present
        signal_types = [s["signal"] for s in result.get("signals", [])]
        assert "SAME_DAY_CLAIMS_EXCEEDED" in signal_types
        assert "HIGH_VALUE_CLAIM" in signal_types
        # Score should be sum of weights: 0.35 + 0.20 = 0.55
        assert 0.50 <= result["fraud_score"] <= 0.60
