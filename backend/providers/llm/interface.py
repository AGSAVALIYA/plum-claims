"""LLM Provider interface and types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMRequest:
    """A request to an LLM provider."""

    messages: list[dict[str, Any]]
    response_schema: dict[str, Any] | None = None
    temperature: float = 0.1
    max_tokens: int = 4096
    cache_key: str | None = None


@dataclass
class LLMResponse:
    """A response from an LLM provider."""

    content: str
    model: str = ""
    usage: dict = field(default_factory=dict)  # {"input_tokens": N, "output_tokens": N}
    cost: float = 0.0
    duration_ms: float = 0.0
    structured_output: dict | None = None
    finish_reason: str = "stop"
    cached: bool = False


class ILLMProvider(ABC):
    """Interface for LLM providers (OpenAI, Anthropic, Mock)."""

    @abstractmethod
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request and return the response."""
        ...

    @abstractmethod
    async def extract_structured(self, request: LLMRequest) -> dict[str, Any]:
        """Send a request and parse structured JSON output."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available."""
        ...
