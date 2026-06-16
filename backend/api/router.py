"""Main API router."""

from fastapi import APIRouter

from backend.api.v1.admin import router as admin_router
from backend.api.v1.auth import router as auth_router
from backend.api.v1.claims import router as claims_router
from backend.api.v1.documents import router as documents_router
from backend.core.config import settings

api_router = APIRouter(prefix=settings.api_prefix)
api_router.include_router(auth_router)
api_router.include_router(claims_router)
api_router.include_router(documents_router)
api_router.include_router(admin_router)
