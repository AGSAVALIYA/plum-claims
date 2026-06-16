"""Document processing providers — Docling, vision LLM, and hybrid adapters.

Per planning doc 01_system_architecture.md:
- DoclingAdapter: structured digital PDFs with table extraction
- VisionLLMAdapter: handwritten/blurry docs using vision-capable LLMs
- HybridDocumentProcessor: routes to best adapter based on quality assessment
"""

from backend.providers.doc_processing.hybrid_processor import HybridDocumentProcessor
from backend.providers.doc_processing.interface import IDocumentProcessor

__all__ = ["HybridDocumentProcessor", "IDocumentProcessor"]
