"""Redis cache adapter."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from backend.providers.cache.interface import ICacheProvider


class RedisCacheAdapter(ICacheProvider):
    """Redis-backed cache adapter."""

    def __init__(self, redis_url: str = "redis://redis:6379/0") -> None:
        self.redis_url = redis_url
        self._client: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._client

    async def get(self, key: str) -> Any | None:
        try:
            client = await self._get_client()
            value = await client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            client = await self._get_client()
            if not isinstance(value, str):
                value = json.dumps(value)
            if ttl:
                await client.setex(key, ttl, value)
            else:
                await client.set(key, value)
        except Exception:
            pass

    async def delete(self, key: str) -> None:
        try:
            client = await self._get_client()
            await client.delete(key)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception:
            return False

    async def flush(self) -> None:
        try:
            client = await self._get_client()
            await client.flushdb()
        except Exception:
            pass
