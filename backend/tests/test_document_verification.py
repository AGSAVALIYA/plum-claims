"""Unit tests for document verification service."""

import pytest

from backend.domain.documents.service import DocumentService


class TestDocumentVerification:
    """Tests for the DocumentService.verify_documents method."""

    @pytest.mark.asyncio
    async def test_valid_documents_pass(self, db_session):
        """Valid consultation documents should pass verification."""
        service = DocumentService(db_session)
        policy_reqs = {
            "required": ["PRESCRIPTION", "HOSPITAL_BILL"],
            "optional": [],
        }
        docs = [
            {
                "file_id": "F1",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "John Doe",
            },
            {
                "file_id": "F2",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "John Doe",
            },
        ]

        result = await service.verify_documents(
            claim_id=1,
            claim_category="CONSULTATION",
            policy_doc_reqs=policy_reqs,
            uploaded_docs=docs,
        )

        assert result["is_valid"] is True
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_wrong_document_type_detected(self, db_session):
        """Two prescriptions instead of prescription + hospital bill."""
        service = DocumentService(db_session)
        policy_reqs = {
            "required": ["PRESCRIPTION", "HOSPITAL_BILL"],
            "optional": [],
        }
        docs = [
            {
                "file_id": "F1",
                "file_name": "rx1.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh",
            },
            {
                "file_id": "F2",
                "file_name": "rx2.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh",
            },
        ]

        result = await service.verify_documents(
            claim_id=1,
            claim_category="CONSULTATION",
            policy_doc_reqs=policy_reqs,
            uploaded_docs=docs,
        )

        assert result["is_valid"] is False
        assert len(result["errors"]) >= 1
        # Error must mention the missing type
        error_msg = result["errors"][0]["message"]
        assert "HOSPITAL_BILL" in error_msg or "PRESCRIPTION" in error_msg

    @pytest.mark.asyncio
    async def test_unreadable_document_detected(self, db_session):
        """Unreadable document should be flagged."""
        service = DocumentService(db_session)
        policy_reqs = {
            "required": ["PRESCRIPTION", "PHARMACY_BILL"],
            "optional": [],
        }
        docs = [
            {
                "file_id": "F1",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Priya",
            },
            {
                "file_id": "F2",
                "file_name": "blurry.jpg",
                "actual_type": "PHARMACY_BILL",
                "quality": "UNREADABLE",
                "patient_name_on_doc": "Priya",
            },
        ]

        result = await service.verify_documents(
            claim_id=1,
            claim_category="PHARMACY",
            policy_doc_reqs=policy_reqs,
            uploaded_docs=docs,
        )

        assert result["is_valid"] is False
        unreadable_errors = [e for e in result["errors"] if e["error_type"] == "UNREADABLE"]
        assert len(unreadable_errors) >= 1
        assert "blurry" in unreadable_errors[0]["message"].lower()

    @pytest.mark.asyncio
    async def test_patient_name_mismatch_detected(self, db_session):
        """Documents with different patient names should be flagged."""
        service = DocumentService(db_session)
        policy_reqs = {
            "required": ["PRESCRIPTION", "HOSPITAL_BILL"],
            "optional": [],
        }
        docs = [
            {
                "file_id": "F1",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh Kumar",
            },
            {
                "file_id": "F2",
                "file_name": "bill.jpg",
                "actual_type": "HOSPITAL_BILL",
                "quality": "GOOD",
                "patient_name_on_doc": "Arjun Mehta",
            },
        ]

        result = await service.verify_documents(
            claim_id=1,
            claim_category="CONSULTATION",
            policy_doc_reqs=policy_reqs,
            uploaded_docs=docs,
        )

        assert result["is_valid"] is False
        mismatch_errors = [e for e in result["errors"] if e["error_type"] == "PATIENT_MISMATCH"]
        assert len(mismatch_errors) >= 1
        assert "Rajesh Kumar" in mismatch_errors[0]["message"]
        assert "Arjun Mehta" in mismatch_errors[0]["message"]

    @pytest.mark.asyncio
    async def test_missing_required_document(self, db_session):
        """Missing required document type should be detected."""
        service = DocumentService(db_session)
        policy_reqs = {
            "required": ["PRESCRIPTION", "HOSPITAL_BILL", "LAB_REPORT"],
            "optional": [],
        }
        docs = [
            {
                "file_id": "F1",
                "file_name": "rx.jpg",
                "actual_type": "PRESCRIPTION",
                "quality": "GOOD",
                "patient_name_on_doc": "Rajesh",
            },
        ]

        result = await service.verify_documents(
            claim_id=1,
            claim_category="DIAGNOSTIC",
            policy_doc_reqs=policy_reqs,
            uploaded_docs=docs,
        )

        assert result["is_valid"] is False
        missing_errors = [e for e in result["errors"] if e["error_type"] == "MISSING_REQUIRED"]
        assert len(missing_errors) >= 1
