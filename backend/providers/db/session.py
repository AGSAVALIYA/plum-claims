"""Database session management using SQLAlchemy async."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class DatabaseSession:
    """Manages AsyncEngine and session factory."""

    def __init__(self, database_url: str | None = None) -> None:
        self._engine = create_async_engine(
            database_url or settings.database_url,
            echo=settings.database_echo,
            pool_size=10,
            max_overflow=20,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @property
    def engine(self):
        return self._engine

    @property
    def session_factory(self):
        return self._session_factory

    async def create_all(self) -> None:
        """Create all tables (for dev/testing)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        """Drop all tables (for testing)."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def close(self) -> None:
        await self._engine.dispose()


# Global session factory instance
_db: DatabaseSession | None = None


def get_db() -> DatabaseSession:
    global _db
    if _db is None:
        _db = DatabaseSession()
    return _db


async def get_session() -> AsyncSession:
    """Dependency that yields an async database session.

    Commits on successful request, rolls back on exception.
    """
    db = get_db()
    async with db.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
