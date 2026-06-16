"""LLM response caching with content-addressable SHA-256 keys.

Per planning doc 05_caching_strategy.md:
- Cache key: plum:llm:{model}:{prompt_hash[:16]}
- TTL: 24 hours for completions, 7 days for document extraction
- Compression: gzip for responses > 1KB
- Serialization: JSON (msgpack-preferred but JSON for portability)
- Metrics: llm_cache_hits_total, llm_cache_misses_total, llm_cache_cost_savings_total
"""

from __future__ import annotations

import gzip
import hashlib
import json
from typing import Any

from backend.core.logging import get_logger
from backend.core.telemetry import record_llm_cache_hit, record_llm_cache_miss
from backend.providers.llm.interface import ILLMProvider, LLMRequest, LLMResponse

logger = get_logger(__name__)

# ── Constants ──────────────────────────────────────────────────────

COMPLETION_TTL = 86_400  # 24 hours
EXTRACTION_TTL = 604_800  # 7 days
COMPRESSION_THRESHOLD = 1024  # 1 KB


def _compute_cache_key(model: str, messages: list[dict[str, Any]]) -> str:
    """Compute a content-addressable cache key from the request content.

    Uses SHA-256 hash of the serialized messages + model to produce a
    deterministic, collision-resistant key.
    """
    content = json.dumps(messages, sort_keys=True, default=str)
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    return f"plum:llm:{model}:{content_hash[:16]}"


def _compress(data: bytes) -> bytes:
    """gzip-compress data if it exceeds the compression threshold."""
    if len(data) > COMPRESSION_THRESHOLD:
        return gzip.compress(data)
    return data


def _decompress(data: bytes) -> bytes:
    """Decompress gzip-compressed data, or return as-is if not compressed."""
    try:
        return gzip.decompress(data)
    except gzip.BadGzipFile:
        return data


class CachedLLMProvider:
    """Decorator/wrapper that adds response caching to any ILLMProvider.

    Usage:
        base_provider = OpenAIAdapter(api_key="...", model="gpt-4o")
        cached_provider = CachedLLMProvider(base_provider, cache_adapter)
        response = await cached_provider.chat(request)
    """

    def __init__(
        self,
        provider: ILLMProvider,
        cache_adapter,
        default_ttl: int = COMPLETION_TTL,
    ) -> None:
        self._provider = provider
        self._cache = cache_adapter
        self._default_ttl = default_ttl

    @property
    def model(self) -> str:
        if hasattr(self._provider, "model"):
            return self._provider.model
        return "unknown"

    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Chat completion with caching."""
        cache_key = request.cache_key or _compute_cache_key(self.model, request.messages)

        # Check cache
        try:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                record_llm_cache_hit(self.model)
                logger.debug("llm_cache_hit", cache_key=cache_key, model=self.model)
                return self._deserialize_response(cached)
        except Exception:
            pass

        record_llm_cache_miss(self.model)
        logger.debug("llm_cache_miss", cache_key=cache_key, model=self.model)

        # Call provider
        response = await self._provider.chat(request)

        # Store in cache
        try:
            ttl = EXTRACTION_TTL if request.response_schema is not None else self._default_ttl
            serialized = self._serialize_response(response)
            await self._cache.set(cache_key, serialized, ttl=ttl)
        except Exception as e:
            logger.warning("llm_cache_store_failed", error=str(e))

        return response

    async def extract_structured(self, request: LLMRequest) -> dict[str, Any]:
        """Structured extraction with caching.
        Injects _llm_usage and _llm_cost into the returned dict for cost tracking.
        """
        cache_key = request.cache_key or _compute_cache_key(self.model, request.messages)

        # Check cache
        try:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                record_llm_cache_hit(self.model)
                logger.debug("llm_cache_hit", cache_key=cache_key, model=self.model)
                response = self._deserialize_response(cached)
                if response.structured_output:
                    result = response.structured_output
                else:
                    result = json.loads(response.content)
                if isinstance(result, dict):
                    result.setdefault("_llm_usage", response.usage)
                    result.setdefault("_llm_cost", response.cost)
                return result
        except Exception:
            pass

        record_llm_cache_miss(self.model)
        result = await self._provider.extract_structured(request)

        # Store in cache
        try:
            llm_usage = result.get("_llm_usage", {}) if isinstance(result, dict) else {}
            llm_cost = result.get("_llm_cost", 0.0) if isinstance(result, dict) else 0.0
            response = LLMResponse(
                content=json.dumps(result),
                structured_output=result if isinstance(result, dict) else None,
                model=self.model,
                usage=llm_usage,
                cost=llm_cost,
            )
            serialized = self._serialize_response(response)
            await self._cache.set(cache_key, serialized, ttl=EXTRACTION_TTL)
        except Exception as e:
            logger.warning("llm_cache_store_failed", error=str(e))

        return result

    async def health_check(self) -> bool:
        return await self._provider.health_check()

    @staticmethod
    def _serialize_response(response: LLMResponse) -> bytes:
        """Serialize an LLMResponse to compressed bytes for cache storage."""
        data = {
            "content": response.content,
            "structured_output": response.structured_output,
            "usage": response.usage,
            "cost": response.cost,
            "model": response.model,
            "cached": True,
        }
        raw = json.dumps(data).encode("utf-8")
        return _compress(raw)

    @staticmethod
    def _deserialize_response(data: Any) -> LLMResponse:
        """Deserialize cached bytes back to an LLMResponse."""
        if isinstance(data, bytes):
            raw = _decompress(data)
            parsed = json.loads(raw)
        elif isinstance(data, str):
            parsed = json.loads(data)
        elif isinstance(data, dict):
            parsed = data
        else:
            raise ValueError(f"Unexpected cache data type: {type(data)}")

        return LLMResponse(
            content=parsed.get("content", ""),
            structured_output=parsed.get("structured_output"),
            usage=parsed.get("usage", {}),
            cost=parsed.get("cost", 0.0),
            model=parsed.get("model", ""),
            cached=True,
        )
