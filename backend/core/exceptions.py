"""Domain exception hierarchy for Plum Claims."""

from __future__ import annotations

from typing import Any


class PlumException(Exception):
    """Base exception for all Plum domain errors."""

    def __init__(
        self,
        message: str,
        code: str = "PLUM_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ── Validation Errors (422) ──────────────────────────────────────


class DocumentValidationError(PlumException):
    """Raised when uploaded documents fail verification rules."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="DOCUMENT_VALIDATION_FAILED", details=details)


class ClaimValidationError(PlumException):
    """Raised when claim submission data is invalid."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="CLAIM_VALIDATION_FAILED", details=details)


# ── Not Found Errors (404) ───────────────────────────────────────


class ResourceNotFoundError(PlumException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str | int) -> None:
        super().__init__(
            f"{resource_type} with id {resource_id} not found",
            code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


# ── Policy Errors ────────────────────────────────────────────────


class PolicyLoadError(PlumException):
    """Raised when policy terms cannot be loaded."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="POLICY_LOAD_FAILED")


class PolicyRuleViolation(PlumException):
    """Raised when a claim violates a policy rule (used internally)."""

    def __init__(
        self,
        rule_name: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code=f"POLICY_{rule_name.upper()}", details=details)


# ── Upstream / Provider Errors ───────────────────────────────────


class LLMProviderError(PlumException):
    """Raised when an LLM provider fails."""

    def __init__(self, provider: str, message: str) -> None:
        super().__init__(
            f"LLM provider '{provider}' error: {message}",
            code="LLM_PROVIDER_ERROR",
            details={"provider": provider},
        )


class StorageProviderError(PlumException):
    """Raised when a storage operation fails."""

    def __init__(self, operation: str, message: str) -> None:
        super().__init__(
            f"Storage error during {operation}: {message}",
            code="STORAGE_ERROR",
            details={"operation": operation},
        )


class ExtractionError(PlumException):
    """Raised when document extraction fails."""

    def __init__(self, document_id: int, message: str) -> None:
        super().__init__(
            f"Extraction failed for document {document_id}: {message}",
            code="EXTRACTION_FAILED",
            details={"document_id": document_id},
        )
