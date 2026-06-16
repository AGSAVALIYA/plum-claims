"""OpenAI LLM adapter with tenacity retries.

Supports OpenAI-compatible APIs including DeepSeek via custom base_url.
For structured output with DeepSeek, uses response_format={'type': 'json_object'}
and injects 'json' keyword into the system prompt per DeepSeek docs.
"""

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


# Model costs per 1K tokens for OpenAI-compatible models
MODEL_COSTS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "deepseek-chat": {"input": 0.001, "output": 0.004},
    "deepseek-v4": {"input": 0.001, "output": 0.004},
}


def _compute_openai_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute LLM call cost from token counts using model-specific rates."""
    for key, rates in MODEL_COSTS.items():
        if key in model or model in key:
            input_cost = (input_tokens / 1000) * rates["input"]
            output_cost = (output_tokens / 1000) * rates["output"]
            return input_cost + output_cost
    return 0.0


class OpenAIAdapter(ILLMProvider):
    """LLM provider adapter for OpenAI-compatible APIs (OpenAI, DeepSeek, etc.)."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import AsyncOpenAI

            kwargs: dict[str, Any] = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncOpenAI(**kwargs)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError)),
        reraise=True,
    )
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request."""
        try:
            client = self._get_client()

            # Build messages — for DeepSeek JSON mode, inject 'json' into system prompt
            messages = list(request.messages)
            if request.response_schema:
                for i, m in enumerate(messages):
                    if m.get("role") == "system":
                        if "json" not in m.get("content", "").lower():
                            messages[i] = {
                                **m,
                                "content": m["content"]
                                + "\n\nYou MUST respond with valid JSON only. No markdown, no explanation.",
                            }
                        break
                else:
                    messages.insert(
                        0,
                        {
                            "role": "system",
                            "content": "You MUST respond with valid JSON only. No markdown, no explanation.",
                        },
                    )

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            if request.response_schema:
                # DeepSeek uses 'json_object' type, OpenAI uses 'json_schema'
                is_deepseek = self.base_url and "deepseek" in self.base_url
                if is_deepseek:
                    kwargs["response_format"] = {"type": "json_object"}
                else:
                    kwargs["response_format"] = {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "response",
                            "schema": request.response_schema,
                        },
                    }

            completion = await client.chat.completions.create(**kwargs)
            content = completion.choices[0].message.content or ""

            # Normalize usage to input_tokens / output_tokens
            prompt_tokens = completion.usage.prompt_tokens if completion.usage else 0
            completion_tokens = completion.usage.completion_tokens if completion.usage else 0
            usage = {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
            }
            cost = _compute_openai_cost(self.model, prompt_tokens, completion_tokens)

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
            raise LLMProviderError("openai", str(e))

    async def extract_structured(self, request: LLMRequest) -> dict[str, Any]:
        """Send request and return structured JSON output only.

        Validates response against the schema if provided, and retries once
        with an error correction prompt if validation fails.
        Injects _llm_usage and _llm_cost into the returned dict for cost tracking.
        """
        import json

        # Track total usage and cost across all chat() calls
        total_usage: dict[str, int] = {}
        total_cost = 0.0

        def _accumulate(response: LLMResponse) -> None:
            nonlocal total_cost
            for k, v in response.usage.items():
                total_usage[k] = total_usage.get(k, 0) + v
            total_cost += response.cost

        response = await self.chat(request)
        _accumulate(response)

        if response.structured_output:
            parsed = response.structured_output
        else:
            try:
                parsed = json.loads(response.content)
            except json.JSONDecodeError:
                if isinstance(parsed := {"_raw": response.content}, dict):
                    parsed["_llm_usage"] = total_usage
                    parsed["_llm_cost"] = total_cost
                return parsed

        # Validate against schema if provided; retry once on failure
        if request.response_schema:
            if not self._validate_schema(parsed, request.response_schema):
                # Retry once with error correction prompt
                retry_request = LLMRequest(
                    messages=list(request.messages) + [
                        {
                            "role": "user",
                            "content": (
                                f"Your previous response did not match the required schema. "
                                f"The schema requires these fields: {json.dumps(request.response_schema)}. "
                                f"Your response was: {response.content}. "
                                f"Please return valid JSON that matches the schema exactly."
                            ),
                        }
                    ],
                    response_schema=request.response_schema,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                )
                retry_response = await self.chat(retry_request)
                _accumulate(retry_response)
                if retry_response.structured_output:
                    parsed = retry_response.structured_output
                else:
                    try:
                        parsed = json.loads(retry_response.content)
                    except json.JSONDecodeError:
                        parsed = {"_raw": response.content, "_schema_error": f"Failed to match schema after retry. Expected: {json.dumps(request.response_schema)}"}

        if isinstance(parsed, dict):
            parsed["_llm_usage"] = total_usage
            parsed["_llm_cost"] = total_cost
        return parsed

    @staticmethod
    def _validate_schema(parsed: dict, schema: dict) -> bool:
        """Validate parsed JSON against a JSON Schema-like dict."""
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields exist
        for field in required:
            if field not in parsed:
                return False

        # Check types for defined properties
        for field, value in parsed.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
                elif expected_type == "array" and not isinstance(value, list):
                    return False
                # Check enum values
                enum_vals = properties[field].get("enum")
                if enum_vals and value not in enum_vals:
                    return False

        return True

    async def health_check(self) -> bool:
        """Check if the provider is available."""
        try:
            client = self._get_client()
            await client.models.list()
            return True
        except Exception:
            return False
