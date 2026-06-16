"""API v1 endpoints — claims and documents REST resources."""

from backend.api.v1.claims import router as claims_router
from backend.api.v1.documents import router as documents_router

__all__ = ["claims_router", "documents_router"]
