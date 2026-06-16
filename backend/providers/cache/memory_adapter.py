"""In-memory cache adapter for testing and development."""

from __future__ import annotations

import time
from typing import Any

from backend.providers.cache.interface import ICacheProvider


class InMemoryCacheAdapter(ICacheProvider):
    """Simple in-memory cache for development and testing."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float | None]] = {}

    async def get(self, key: str) -> Any | None:
        """Get value, respecting TTL."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set value with optional TTL in seconds."""
        expires_at = time.monotonic() + ttl if ttl else None
        self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        val = await self.get(key)
        return val is not None

    async def flush(self) -> None:
        """Clear all entries."""
        self._store.clear()
