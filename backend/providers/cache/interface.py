"""Cache provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ICacheProvider(ABC):
    """Interface for caching providers (Redis, InMemory)."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Get a value from the cache."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set a value in the cache with optional TTL in seconds."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a key from the cache."""
        ...

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...

    @abstractmethod
    async def flush(self) -> None:
        """Clear all cached entries."""
        ...
