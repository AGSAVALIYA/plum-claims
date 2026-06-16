"""Structured logging configuration using structlog."""

from __future__ import annotations

import logging
import re

import structlog

from backend.core.config import settings

# ── PHI/PII patterns for log scrubbing ──────────────────────────

_SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)patient_name[=:]\s*['\"]?([^'\"},]+)"), r"patient_name=[REDACTED]"),
    (re.compile(r"(?i)doctor_name[=:]\s*['\"]?([^'\"},]+)"), r"doctor_name=[REDACTED]"),
    (
        re.compile(r"(?i)patient_name_on_doc[=:]\s*['\"]?([^'\"},]+)"),
        r"patient_name_on_doc=[REDACTED]",
    ),
    (re.compile(r"(?i)name[=:]\s*['\"]?([^'\"},]+)"), r"name=[REDACTED]"),
    (re.compile(r"(?i)diagnosis[=:]\s*['\"]?([^'\"},]+)"), r"diagnosis=[REDACTED]"),
    (re.compile(r"(?i)diagnosis_text[=:]\s*['\"]?([^'\"},]+)"), r"diagnosis_text=[REDACTED]"),
    (
        re.compile(r"(?i)doctor_registration[=:]\s*['\"]?([^'\"},]+)"),
        r"doctor_registration=[REDACTED]",
    ),
]

_SENSITIVE_KEYS = frozenset(
    {
        "patient_name",
        "patient_name_on_doc",
        "doctor_name",
        "doctor_registration",
        "diagnosis",
        "diagnosis_text",
        "dob",
        "ssn",
        "phone",
        "email",
        "address",
    }
)


def _redact_string(value: str) -> str:
    """Apply regex-based redaction to a string value."""
    for pattern, replacement in _SENSITIVE_PATTERNS:
        value = pattern.sub(replacement, value)
    return value


def _redact_sensitive(_, __, event_dict: dict) -> dict:
    """Structlog processor: redact PHI/PII from event dictionaries."""
    for key in _SENSITIVE_KEYS:
        if key in event_dict:
            event_dict[key] = "[REDACTED]"

    # Also redact any string values that match patterns
    for key, value in event_dict.items():
        if isinstance(value, str) and key not in ("event", "level", "logger", "timestamp"):
            event_dict[key] = _redact_string(value)

    return event_dict


def add_open_telemetry_spans(_, __, event_dict: dict) -> dict:
    """Add trace_id and span_id from OpenTelemetry context to log entries."""
    try:
        from opentelemetry.trace import get_current_span

        span = get_current_span()
        if span.is_recording():
            ctx = span.get_span_context()
            if ctx.is_valid:
                event_dict["trace_id"] = format(ctx.trace_id, "032x")
                event_dict["span_id"] = format(ctx.span_id, "016x")
    except Exception:
        pass
    return event_dict


def setup_logging() -> None:
    """Configure structlog for the application."""
    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_open_telemetry_spans,
        _redact_sensitive,
    ]

    if settings.log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Quiet noisy third-party loggers
    for lib in ("openai", "httpx", "httpcore", "urllib3", "aiosqlite"):
        logging.getLogger(lib).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger for the given name."""
    return structlog.get_logger(name)
