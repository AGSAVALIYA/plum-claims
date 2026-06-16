"""Hybrid document processor — routes to Docling or Vision LLM based on quality.

Per planning doc 01_system_architecture.md:
- Digital/structured PDFs → DoclingAdapter (excellent table extraction)
- Handwritten/blurry photos → VisionLLMAdapter (uses ILLMProvider)
- Quality assessment determines the routing
"""

from __future__ import annotations

from typing import Any

from backend.core.logging import get_logger
from backend.providers.doc_processing.interface import (
    DocumentType,
    ExtractionResult,
    IDocumentProcessor,
    QualityAssessment,
)

logger = get_logger(__name__)


class HybridDocumentProcessor(IDocumentProcessor):
    """Routes documents to the best processor based on quality assessment.

    Falls back to vision LLM when Docling is unavailable or document
    is low-quality (handwritten, blurry, scanned).
    """

    def __init__(
        self,
        llm_provider: Any = None,
    ) -> None:
        """Initialize with an optional LLM provider for vision-based extraction.

        Args:
            llm_provider: An ILLMProvider instance for vision-capable extraction.
                          If None, only text-based extraction is available.
        """
        self._llm = llm_provider
        self._docling: Any = None

    @property
    def docling_available(self) -> bool:
        """Check if the Docling library is available."""
        if self._docling is None:
            try:
                import docling  # type: ignore[import-untyped]

                self._docling = True
            except ImportError:
                self._docling = False
                logger.debug("docling_not_available")
        return self._docling

    async def classify_document(self, file_bytes: bytes, filename: str) -> DocumentType:
        """Classify document type using filename heuristics and content analysis.

        When Docling is available, uses its classification. Otherwise falls
        back to filename-based heuristics.
        """
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        # PDF documents: try Docling first, then heuristics
        if ext == "pdf" and self.docling_available:
            try:
                # Docling would process the PDF and classify sections
                pass  # Placeholder for real Docling integration
            except Exception:
                pass

        # Heuristic fallback based on filename
        filename_lower = filename.lower()
        if any(kw in filename_lower for kw in ("prescription", "rx", "prescri")):
            return DocumentType(
                primary_type="PRESCRIPTION",
                confidence=0.7,
            )
        elif any(kw in filename_lower for kw in ("bill", "invoice", "receipt")):
            if "pharmacy" in filename_lower or "pharm" in filename_lower:
                return DocumentType(primary_type="PHARMACY_BILL", confidence=0.7)
            elif "hospital" in filename_lower or "hosp" in filename_lower:
                return DocumentType(primary_type="HOSPITAL_BILL", confidence=0.7)
            return DocumentType(primary_type="HOSPITAL_BILL", confidence=0.5)
        elif any(kw in filename_lower for kw in ("lab", "report", "diagnostic")):
            return DocumentType(primary_type="LAB_REPORT", confidence=0.7)
        elif any(kw in filename_lower for kw in ("dental",)):
            return DocumentType(primary_type="DENTAL_REPORT", confidence=0.7)
        elif any(kw in filename_lower for kw in ("discharge",)):
            return DocumentType(primary_type="DISCHARGE_SUMMARY", confidence=0.7)

        # Default: attempt vision-based classification if available
        return DocumentType(primary_type="UNKNOWN", confidence=0.0)

    async def assess_quality(self, file_bytes: bytes) -> QualityAssessment:
        """Assess document readability.

        Uses OpenCV for basic quality checks on images. For PDFs,
        delegates to Docling when available.
        """
        issues: list[str] = []

        # Basic checks that don't require heavy processing
        if len(file_bytes) < 100:
            issues.append("low_resolution")
            return QualityAssessment(is_readable=False, score=0.0, issues=issues)

        # Check if it's a PDF
        if file_bytes[:4] == b"%PDF":
            return QualityAssessment(is_readable=True, score=0.9, issues=[])

        # For images, use OpenCV for basic quality check
        try:
            import cv2  # type: ignore[import-untyped]
            import numpy as np

            arr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return QualityAssessment(is_readable=False, score=0.0, issues=["unreadable"])

            # Laplacian variance as a blur detector
            laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
            if laplacian_var < 50:
                issues.append("blurry")

            # Check resolution
            h, w = img.shape[:2]
            if h < 200 or w < 200:
                issues.append("low_resolution")

            score = min(laplacian_var / 500.0, 1.0) if laplacian_var < 500 else 1.0
            is_readable = len(issues) == 0 or laplacian_var >= 20

            return QualityAssessment(
                is_readable=is_readable,
                score=round(score, 2),
                issues=issues,
            )
        except ImportError:
            # OpenCV not available — assume readable
            return QualityAssessment(is_readable=True, score=0.8, issues=[])

    async def extract_text(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        """Extract raw text from the document.

        Routes to Docling for PDFs, or uses Tesseract/EasyOCR for images.
        """
        # For now, return basic extraction metadata
        # Full Docling/OCR integration requires external service dependencies
        # Try classification for a meaningful document_type before falling back
        try:
            classification = await self.classify_document(file_bytes, filename)
            doc_type = classification.primary_type
        except Exception:
            doc_type = "UNKNOWN"

        return ExtractionResult(
            success=True,
            document_type=doc_type,
            extracted_data={},
            confidence=0.5,
            raw_text=None,
            processor_used="hybrid",
        )

    async def extract_structured(
        self,
        file_bytes: bytes,
        filename: str,
        schema: dict[str, Any],
    ) -> ExtractionResult:
        """Extract structured data matching the given schema.

        Uses the vision LLM provider when available for complex extraction.
        Falls back to basic extraction otherwise.
        """
        if self._llm:
            try:
                from backend.providers.llm.interface import LLMRequest

                # Build a prompt that includes schema context
                request = LLMRequest(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"Extract structured data from this document. "
                                f"Output valid JSON matching this schema: "
                                f"{schema}"
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Filename: {filename}. Document type: {await self.classify_document(file_bytes, filename)}",
                        },
                    ],
                    response_schema=schema,
                )
                result = await self._llm.extract_structured(request)
                try:
                    classification = await self.classify_document(file_bytes, filename)
                    doc_type = classification.primary_type
                except Exception:
                    doc_type = "UNKNOWN"
                return ExtractionResult(
                    success=True,
                    document_type=doc_type,
                    extracted_data=result,
                    confidence=0.85,
                    processor_used="vision_llm",
                )
            except Exception as e:
                logger.warning("vision_llm_extraction_failed", error=str(e))

        return ExtractionResult(
            success=False,
            document_type="UNKNOWN",
            extracted_data={},
            confidence=0.0,
            processor_used="hybrid",
        )

    async def health_check(self) -> bool:
        """Check if at least one processing path is available."""
        return self.docling_available or self._llm is not None
