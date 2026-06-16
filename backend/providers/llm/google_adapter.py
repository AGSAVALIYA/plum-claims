"""Google Gemini LLM adapter with tenacity retries.

Per planning doc 01_system_architecture.md: Google Gemini adapter supporting
structured output via the google-genai SDK.
Supports gemini-3.5-flash with thinking capabilities.
"""

from __future__ import annotations

import json
from typing import Any

import httpx

from backend.core.logging import get_logger

logger = get_logger(__name__)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.core.exceptions import LLMProviderError
from backend.providers.llm.interface import ILLMProvider, LLMRequest, LLMResponse


# Model costs per 1K tokens for Google Gemini models
MODEL_COSTS: dict[str, dict[str, float]] = {
    "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
}


def _compute_google_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Compute LLM call cost from token counts using model-specific rates."""
    for key, rates in MODEL_COSTS.items():
        if key in model or model in key:
            input_cost = (input_tokens / 1000) * rates["input"]
            output_cost = (output_tokens / 1000) * rates["output"]
            return input_cost + output_cost
    return 0.0


class GoogleGeminiAdapter(ILLMProvider):
    """LLM provider adapter for Google's Gemini API (gemini-3.5-flash)."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model = model
        self._client: Any = None
        self._types: Any = None  # google.genai.types

    def _get_client(self) -> Any:
        """Lazy-initialize the Google GenAI client."""
        if self._client is None:
            try:
                from google import genai  # type: ignore[import-untyped]
                from google.genai import types  # type: ignore[import-untyped]
            except ImportError:
                raise LLMProviderError(
                    "google",
                    "google-genai package is required. Install with: pip install google-genai",
                )
            self._client = genai.Client(api_key=self.api_key)
            self._types = types
        return self._client

    def _get_types(self) -> Any:
        """Get the google.genai.types module."""
        if self._types is None:
            from google.genai import types  # type: ignore[import-untyped]

            self._types = types
        return self._types

    def _extract_system_message(self, messages: list[dict[str, Any]]) -> str | None:
        for m in messages:
            if m.get("role") == "system":
                return m["content"]
        return None

    def _build_contents(self, messages: list[dict[str, Any]]) -> list[Any]:
        """Build google.genai.types.Content list from messages.

        Handles both plain-text messages (content is a string) and
        multimodal messages (content is a list of OpenAI-format parts
        like {'type': 'text', 'text': '...'} or
        {'type': 'image_url', 'image_url': {'url': 'data:mime;base64,...'}}).
        """
        types = self._get_types()
        contents: list[Any] = []
        for m in messages:
            role = m.get("role", "user")
            if role == "system":
                continue  # Handled via system_instruction
            content = m.get("content", "")

            if isinstance(content, str):
                # Plain text message
                contents.append(
                    types.Content(
                        role="user" if role == "user" else "model",
                        parts=[types.Part.from_text(text=content)],
                    )
                )
            elif isinstance(content, list):
                # Multimodal message: convert each OpenAI-format part to a genai Part
                parts: list[Any] = []
                for part in content:
                    part_type = part.get("type", "")
                    if part_type == "text":
                        parts.append(types.Part.from_text(text=part.get("text", "")))
                    elif part_type == "image_url":
                        image_url = part.get("image_url", {}).get("url", "")
                        # Parse data: URL — format is "data:<mime>;base64,<b64data>"
                        if image_url.startswith("data:"):
                            header, b64data = image_url.split(",", 1)
                            mime_type = header.split(":")[1].split(";")[0] if ":" in header else "image/png"
                            import base64
                            image_bytes = base64.b64decode(b64data)
                            parts.append(
                                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                            )
                        else:
                            # External URL — use from_uri
                            parts.append(
                                types.Part.from_uri(file_uri=image_url, mime_type="image/png")
                            )
                    elif part_type == "file":
                        # File/PDF attachment
                        file_data = part.get("file_data", "")
                        file_name = part.get("filename", "document")
                        if file_data.startswith("data:"):
                            pass  # handled below
                        else:
                            logger.warning("google_adapter_skipped_file_part", file_name=file_name, reason="file_data is not a data: URI")
                        if file_data.startswith("data:"):
                            header, b64data = file_data.split(",", 1)
                            mime_type = header.split(":")[1].split(";")[0] if ":" in header else "application/pdf"
                            import base64
                            file_bytes = base64.b64decode(b64data)
                            parts.append(
                                types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
                            )
                    else:
                        # Unknown part type — try treating as text
                        text_val = part.get("text") or part.get("content") or str(part)
                        parts.append(types.Part.from_text(text=str(text_val)))
                contents.append(
                    types.Content(
                        role="user" if role == "user" else "model",
                        parts=parts,
                    )
                )
            else:
                # Fallback: coerce to string
                logger.warning("google_adapter_coerced_content_to_string", content_type=type(content).__name__)
                contents.append(
                    types.Content(
                        role="user" if role == "user" else "model",
                        parts=[types.Part.from_text(text=str(content))],
                    )
                )
        return contents

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ReadTimeout, httpx.ConnectError)),
        reraise=True,
    )
    async def chat(self, request: LLMRequest) -> LLMResponse:
        """Send a chat completion request to Google Gemini."""
        try:
            client = self._get_client()
            types = self._get_types()
            system = self._extract_system_message(request.messages)
            contents = self._build_contents(request.messages)

            # Build GenerateContentConfig
            config_kwargs: dict[str, Any] = {
                "temperature": request.temperature,
                "max_output_tokens": request.max_tokens,
            }
            if system:
                config_kwargs["system_instruction"] = system
            if request.response_schema:
                config_kwargs["response_mime_type"] = "application/json"
                config_kwargs["response_schema"] = request.response_schema

            # Enable thinking for gemini-3.5-flash (thinking_level="MEDIUM")
            if "3.5" in self.model or "pro" in self.model.lower():
                config_kwargs["thinking_config"] = types.ThinkingConfig(
                    thinking_level="MEDIUM",
                )

            config = types.GenerateContentConfig(**config_kwargs)

            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )

            content = response.text or ""

            # Normalize usage to input_tokens / output_tokens
            prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            usage = {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
            }
            cost = _compute_google_cost(self.model, prompt_tokens, completion_tokens)

            structured_output = None
            if request.response_schema and content:
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
        except LLMProviderError:
            raise
        except Exception as e:
            raise LLMProviderError("google", str(e))

    async def extract_structured(self, request: LLMRequest) -> dict[str, Any]:
        """Send request and return structured JSON output only.
        Injects _llm_usage and _llm_cost into the returned dict for cost tracking.
        """
        response = await self.chat(request)
        if response.structured_output:
            result = response.structured_output
        else:
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
        """Check if the provider is available."""
        try:
            client = self._get_client()
            types = self._get_types()
            response = client.models.generate_content(
                model=self.model,
                contents=types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="ping")],
                ),
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            # Check text or candidates for successful response
            if response.text:
                return True
            if response.candidates and response.candidates[0].content:
                return True
            return False
        except Exception:
            return False
