"""Application configuration via Pydantic BaseSettings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Application
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    cors_origins: str = "http://localhost:3000"
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://plum_admin:password123@db:5432/plum_claims"
    database_echo: bool = False

    # Redis / Cache
    redis_url: str = "redis://redis:6379/0"
    redis_enabled: bool = True

    # LLM Provider
    llm_provider: Literal["openai", "anthropic", "google", "mock"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_base_url: str = Field(default="", validation_alias="OPENAI_BASE_URL")
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    google_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    google_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")

    # Document Processing
    document_processor: Literal["hybrid", "docling_only", "vision_only"] = "hybrid"
    docling_ocr_engine: str = "easyocr"

    # Storage
    storage_provider: Literal["local", "minio", "s3"] = "local"
    storage_path: str = "/workspace/backend/uploads"

    # Observability
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"
    otel_exporter_otlp_endpoint: str = "http://jaeger:4317"
    otel_service_name: str = "plum-claims"
    enable_tracing: bool = True
    enable_metrics: bool = True

    # Security
    jwt_secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 60
    rate_limit_per_minute: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def policy_file_path(self) -> Path:
        env_path = os.environ.get("POLICY_FILE_PATH", "")
        if env_path:
            return Path(env_path)
        return Path(__file__).parent.parent.parent / "assignment" / "policy_terms.json"

    @property
    def test_cases_path(self) -> Path:
        env_path = os.environ.get("TEST_CASES_PATH", "")
        if env_path:
            return Path(env_path)
        return Path(__file__).parent.parent.parent / "assignment" / "test_cases.json"


settings = Settings()
