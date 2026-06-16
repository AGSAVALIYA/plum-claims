"""Document Extraction Agent — extracts structured data from verified documents."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.container import get_container
from backend.core.logging import get_logger
from backend.domain.documents.service import DocumentService
from backend.orchestrator.agents.base import BaseAgent

logger = get_logger(__name__)


class ExtractionAgent(BaseAgent):
    """Agent that extracts structured data from verified documents."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__("extraction_agent")
        self.session = session
        self.doc_service = DocumentService(session)

    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Extract structured data from verified documents.

        Context must include:
        - documents: list of verified document metadata with content
        - simulate_component_failure: bool (optional)
        """
        documents = context.get("documents", [])
        simulate_failure = context.get("simulate_component_failure", False)

        if simulate_failure:
            logger.warning("extraction_agent_simulated_failure")
            raise RuntimeError("Simulated extraction failure")

        llm = None
        try:
            llm = get_container().llm
        except Exception:
            logger.warning("llm_provider_unavailable", agent=self.name)

        # Filter to only verified documents with content
        docs_with_content = [
            d for d in documents if d.get("content") is not None or d.get("actual_type")
        ]

        result = await self.doc_service.extract_document_data(
            claim_id=context.get("claim_id", 0),
            documents=docs_with_content,
            llm_provider=llm,
            simulate_failure=simulate_failure,
        )

        # Build checks
        checks = []
        for doc in result.get("documents", []):
            checks.append(
                {
                    "check": f"EXTRACT_DOC_{doc.get('document_index', '?')}",
                    "passed": doc.get("confidence", 0) > 0,
                    "reason": f"Extracted {doc.get('document_type', 'unknown')} with confidence {doc.get('confidence', 0)}",
                }
            )

        logger.info(
            "extraction_agent_done",
            claim_id=context.get("claim_id"),
            doc_count=len(result.get("documents", [])),
            overall_confidence=result.get("overall_confidence", 0),
        )

        return {
            "agent": self.name,
            "documents": result["documents"],
            "overall_confidence": result["overall_confidence"],
            "unextracted_fields": result.get("unextracted_fields", []),
            "checks": checks,
            "confidence": result["overall_confidence"],
            "llm_usage": result.get("llm_usage", {}),
            "llm_cost": result.get("llm_cost", 0.0),
        }
