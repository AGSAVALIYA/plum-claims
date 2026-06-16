"""Anthropic LLM adapter with tenacity retries."""

from __future__ import annotations

from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.core.exceptions import LLMProviderError
from backend.providers.llm.interface import ILLMProvider, LLMRequest, LLMResponse


# Model costs per 1K tokens for Anthropic models
MODEL_COSTS: dict[str, dict[str, float]] = {
    "claude-sonnet-4": {"input": 0.003, "output": 0.015},
    "claude-opus-4": {"input": 0.015, "output": 0.075},
    "claude-haiku-3": {"input": 0.00025, "output": 0.00125},
}


def _compute_anthropic_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute LLM call cost from token counts using model-specific rates."""
    for key, rates in MODEL_COSTS.items():
        if key in model or model in key:
            input_cost = (input_tokens / 1000) * rates["input"]
            output_cost = (output_tokens / 1000) * rates["output"]
            return input_cost + output_cost
    return 0.0


class AnthropicAdapter(ILLMProvider):
    """LLM provider adapter for Anthropic's Claude API (supports custom base_url for proxies like DeepSeek)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from anthropic import AsyncAnthropic

            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncAnthropic(**kwargs)
        return self._client

    def _extract_system_message(self, messages: list[dict[str, Any]]) -> str | None:
        for m in messages:
            if m.get("role") == "system":
                return m["content"]
        return None

    def _extract_text(self, content_blocks: list[Any]) -> str:
        """Extract text from Anthropic content blocks (handles ThinkingBlock + TextBlock)."""
        texts = []
        thinking = []
        for block in content_blocks:
            if hasattr(block, "text"):
                texts.append(block.text)
            elif hasattr(block, "thinking"):
                thinking.append(block.thinking)
        # Prefer explicit text; fall back to thinking content (DeepSeek thinking models)
        return "\n".join(texts) if texts else "\n".join(thinking)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError)),
        reraise=True,
    )
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request to Anthropic/DeepSeek."""
        try:
            client = self._get_client()
            system = self._extract_system_message(request.messages)
            user_messages = [m for m in request.messages if m.get("role") != "system"]

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": user_messages,
                "max_tokens": request.max_tokens,
            }
            if system:
                kwargs["system"] = system

            completion = await client.messages.create(**kwargs)
            content = self._extract_text(completion.content)
            input_tokens = completion.usage.input_tokens if completion.usage else 0
            output_tokens = completion.usage.output_tokens if completion.usage else 0
            usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            }
            cost = _compute_anthropic_cost(self.model, input_tokens, output_tokens)

            structured_output = None
            if request.response_schema and content:
                import json

                try:
                    structured_output = json.loads(content)
                except json.JSONDecodeError:
                    pass

            return LLMResponse(
                content=content,
                structured_output=structured_output,
                usage=usage,
                cost=cost,
                model=self.model,
            )
        except Exception as e:
            raise LLMProviderError("anthropic", str(e))

    async def extract_structured(self, request: LLMRequest) -> dict[str, Any]:
        """Send request and return structured JSON output only.
        Injects _llm_usage and _llm_cost into the returned dict for cost tracking.
        """
        response = await self.chat(request)
        if response.structured_output:
            result = response.structured_output
        else:
            import json

            try:
                result = json.loads(response.content)
            except json.JSONDecodeError:
                error_result: dict[str, Any] = {"_raw": response.content}
                error_result["_llm_usage"] = response.usage
                error_result["_llm_cost"] = response.cost
                return error_result

        if isinstance(result, dict):
            result["_llm_usage"] = response.usage
            result["_llm_cost"] = response.cost
        return result

    async def health_check(self) -> bool:
        try:
            client = self._get_client()
            await client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception:
            return False
