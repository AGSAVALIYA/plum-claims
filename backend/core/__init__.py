"""Core cross-cutting concerns — config, exceptions, logging, telemetry."""

from backend.core.config import settings
from backend.core.exceptions import PlumException

__all__ = ["PlumException", "settings"]
