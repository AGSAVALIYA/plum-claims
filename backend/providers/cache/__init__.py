"""Cache provider — Redis and in-memory adapters."""

from backend.providers.cache.interface import ICacheProvider
from backend.providers.cache.memory_adapter import InMemoryCacheAdapter
from backend.providers.cache.redis_adapter import RedisCacheAdapter

__all__ = ["ICacheProvider", "InMemoryCacheAdapter", "RedisCacheAdapter"]
