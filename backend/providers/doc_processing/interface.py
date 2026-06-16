"""Document processor interface and data types.

Per planning doc 01_system_architecture.md: Abstract interface for document
processing — classification, quality assessment, and structured extraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DocumentType:
    """Detected document type with confidence."""

    primary_type: str  # e.g., "PRESCRIPTION", "HOSPITAL_BILL", "LAB_REPORT"
    confidence: float  # 0.0–1.0
    alternative_types: list[str] = field(default_factory=list)


@dataclass
class QualityAssessment:
    """Document quality assessment result."""

    is_readable: bool
    score: float  # 0.0–1.0 (1.0 = perfectly clear)
    issues: list[str] = field(default_factory=list)
    # Possible issues: "low_resolution", "blurry", "handwritten", "scanned",
    #   "skewed", "multi_language", "watermark")


@dataclass
class ExtractionResult:
    """Structured data extracted from a document."""

    success: bool
    document_type: str
    extracted_data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_text: str | None = None
    field_confidences: dict[str, float] = field(default_factory=dict)
    processor_used: str = ""  # "docling" or "vision_llm"


class IDocumentProcessor(ABC):
    """Abstract interface for document processing."""

    @abstractmethod
    async def classify_document(self, file_bytes: bytes, filename: str) -> DocumentType:
        """Determine the type of document (prescription, bill, lab report, etc.)."""
        ...

    @abstractmethod
    async def assess_quality(self, file_bytes: bytes) -> QualityAssessment:
        """Assess document readability and quality."""
        ...

    @abstractmethod
    async def extract_text(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        """Extract raw text from the document."""
        ...

    @abstractmethod
    async def extract_structured(
        self,
        file_bytes: bytes,
        filename: str,
        schema: dict[str, Any],
    ) -> ExtractionResult:
        """Extract structured data matching the given JSON schema."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify the processor's dependencies are available."""
        ...
