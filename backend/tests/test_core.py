"""Unit tests for exception handling and core utilities."""

from backend.core.exceptions import (
    DocumentValidationError,
    LLMProviderError,
    PlumException,
    ResourceNotFoundError,
)


class TestExceptions:
    """Tests for the domain exception hierarchy."""

    def test_plum_exception_base(self):
        exc = PlumException("test error", code="TEST_CODE", details={"key": "value"})
        assert exc.message == "test error"
        assert exc.code == "TEST_CODE"
        assert exc.details == {"key": "value"}
        assert str(exc) == "test error"

    def test_document_validation_error(self):
        exc = DocumentValidationError(
            "Wrong document type",
            details={"uploaded": "PRESCRIPTION", "required": "HOSPITAL_BILL"},
        )
        assert exc.code == "DOCUMENT_VALIDATION_FAILED"
        assert "HOSPITAL_BILL" in str(exc.details["required"])

    def test_resource_not_found(self):
        exc = ResourceNotFoundError("Claim", 42)
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.details["resource_id"] == 42

    def test_llm_provider_error(self):
        exc = LLMProviderError("openai", "Rate limit exceeded")
        assert exc.code == "LLM_PROVIDER_ERROR"
        assert "openai" in str(exc.message)


class TestConfig:
    """Tests for application configuration."""

    def test_settings_defaults(self):
        from backend.core.config import Settings

        settings = Settings()
        assert settings.app_env == "development"
        assert settings.api_prefix == "/api/v1"
        assert settings.cors_origins_list == ["http://localhost:3000"]

    def test_cors_origins_parsing(self):
        from backend.core.config import Settings

        settings = Settings(cors_origins="http://localhost:3000,https://example.com")
        assert settings.cors_origins_list == ["http://localhost:3000", "https://example.com"]
