"""Dependency injection container for the application.

Uses a simple manual DI approach (no heavy frameworks) suitable for a modular monolith.
Provides lazy-initialized singletons for all infrastructure dependencies.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.providers.cache.interface import ICacheProvider
    from backend.providers.db.session import DatabaseSession
    from backend.providers.doc_processing.interface import IDocumentProcessor
    from backend.providers.llm.interface import ILLMProvider
    from backend.providers.storage.interface import IStorageProvider


class Container:
    """Simple DI container holding all application singletons."""

    _instance: Container | None = None

    def __init__(self) -> None:
        self._db: DatabaseSession | None = None
        self._cache: ICacheProvider | None = None
        self._storage: IStorageProvider | None = None
        self._llm: ILLMProvider | None = None
        self._llm_raw: ILLMProvider | None = None  # Uncached base provider
        self._doc_processor: IDocumentProcessor | None = None
        self._policy_data: dict | None = None

    @property
    def db(self) -> DatabaseSession:
        if self._db is None:
            from backend.providers.db.session import DatabaseSession

            self._db = DatabaseSession()
        return self._db

    @property
    def cache(self) -> ICacheProvider:
        if self._cache is None:
            from backend.core.config import settings

            if settings.redis_enabled:
                from backend.providers.cache.redis_adapter import RedisCacheAdapter

                self._cache = RedisCacheAdapter(settings.redis_url)
            else:
                from backend.providers.cache.memory_adapter import InMemoryCacheAdapter

                self._cache = InMemoryCacheAdapter()
        return self._cache

    @property
    def storage(self) -> IStorageProvider:
        if self._storage is None:
            from backend.core.config import settings

            provider = settings.storage_provider
            if provider == "minio":
                from backend.providers.storage.minio_adapter import MinIOAdapter

                self._storage = MinIOAdapter()
            elif provider == "s3":
                from backend.providers.storage.s3_adapter import S3Adapter

                self._storage = S3Adapter()
            else:
                from backend.providers.storage.local_adapter import LocalStorageAdapter

                self._storage = LocalStorageAdapter(settings.storage_path)
        return self._storage

    @property
    def llm(self) -> ILLMProvider:
        """Get the primary LLM provider, optionally wrapped with response caching.

        When Redis is enabled, the LLM provider is wrapped with CachedLLMProvider
        for content-addressable response caching (SHA-256 based cache keys).
        """
        if self._llm is None:
            from backend.core.config import settings

            # Create the base (uncached) provider
            base_provider = self._build_llm_provider()

            # Wrap with caching if Redis is enabled
            if settings.redis_enabled:
                try:
                    from backend.providers.llm.cache import CachedLLMProvider

                    self._llm = CachedLLMProvider(base_provider, self.cache)
                except Exception:
                    self._llm = base_provider
            else:
                self._llm = base_provider

        return self._llm

    @property
    def llm_raw(self) -> ILLMProvider:
        """Get the base LLM provider without caching."""
        if self._llm_raw is None:
            self._llm_raw = self._build_llm_provider()
        return self._llm_raw

    def _build_llm_provider(self) -> ILLMProvider:
        """Build the base LLM provider from settings."""
        from backend.core.config import settings

        provider = settings.llm_provider
        if provider == "openai":
            from backend.providers.llm.openai_adapter import OpenAIAdapter

            return OpenAIAdapter(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                base_url=settings.openai_base_url or None,
            )
        elif provider == "anthropic":
            from backend.providers.llm.anthropic_adapter import AnthropicAdapter

            return AnthropicAdapter(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
            )
        elif provider == "google":
            from backend.providers.llm.google_adapter import GoogleGeminiAdapter

            return GoogleGeminiAdapter(
                api_key=getattr(settings, "google_api_key", ""),
                model=getattr(settings, "google_model", "gemini-2.0-flash"),
            )
        else:
            from backend.providers.llm.mock_adapter import MockLLMAdapter

            return MockLLMAdapter()

    @property
    def doc_processor(self) -> IDocumentProcessor:
        """Get the document processor (hybrid Docling + Vision LLM)."""
        if self._doc_processor is None:
            from backend.providers.doc_processing.hybrid_processor import (
                HybridDocumentProcessor,
            )

            # Pass the raw (uncached) LLM for vision-based extraction
            self._doc_processor = HybridDocumentProcessor(llm_provider=self.llm_raw)
        return self._doc_processor

    @property
    def policy_data(self) -> dict:
        if self._policy_data is None:
            import json

            from backend.core.config import settings

            with open(settings.policy_file_path) as f:
                self._policy_data = json.load(f)
        return self._policy_data

    def reset(self) -> None:
        """Reset all singletons (useful for testing)."""
        self._db = None
        self._cache = None
        self._storage = None
        self._llm = None
        self._llm_raw = None
        self._doc_processor = None
        self._policy_data = None


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Get the singleton DI container."""
    return Container()
