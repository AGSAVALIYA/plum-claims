"""Base agent interface for the multi-agent pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for all processing agents."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    async def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's logic and return results."""
        ...

    def agent_name(self) -> str:
        return self.name
