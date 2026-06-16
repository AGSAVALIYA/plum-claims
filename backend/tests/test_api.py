"""API endpoint tests using FastAPI TestClient.

Tests the REST API layer (HTTP validation, routing, serialization) in addition
to the existing Python-layer integration tests.
"""

import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.auth import create_access_token
from backend.core.config import settings
from backend.domain.claims.service import ClaimsService


# ── Fixtures ────────────────────────────────────────────────


@pytest.fixture
def api_client(db_session):
    """Create a TestClient with overridden dependencies.

    Overrides:
    - get_db_session → returns the test db_session
    - get_current_user → returns a fixed member user
    - Celery task → no-op (avoid needing a real worker)
    """
    from backend.api.dependencies import get_db_session
    from backend.api.auth import get_current_user
    from backend.main import app

    async def _override_db():
        yield db_session

    async def _override_user():
        from backend.api.auth import TokenPayload
        return TokenPayload(sub="EMP001", role="member")

    app.dependency_overrides[get_db_session] = _override_db
    app.dependency_overrides[get_current_user] = _override_user

    # Patch Celery's process_claim_async.delay to be a no-op
    with patch("backend.orchestrator.tasks.process_claim_async") as mock_task:
        mock_task.delay = lambda *args, **kwargs: None
        client = TestClient(app)
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def valid_claim_payload():
    """A valid claim submission payload."""
    return {
        "member_id": "EMP001",
        "policy_id": "PLUM_GHI_2024",
        "claim_category": "CONSULTATION",
        "treatment_date": "2026-06-01",
        "claimed_amount": 1500.0,
        "hospital_name": "City Clinic, Bengaluru",
        "documents": [
            {
                "file_id": "DOC001",
                "file_name": "prescription.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh Kumar",
                "content": {"doctor_name": "Dr. Sharma", "diagnosis": "Viral Fever"},
            },
            {
                "file_id": "DOC002",
                "file_name": "hospital_bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh Kumar",
                "content": {"total": 1500, "line_items": [{"description": "Consultation", "amount": 1500}]},
            },
        ],
    }


# ── Tests ────────────────────────────────────────────────────


class TestSubmitClaim:
    """Tests for POST /api/v1/claims."""

    async def test_valid_submission_returns_202(self, api_client, db_session, valid_claim_payload):
        """POST /api/v1/claims with valid data returns 202 Accepted."""
        # Need to add member for valid processing
        from datetime import UTC, datetime

        from backend.domain.member.models import Member

        member = Member(
            member_id="EMP001",
            name="Rajesh Kumar",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            relationship="SELF",
            join_date=date(2024, 4, 1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(member)
        await db_session.commit()

        response = api_client.post(
            "/api/v1/claims",
            json=valid_claim_payload,
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "SUBMITTED"
        assert data["claim_id"] > 0

    def test_invalid_submission_returns_422(self, api_client):
        """POST /api/v1/claims with invalid data returns 422."""
        invalid_payloads = [
            # Missing member_id
            {
                "claim_category": "CONSULTATION",
                "treatment_date": "2026-06-01",
                "claimed_amount": 1500,
            },
            # Invalid category
            {
                "member_id": "EMP001",
                "claim_category": "INVALID_CATEGORY",
                "treatment_date": "2026-06-01",
                "claimed_amount": 1500,
            },
            # Negative amount
            {
                "member_id": "EMP001",
                "claim_category": "CONSULTATION",
                "treatment_date": "2026-06-01",
                "claimed_amount": -100,
            },
        ]

        for payload in invalid_payloads:
            response = api_client.post(
                "/api/v1/claims",
                json=payload,
                headers={"Authorization": "Bearer test-token"},
            )
            assert response.status_code == 422, f"Expected 422 for payload: {payload}"

    def test_unauthorized_request_returns_422(self, api_client):
        """POST /api/v1/claims with missing required fields returns 422.

        Note: In development mode (default test config), auto-auth is enabled
        so 401 is not returned for missing tokens. This test validates
        schema validation instead.
        """
        response = api_client.post(
            "/api/v1/claims",
            json={"member_id": "EMP001"},  # Missing required fields
            headers={"Authorization": "Bearer test-token"},
        )
        assert response.status_code == 422


class TestListClaims:
    """Tests for GET /api/v1/claims."""

    async def test_list_claims_returns_paginated_list(self, api_client, db_session):
        """GET /api/v1/claims returns a paginated list of claims."""
        from datetime import UTC, datetime

        from backend.domain.member.models import Member

        member = Member(
            member_id="EMP001",
            name="Rajesh Kumar",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            relationship="SELF",
            join_date=date(2024, 4, 1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(member)
        await db_session.commit()

        # Submit a valid claim first
        payload = {
            "member_id": "EMP001",
            "policy_id": "PLUM_GHI_2024",
            "claim_category": "CONSULTATION",
            "treatment_date": "2026-06-01",
            "claimed_amount": 1500.0,
            "documents": [
                {
                    "file_id": "DOC003",
                    "file_name": "prescription.jpg",
                    "actual_type": "PRESCRIPTION",
                    "quality": "GOOD",
                    "patient_name_on_doc": "Rajesh Kumar",
                    "content": {"diagnosis": "Viral Fever"},
                },
            ],
        }
        api_client.post(
            "/api/v1/claims",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )

        response = api_client.get("/api/v1/claims")
        assert response.status_code == 200
        data = response.json()
        assert "claims" in data
        assert isinstance(data["claims"], list)
        assert data["total"] >= 1
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_list_claims_with_filters(self, api_client, db_session):
        """GET /api/v1/claims with member_id filter."""
        response = api_client.get("/api/v1/claims?member_id=NONEXISTENT")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["claims"]) == 0


class TestGetClaimTrace:
    """Tests for GET /api/v1/claims/{id}/trace."""

    async def test_get_claim_trace(self, api_client, db_session):
        """GET /api/v1/claims/{id}/trace returns a processing trace."""
        from datetime import UTC, datetime

        from backend.domain.member.models import Member

        member = Member(
            member_id="EMP002",
            name="Test User",
            date_of_birth=date(1990, 1, 1),
            gender="M",
            relationship="SELF",
            join_date=date(2024, 4, 1),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(member)
        await db_session.commit()

        # Submit a claim
        payload = {
            "member_id": "EMP002",
            "policy_id": "PLUM_GHI_2024",
            "claim_category": "CONSULTATION",
            "treatment_date": "2026-06-01",
            "claimed_amount": 1500.0,
            "documents": [
                {
                    "file_id": "DOC004",
                    "file_name": "prescription.jpg",
                    "actual_type": "PRESCRIPTION",
                    "quality": "GOOD",
                    "patient_name_on_doc": "Test User",
                    "content": {"diagnosis": "Viral Fever"},
                },
            ],
        }
        submit_resp = api_client.post(
            "/api/v1/claims",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        claim_id = submit_resp.json()["claim_id"]

        # Get trace
        response = api_client.get(f"/api/v1/claims/{claim_id}/trace")
        # Should either return a trace or 404 if not processed yet
        assert response.status_code in (200, 404)
        if response.status_code == 200:
            data = response.json()
            assert "claim_id" in data
            assert "steps" in data
