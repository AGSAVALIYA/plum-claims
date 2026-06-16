"""Utility functions for JSON-safe serialization."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def to_json_safe(obj: Any) -> Any:
    """Convert an object to a JSON-serializable form.

    Recursively converts Decimal -> float and handles dicts/lists.
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: to_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [to_json_safe(item) for item in obj]
    return obj
