"""Policy domain service — loads and evaluates policy rules."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from backend.core.container import get_container
from backend.core.logging import get_logger

logger = get_logger(__name__)


class PolicyService:
    """Evaluates claims against policy terms loaded from policy_terms.json."""

    _instance: PolicyService | None = None

    def __init__(self) -> None:
        self._policy: dict | None = None

    @classmethod
    def get_instance(cls) -> PolicyService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def policy(self) -> dict:
        """Lazy-load policy data from the policy file."""
        if self._policy is None:
            self._policy = get_container().policy_data
        return self._policy

    def reload(self) -> None:
        """Force reload policy data."""
        self._policy = None
        get_container()._policy_data = None

    # ── Document Requirements ──────────────────────────────────

    def get_document_requirements(self, claim_category: str) -> dict[str, Any]:
        """Get required and optional document types for a claim category."""
        doc_reqs = self.policy.get("document_requirements", {}).get(claim_category, {})
        return {
            "required": doc_reqs.get("required", []),
            "optional": doc_reqs.get("optional", []),
        }

    # ── Coverage Checks ────────────────────────────────────────

    def get_category_config(self, claim_category: str) -> dict[str, Any]:
        """Get the OPD category configuration."""
        category_key = claim_category.lower()
        return self.policy.get("opd_categories", {}).get(category_key, {})

    def is_category_covered(self, claim_category: str) -> bool:
        """Check if a claim category is covered."""
        config = self.get_category_config(claim_category)
        return config.get("covered", False)

    def get_sub_limit(self, claim_category: str) -> Decimal:
        """Get the sub-limit for a claim category."""
        config = self.get_category_config(claim_category)
        return Decimal(str(config.get("sub_limit", 0)))

    def get_copay_percent(self, claim_category: str) -> Decimal:
        """Get the co-pay percentage for a claim category."""
        config = self.get_category_config(claim_category)
        return Decimal(str(config.get("copay_percent", 0)))

    def get_network_discount_percent(self, claim_category: str) -> Decimal:
        """Get the network discount percentage for a claim category."""
        config = self.get_category_config(claim_category)
        return Decimal(str(config.get("network_discount_percent", 0)))

    def is_network_hospital(self, hospital_name: str | None) -> bool:
        """Check if a hospital is in the network."""
        if not hospital_name:
            return False
        network = self.policy.get("network_hospitals", [])
        return hospital_name in network

    # ── Per-Claim and Annual Limits ────────────────────────────

    def get_per_claim_limit(self) -> Decimal:
        """Get the per-claim limit."""
        return Decimal(str(self.policy.get("coverage", {}).get("per_claim_limit", 5000)))

    def get_annual_opd_limit(self) -> Decimal:
        """Get the annual OPD limit."""
        return Decimal(str(self.policy.get("coverage", {}).get("annual_opd_limit", 50000)))

    def get_sum_insured(self) -> Decimal:
        """Get the sum insured per employee."""
        return Decimal(str(self.policy.get("coverage", {}).get("sum_insured_per_employee", 500000)))

    def get_family_floater_limit(self) -> Decimal:
        """Get the family floater combined limit."""
        return Decimal(
            str(
                self.policy.get("coverage", {})
                .get("family_floater", {})
                .get("combined_limit", 150000)
            )
        )

    def get_submission_deadline_days(self) -> int:
        """Get the deadline in days from treatment date."""
        return int(self.policy.get("submission_rules", {}).get("deadline_days_from_treatment", 30))

    def get_minimum_claim_amount(self) -> Decimal:
        """Get the minimum claim amount."""
        return Decimal(
            str(self.policy.get("submission_rules", {}).get("minimum_claim_amount", 500))
        )

    # ── Waiting Periods ────────────────────────────────────────

    def get_initial_waiting_days(self) -> int:
        """Get the initial waiting period in days."""
        return int(self.policy.get("waiting_periods", {}).get("initial_waiting_period_days", 30))

    def get_pre_existing_waiting_days(self) -> int:
        """Get the pre-existing conditions waiting period in days."""
        return int(self.policy.get("waiting_periods", {}).get("pre_existing_conditions_days", 365))

    def get_condition_waiting_days(self, condition: str) -> int | None:
        """Get waiting period for a specific condition, or None if not applicable."""
        specific = self.policy.get("waiting_periods", {}).get("specific_conditions", {})
        condition_lower = condition.lower()
        for key, days in specific.items():
            if key in condition_lower or condition_lower in key:
                return days
        return None

    def is_within_waiting_period(
        self, join_date: date, treatment_date: date, diagnosis: str | None = None
    ) -> tuple[bool, str | None, date | None]:
        """
        Check if a claim is within a waiting period.
        Returns (is_within_period, period_name, eligible_from_date).

        Checks in order:
        1. Initial waiting period (30 days) — applies to ALL claims
        2. Condition-specific waiting periods (e.g., diabetes 90d)
        3. Pre-existing conditions waiting period (365 days) — for chronic conditions NOT in specific list
        """
        days_since_join = (treatment_date - join_date).days

        # Initial waiting period — applies to ALL claims
        initial_days = self.get_initial_waiting_days()
        if days_since_join < initial_days:
            eligible = join_date + timedelta(days=initial_days)
            return True, "INITIAL_WAITING_PERIOD", eligible

        # Condition-specific waiting periods (takes precedence over pre-existing)
        if diagnosis:
            condition_days = self.get_condition_waiting_days(diagnosis)
            if condition_days:
                if days_since_join < condition_days:
                    eligible = join_date + timedelta(days=condition_days)
                    return True, "CONDITION_WAITING_PERIOD", eligible
                else:
                    # Condition-specific waiting period has passed
                    return False, None, None

        # Pre-existing conditions waiting period (365 days)
        # Only applies to chronic conditions NOT in the specific conditions list
        if diagnosis and self._is_pre_existing_condition(diagnosis):
            pre_existing_days = self.get_pre_existing_waiting_days()
            if days_since_join < pre_existing_days:
                eligible = join_date + timedelta(days=pre_existing_days)
                return True, "PRE_EXISTING_CONDITION", eligible

        return False, None, None

    def _is_pre_existing_condition(self, diagnosis: str) -> bool:
        """Check if a diagnosis is considered a pre-existing/chronic condition."""
        chronic_keywords = [
            "diabetes", "hypertension", "thyroid", "asthma", "copd",
            "arthritis", "osteoporosis", "chronic", "cardiac", "heart",
            "renal", "kidney", "liver", "cirrhosis", "epilepsy",
            "parkinson", "autoimmune", "lupus", "rheumatoid",
        ]
        diagnosis_lower = diagnosis.lower()
        return any(kw in diagnosis_lower for kw in chronic_keywords)

    # ── Exclusions ─────────────────────────────────────────────

    def get_excluded_conditions(self) -> list[str]:
        """Get list of excluded conditions."""
        return self.policy.get("exclusions", {}).get("conditions", [])

    def get_dental_exclusions(self) -> list[str]:
        """Get list of dental exclusions."""
        return self.policy.get("exclusions", {}).get("dental_exclusions", [])

    def get_vision_exclusions(self) -> list[str]:
        """Get list of vision exclusions."""
        return self.policy.get("exclusions", {}).get("vision_exclusions", [])

    def is_excluded_condition(self, diagnosis: str | None) -> bool:
        """Check if a diagnosis matches excluded conditions."""
        if not diagnosis:
            return False
        excluded = self.get_excluded_conditions()
        diagnosis_lower = diagnosis.lower()
        for cond in excluded:
            if cond.lower() in diagnosis_lower or any(
                word in diagnosis_lower for word in cond.lower().split()
            ):
                return True
        return False

    def is_excluded_procedure(self, claim_category: str, description: str) -> bool:
        """Check if a procedure is excluded for a category.

        Also checks against a universal deny-list of obviously non-medical items.
        """
        desc_lower = description.lower()

        # ── Universal deny-list: obviously non-medical items ─────
        non_medical_keywords = [
            "samosa", "chutni", "cricket", "sports jersey", "jersy",
            "turf booking", "movie ticket", "pizza", "burger", "ice cream",
            "groceries", "shopping", "toys", "video game", "playstation",
            "netflix", "amazon prime", "cricket bat", "football", "bat ",
            "shoe", "sandals", "perfume", "cosmetic", "haircut", "salon",
            "pet food", "dog food", "cat food", "alcohol", "cigarette",
            "lottery", "betting", "gambling",
        ]
        for kw in non_medical_keywords:
            if kw in desc_lower:
                return True

        cat_config = self.get_category_config(claim_category)

        # Check excluded procedures list from policy config
        excluded_procedures = cat_config.get("excluded_procedures", [])
        for proc in excluded_procedures:
            if proc.lower() in desc_lower:
                return True

        # Check category-specific exclusions from top-level
        if claim_category == "DENTAL":
            for exc in self.get_dental_exclusions():
                if exc.lower() in desc_lower:
                    return True
        elif claim_category == "VISION":
            for exc in self.get_vision_exclusions():
                if exc.lower() in desc_lower:
                    return True

        return False

    # ── Pre-Authorization ──────────────────────────────────────

    def needs_pre_authorization(
        self, claim_category: str, line_items: list[dict[str, Any]]
    ) -> tuple[bool, str | None]:
        """
        Check if any line item requires pre-authorization.
        Returns (needs_auth, description_of_at_risk_item).
        """
        pre_auth_req = self.policy.get("pre_authorization", {}).get("required_for", [])
        high_value_tests = (
            self.policy.get("opd_categories", {})
            .get("diagnostic", {})
            .get("high_value_tests_requiring_pre_auth", [])
        )
        pre_auth_threshold = Decimal(
            str(
                self.policy.get("opd_categories", {})
                .get("diagnostic", {})
                .get("pre_auth_threshold", 10000)
            )
        )

        for item in line_items:
            desc = item.get("description", "")
            amount = Decimal(str(item.get("amount", 0)))

            for test_name in high_value_tests:
                if test_name.lower() in desc.lower() and amount > pre_auth_threshold:
                    return True, desc

            # Check generic pre-auth requirements
            for req in pre_auth_req:
                req_lower = req.lower()
                desc_lower = desc.lower()
                # Match patterns like "MRI scan (amount > ₹10,000)"
                if ("mri" in req_lower and "mri" in desc_lower) or (
                    "ct scan" in req_lower and "ct" in desc_lower
                ):
                    if amount > pre_auth_threshold:
                        return True, desc
                elif "pet scan" in req_lower and "pet" in desc_lower:
                    return True, desc
                elif "major surgical" in req_lower:
                    if "surgery" in desc_lower or "surgical" in desc_lower:
                        return True, desc

        return False, None

    # ── Category-Specific Rules ────────────────────────────────

    def get_covered_procedures(self, claim_category: str) -> list[str]:
        """Get covered procedures for a category."""
        config = self.get_category_config(claim_category)
        return config.get("covered_procedures", [])

    def get_covered_systems(self, claim_category: str) -> list[str]:
        """Get covered alternative medicine systems."""
        config = self.get_category_config(claim_category)
        return config.get("covered_systems", [])

    def get_max_sessions(self, claim_category: str) -> int:
        """Get max sessions per year for a category."""
        config = self.get_category_config(claim_category)
        return config.get("max_sessions_per_year", 0)

    def requires_registered_practitioner(self, claim_category: str) -> bool:
        """Check if category requires a registered practitioner."""
        config = self.get_category_config(claim_category)
        return config.get("requires_registered_practitioner", False)

    def get_branded_drug_copay_percent(self) -> Decimal:
        """Get co-pay for branded drugs."""
        config = self.get_category_config("PHARMACY")
        return Decimal(str(config.get("branded_drug_copay_percent", 30)))

    def is_generic_mandatory(self) -> bool:
        """Check if generic drugs are mandatory."""
        config = self.get_category_config("PHARMACY")
        return config.get("generic_mandatory", False)
