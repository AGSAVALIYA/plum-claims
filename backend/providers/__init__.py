"""Provider abstraction layer — interfaces and adapters for external dependencies.

Providers:
- cache: ICacheProvider → RedisCacheAdapter / InMemoryCacheAdapter
- db: DatabaseSession, async SQLAlchemy engine
- llm: ILLMProvider → OpenAIAdapter / AnthropicAdapter / MockLLMAdapter
- storage: IStorageProvider → LocalStorageAdapter
"""

__all__: list[str] = []
