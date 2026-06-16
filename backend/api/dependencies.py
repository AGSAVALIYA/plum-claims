"""API dependencies for FastAPI dependency injection."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.providers.db.session import get_session


async def get_db_session() -> AsyncSession:
    """Dependency that yields a database session."""
    async for session in get_session():
        yield session
