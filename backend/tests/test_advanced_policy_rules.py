"""Tests for advanced policy rules: branded drugs, family floater, sessions limit, and exclusion math sequence."""

import unittest.mock as mock
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from backend.domain.claims.service import ClaimsService
from backend.domain.member.models import Member
from backend.domain.policy.service import PolicyService
from backend.orchestrator.engine import ClaimOrchestrator


class TestAdvancedPolicyRules:
    """Integration tests for advanced policy evaluation rules."""

    @pytest.mark.asyncio
    async def test_exclusion_applied_before_discount_and_copay(self, db_session):
        """Verify that line item exclusions are subtracted BEFORE applying network discount and co-pay."""
        # 1. Seed member
        member = Member(
            member_id="EMP100",
            name="Test User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            relationship="SELF",
            join_date=date(2024, 4, 1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(member)
        await db_session.flush()

        # 2. Create Dental claim at network hospital (Apollo)
        claims_service = ClaimsService(db_session)
        claim = await claims_service.create_claim(
            member_id="EMP100",
            policy_id="PLUM_GHI_2024",
            claim_category="DENTAL",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("4000"),
            hospital_name="Apollo Hospitals",
        )

        # Mock documents: hospital bill has two line items (one covered, one cosmetic/excluded)
        docs = [
            {
                "file_id": "F_EXCL_1",
                "file_name": "dental_bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Test User",
                "content": {
                    "hospital_name": "Apollo Hospitals",
                    "patient_name": "Test User",
                    "line_items": [
                        {"description": "Root Canal Treatment", "amount": 3000},
                        {"description": "Teeth Whitening", "amount": 1000},
                    ],
                    "total": 4000,
                },
            }
        ]

        # Mock policy service to simulate 20% discount and 10% copay on Dental
        policy_svc = PolicyService.get_instance()
        with (
            mock.patch.object(
                policy_svc, "get_network_discount_percent", return_value=Decimal("20")
            ),
            mock.patch.object(policy_svc, "get_copay_percent", return_value=Decimal("10")),
        ):
            # 3. Process claim
            orchestrator = ClaimOrchestrator(db_session)
            result = await orchestrator.process_claim(
                claim=claim,
                uploaded_documents=docs,
            )

        assert result["status"] == "DECIDED"
        decision = result["decision"]

        # Math verification:
        # Initial: 4000
        # Excluded item: 1000 (whitening) -> remaining covered amount = 3000
        # Network discount (20% of 3000) = 600 -> remaining = 2400
        # Copay (10% of 2400) = 240 -> final approved = 2160
        assert decision["decision"] == "PARTIAL"
        assert Decimal(str(decision["approved_amount"])) == Decimal("2160")

        # Check line item classifications
        line_items = decision["line_items"]
        assert len(line_items) == 2
        whitening_item = [li for li in line_items if "whitening" in li["description"].lower()][0]
        assert whitening_item["is_covered"] is False

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_pharmacy_branded_drug_copay(self, db_session):
        """Verify that a pharmacy claim containing branded drugs triggers 30% co-pay instead of 0%."""
        member = Member(
            member_id="EMP101",
            name="Test User 2",
            date_of_birth=date(1991, 2, 2),
            gender="F",
            relationship="SELF",
            join_date=date(2024, 4, 1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(member)
        await db_session.flush()

        claims_service = ClaimsService(db_session)
        claim = await claims_service.create_claim(
            member_id="EMP101",
            policy_id="PLUM_GHI_2024",
            claim_category="PHARMACY",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("1000"),
        )

        # Mock documents: prescription contains a brand-name drug (e.g. Crocin Active) instead of generic (Paracetamol)
        docs = [
            {
                "file_id": "F_BRAND_1",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Test User 2",
                "content": {
                    "doctor_name": "Dr. ABC",
                    "patient_name": "Test User 2",
                    "diagnosis": "Fever",
                    "medicines": [
                        "Crocin Active 650mg"
                    ],  # Crocin is branded (not in generic keywords list)
                },
            },
            {
                "file_id": "F_BRAND_2",
                "file_name": "bill.jpg",
                "actual_type": "PHARMACY_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Test User 2",
                "content": {
                    "patient_name": "Test User 2",
                    "total": 1000,
                    "medicines": [{"name": "Crocin Active 650mg", "amount": 1000}],
                },
            },
        ]

        orchestrator = ClaimOrchestrator(db_session)
        result = await orchestrator.process_claim(
            claim=claim,
            uploaded_documents=docs,
        )

        assert result["status"] == "DECIDED"
        decision = result["decision"]

        # Pharmacy normal copay is 0%, but branded drug copay is 30%
        # Final approved: 1000 - 30% = 700
        assert decision["decision"] == "APPROVED"
        assert Decimal(str(decision["approved_amount"])) == Decimal("700")

        # Check that branded drug copay rule check was registered in the trace
        trace = result["processing_trace"]
        policy_step = [s for s in trace["steps"] if s["step_name"] == "Policy Evaluation"][0]
        branded_check = [
            c for c in policy_step["checks_performed"] if c["rule"] == "BRANDED_DRUG_COPAY"
        ]
        assert len(branded_check) > 0
        assert branded_check[0]["passed"] is True

        await db_session.rollback()

    @pytest.mark.asyncio
    async def test_alternative_medicine_sessions_limit(self, db_session):
        """Verify that Alternative Medicine claims are rejected/flagged when the YTD sessions limit is exceeded."""
        member = Member(
            member_id="EMP102",
            name="Test User 3",
            date_of_birth=date(1992, 3, 3),
            gender="F",
            relationship="SELF",
            join_date=date(2024, 4, 1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(member)
        await db_session.flush()

        # Seed Member YTD claims summary with 18 sessions used
        from backend.domain.member.service import MemberService

        member_service = MemberService(db_session)
        summary = await member_service.get_or_create_summary("EMP102", 2026)
        summary.sessions_used_this_year = 18
        await db_session.flush()

        claims_service = ClaimsService(db_session)
        claim = await claims_service.create_claim(
            member_id="EMP102",
            policy_id="PLUM_GHI_2024",
            claim_category="ALTERNATIVE_MEDICINE",
            treatment_date=date(2026, 6, 4),
            claimed_amount=Decimal("3000"),
        )

        # Mock documents: claiming 5 sessions (18 + 5 = 23 sessions, exceeds max limit of 20)
        docs = [
            {
                "file_id": "F_ALT_1",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Test User 3",
                "content": {
                    "doctor_name": "Vaidya Krishnan",
                    "doctor_registration": "AYUR/KL/123",
                    "patient_name": "Test User 3",
                    "diagnosis": "Joint Pain",
                    "treatment": "Ayurveda therapy (5 sessions)",
                },
            },
            {
                "file_id": "F_ALT_2",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Test User 3",
                "content": {
                    "hospital_name": "Ayur Clinic",
                    "patient_name": "Test User 3",
                    "line_items": [
                        {"description": "Panchakarma Therapy (5 sessions)", "amount": 3000}
                    ],
                    "total": 3000,
                },
            },
        ]

        orchestrator = ClaimOrchestrator(db_session)
        result = await orchestrator.process_claim(
            claim=claim,
            uploaded_documents=docs,
        )

        assert result["status"] == "DECIDED"
        decision = result["decision"]

        # Should be REJECTED due to sessions limit
        assert decision["decision"] == "REJECTED"
        assert "SESSIONS_LIMIT_EXCEEDED" in decision["rejection_reasons"]

        # Check checks description in the trace
        trace = result["processing_trace"]
        policy_step = [s for s in trace["steps"] if s["step_name"] == "Policy Evaluation"][0]
        session_check = [
            c
            for c in policy_step["checks_performed"]
            if c["rule"] == "ALTERNATIVE_MEDICINE_SESSIONS_LIMIT"
        ][0]
        assert session_check["passed"] is False

        await db_session.rollback()
