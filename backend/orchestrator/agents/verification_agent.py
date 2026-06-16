"""Document Verification Agent — validates uploaded documents against requirements."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logging import get_logger
from backend.domain.documents.service import DocumentService
from backend.domain.policy.service import PolicyService
from backend.orchestrator.agents.base import BaseAgent

logger = get_logger(__name__)


class VerificationAgent(BaseAgent):
    """Agent that verifies uploaded documents meet policy requirements."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__("verification_agent")
        self.session = session
        self.doc_service = DocumentService(session)
        self.policy_service = PolicyService.get_instance()

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Verify documents against policy requirements.

        Context must include:
        - claim_category: str
        - documents: list of uploaded document metadata
        """
        claim_category = context.get("claim_category", "")
        documents = context.get("documents", [])

        # Get policy document requirements
        doc_reqs = self.policy_service.get_document_requirements(claim_category)

        # Run verification
        result = await self.doc_service.verify_documents(
            claim_id=context.get("claim_id", 0),
            claim_category=claim_category,
            policy_doc_reqs=doc_reqs,
            uploaded_docs=documents,
        )

        # Build checks performed list for traceability
        checks = []
        for err in result.get("errors", []):
            error_type = err.get("error_type", "UNKNOWN")
            document_type = err.get("document_type") or err.get("details", {}).get("required_type", "unknown")
            file_name = err.get("file_name", "")

            if error_type == "MISSING_REQUIRED":
                detail_msg = (
                    f"DOCUMENT_VERIFICATION check FAILED: Required document '{document_type}' "
                    f"is missing for claim category '{claim_category}'. "
                    f"For {claim_category} claims, the following document types are required: "
                    f"{', '.join(doc_reqs.get('required', []))}. "
                    f"Action needed: Upload the missing {document_type} and resubmit."
                )
            elif error_type == "WRONG_TYPE":
                detail_msg = (
                    f"DOCUMENT_VERIFICATION check FAILED: Uploaded file '{file_name}' has type "
                    f"'{err.get('details', {}).get('uploaded_type', 'unknown')}' which is not accepted "
                    f"for '{claim_category}' claims. Required types: "
                    f"{', '.join(doc_reqs.get('required', []))}. "
                    f"Action needed: Remove the incorrect document and upload the correct type."
                )
            elif error_type == "UNREADABLE":
                detail_msg = (
                    f"DOCUMENT_VERIFICATION check FAILED: Document '{file_name}' is unreadable. "
                    f"The document quality is too poor for processing. "
                    f"Action needed: Upload a clearer, legible version of this document."
                )
            elif error_type == "PATIENT_MISMATCH":
                names = err.get("details", {}).get("patient_names", [])
                detail_msg = (
                    f"DOCUMENT_VERIFICATION check FAILED: Patient name mismatch detected. "
                    f"The uploaded documents contain different patient names: "
                    f"{', '.join(names)}. All documents must belong to the same patient. "
                    f"Action needed: Verify that all uploaded documents belong to you and resubmit."
                )
            else:
                detail_msg = err.get("message", f"Unknown error: {error_type}")

            checks.append(
                {
                    "check": error_type,
                    "passed": False,
                    "reason": detail_msg,
                }
            )
        if result["is_valid"]:
            checks.append(
                {
                    "check": "ALL_CHECKS_PASSED",
                    "passed": True,
                    "reason": (
                        f"DOCUMENT_VERIFICATION all checks PASSED: All {len(documents)} uploaded document(s) "
                        f"for '{claim_category}' claim are valid, readable, and match policy requirements."
                    ),
                }
            )

        logger.info(
            "verification_agent_done",
            claim_id=context.get("claim_id"),
            is_valid=result["is_valid"],
            error_count=len(result.get("errors", [])),
        )

        return {
            "agent": self.name,
            "is_valid": result["is_valid"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "documents": result["documents"],
            "checks": checks,
            "confidence": 1.0 if result["is_valid"] else 0.0,
        }
