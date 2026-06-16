"""Mock LLM adapter for testing and development without API keys."""

from __future__ import annotations

from typing import Any

from backend.providers.llm.interface import ILLMProvider, LLMRequest, LLMResponse


class MockLLMAdapter(ILLMProvider):
    """Mock LLM provider that returns predefined responses for testing."""

    def __init__(self, simulate_failure: bool = False) -> None:
        self.simulate_failure = simulate_failure
        self.call_count = 0

    async def chat(self, request: LLMRequest) -> LLMResponse:
        self.call_count += 1
        if self.simulate_failure:
            raise RuntimeError("Simulated LLM failure")

        # Return a reasonable mock response based on the request context
        content = self._generate_mock_content(request)
        return LLMResponse(
            content=content,
            usage={"input_tokens": 0, "output_tokens": 0},
            cost=0.0,
            model="mock-llm",
        )

    def _generate_mock_content(self, request: LLMRequest) -> str:
        """Generate a plausible mock response based on the system prompt."""
        import json

        system_text = ""
        for m in request.messages:
            if m.get("role") == "system":
                system_text = str(m.get("content", ""))
                break

        # Document classification mock
        if "classify" in system_text.lower():
            return json.dumps(
                {
                    "document_type": "PRESCRIPTION",
                    "confidence": 0.92,
                    "is_readable": True,
                }
            )

        # Document extraction mock - based on user content
        user_text = ""
        for m in request.messages:
            if m.get("role") == "user":
                user_text = str(m.get("content", ""))
                break

        # Return structured output based on schema if present
        if request.response_schema:
            schema = request.response_schema
            if isinstance(schema, dict):
                properties = schema.get("properties", {})
                result = {}
                for key, prop in properties.items():
                    if key in ("doctor_name", "patient_name"):
                        result[key] = "Mock Patient" if "patient" in key else "Dr. Mock Doctor"
                    elif key in ("diagnosis",):
                        result[key] = "General Checkup"
                    elif key in ("total", "amount"):
                        result[key] = 1500.0
                    elif key == "date":
                        result[key] = "2024-11-01"
                    elif key == "line_items":
                        result[key] = [{"description": "Consultation", "amount": 1500.0}]
                    elif key == "medicines":
                        result[key] = ["Paracetamol 650mg"]
                    elif key == "hospital_name":
                        result[key] = "Mock Hospital"
                    elif key == "doctor_registration":
                        result[key] = "KA/45678/2015"
                    elif key == "test_name":
                        result[key] = "Complete Blood Count"
                    elif key == "tests_ordered":
                        result[key] = ["CBC"]
                    else:
                        # Use schema hints to provide a valid mock value
                        result[key] = self._mock_value_for_schema(key, prop)
                return json.dumps(result)

    def _mock_value_for_schema(self, key: str, prop: dict) -> Any:
        """Return a valid mock value based on the JSON Schema property definition."""
        prop_type = prop.get("type", "string")
        enum_vals = prop.get("enum")

        # Enum fields: use the first valid option
        if enum_vals:
            if key in ("decision", "final_decision", "policy_decision"):
                return "APPROVED" if "APPROVED" in enum_vals else enum_vals[0]
            if key == "recommendation":
                return "PROCEED" if "PROCEED" in enum_vals else enum_vals[0]
            if key == "risk_level":
                return "LOW" if "LOW" in enum_vals else enum_vals[0]
            return enum_vals[0]

        # Numeric fields
        if prop_type in ("number", "integer"):
            if key in ("fraud_score",):
                return 0.0
            if key in ("confidence", "ai_confidence"):
                return 0.85
            if key in ("approved_amount", "final_amount"):
                return 1500.0
            return 0

        # Boolean fields
        if prop_type == "boolean":
            if key == "is_medical_content":
                return True
            if key in ("requires_human_review", "manual_review_recommended"):
                return False
            return True

        # Array fields
        if prop_type == "array":
            return []

        # String fields — provide realistic mock values based on key name
        if key in ("reasoning", "decision_reason", "ai_reasoning"):
            return "Claim processed successfully. All policy checks passed."
        if key == "content_type":
            return "prescription"
        if key == "patient_name":
            return "Rajesh Kumar"
        if key == "doctor_name":
            return "Dr. Arun Sharma"
        if key == "diagnosis":
            return "General Checkup"
        if key == "treatment":
            return "General Consultation"
        if key == "hospital_name":
            return "Apollo Hospitals"
        if key == "doctor_registration":
            return "KA/45678/2015"

        return "mock"

    async def extract_structured(self, request: LLMRequest) -> dict[str, Any]:
        """Send a request and return structured JSON output with schema validation.
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

        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError:
            error_result: dict[str, Any] = {"_raw": response.content}
            error_result["_llm_usage"] = total_usage
            error_result["_llm_cost"] = total_cost
            return error_result

        # Validate against schema if provided
        if request.response_schema and not self._validate_schema(parsed, request.response_schema):
            # Retry once with error correction prompt
            correction_request = LLMRequest(
                messages=request.messages + [
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
            retry_response = await self.chat(correction_request)
            _accumulate(retry_response)
            try:
                parsed = json.loads(retry_response.content)
            except json.JSONDecodeError:
                error_result = {"_raw": response.content, "_schema_error": f"Failed to parse after retry. Expected schema: {json.dumps(request.response_schema)}"}
                error_result["_llm_usage"] = total_usage
                error_result["_llm_cost"] = total_cost
                return error_result

        if isinstance(parsed, dict):
            parsed["_llm_usage"] = total_usage
            parsed["_llm_cost"] = total_cost
        return parsed

    @staticmethod
    def _validate_schema(parsed: dict, schema: dict) -> bool:
        """Validate parsed JSON against a JSON Schema-like dict."""
        import json

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
        return not self.simulate_failure
