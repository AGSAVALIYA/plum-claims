"""Unit tests for Policy Service."""

from datetime import date
from decimal import Decimal

import pytest

from backend.domain.policy.service import PolicyService


class TestPolicyService:
    """Tests for policy rule evaluation."""

    @pytest.fixture
    def svc(self):
        return PolicyService.get_instance()

    # ── Coverage Checks ─────────────────────────────────

    def test_consultation_is_covered(self, svc):
        assert svc.is_category_covered("CONSULTATION") is True

    def test_consultation_sub_limit(self, svc):
        assert svc.get_sub_limit("CONSULTATION") == Decimal("2000")

    def test_consultation_copay(self, svc):
        assert svc.get_copay_percent("CONSULTATION") == Decimal("10")

    def test_network_discount(self, svc):
        assert svc.get_network_discount_percent("CONSULTATION") == Decimal("20")

    def test_apollo_is_network_hospital(self, svc):
        assert svc.is_network_hospital("Apollo Hospitals") is True

    def test_unknown_hospital_not_network(self, svc):
        assert svc.is_network_hospital("Random Clinic") is False

    # ── Limits ──────────────────────────────────────────

    def test_per_claim_limit(self, svc):
        assert svc.get_per_claim_limit() == Decimal("5000")

    def test_annual_opd_limit(self, svc):
        assert svc.get_annual_opd_limit() == Decimal("50000")

    def test_family_floater_limit(self, svc):
        assert svc.get_family_floater_limit() == Decimal("150000")

    # ── Waiting Periods ─────────────────────────────────

    def test_within_initial_waiting_period(self, svc):
        join_date = date(2024, 4, 1)
        treatment_date = date(2024, 4, 15)  # 14 days after joining
        within, name, eligible = svc.is_within_waiting_period(join_date, treatment_date, None)
        assert within is True
        assert name == "INITIAL_WAITING_PERIOD"

    def test_after_initial_waiting_period(self, svc):
        join_date = date(2024, 4, 1)
        treatment_date = date(2024, 6, 1)  # well past 30 days
        within, name, eligible = svc.is_within_waiting_period(join_date, treatment_date, None)
        assert within is False

    def test_diabetes_waiting_period(self, svc):
        join_date = date(2024, 9, 1)
        treatment_date = date(2024, 10, 15)  # 44 days, within 90-day diabetes
        within, name, eligible = svc.is_within_waiting_period(
            join_date, treatment_date, "Type 2 Diabetes Mellitus"
        )
        assert within is True
        assert name == "CONDITION_WAITING_PERIOD"

    def test_diabetes_waiting_period_passed(self, svc):
        join_date = date(2024, 4, 1)
        treatment_date = date(2024, 11, 1)  # > 90 days
        within, name, eligible = svc.is_within_waiting_period(
            join_date, treatment_date, "Type 2 Diabetes Mellitus"
        )
        assert within is False

    # ── Exclusions ──────────────────────────────────────

    def test_obesity_is_excluded(self, svc):
        assert svc.is_excluded_condition("Morbid Obesity — BMI 37") is True

    def test_viral_fever_not_excluded(self, svc):
        assert svc.is_excluded_condition("Viral Fever") is False

    def test_bariatric_excluded(self, svc):
        assert svc.is_excluded_condition("Bariatric Consultation") is True

    # ── Pre-Authorization ───────────────────────────────

    def test_mri_needs_pre_auth(self, svc):
        items = [{"description": "MRI Lumbar Spine", "amount": 15000}]
        needs, item = svc.needs_pre_authorization("DIAGNOSTIC", items)
        assert needs is True
        assert "MRI" in item

    def test_mri_below_threshold_no_pre_auth(self, svc):
        items = [{"description": "MRI Lumbar Spine", "amount": 5000}]
        needs, item = svc.needs_pre_authorization("DIAGNOSTIC", items)
        assert needs is False

    # ── Dental Procedures ───────────────────────────────

    def test_root_canal_covered(self, svc):
        assert svc.is_excluded_procedure("DENTAL", "Root Canal Treatment") is False

    def test_teeth_whitening_excluded(self, svc):
        assert svc.is_excluded_procedure("DENTAL", "Teeth Whitening") is True

    # ── Document Requirements ───────────────────────────

    def test_consultation_doc_requirements(self, svc):
        reqs = svc.get_document_requirements("CONSULTATION")
        assert "PRESCRIPTION" in reqs["required"]
        assert "HOSPITAL_BILL" in reqs["required"]

    def test_pharmacy_doc_requirements(self, svc):
        reqs = svc.get_document_requirements("PHARMACY")
        assert "PRESCRIPTION" in reqs["required"]
        assert "PHARMACY_BILL" in reqs["required"]
