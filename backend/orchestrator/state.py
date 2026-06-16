"""Orchestrator state management and processing trace models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class ProcessingStep:
    """A single step in the processing pipeline."""

    def __init__(
        self,
        step_index: int,
        step_name: str,
        agent_name: str,
    ) -> None:
        self.step_index = step_index
        self.step_name = step_name
        self.agent_name = agent_name
        self.status: str = "STARTED"
        self.input_data: dict[str, Any] = {}
        self.output_data: dict[str, Any] = {}
        self.error_message: str | None = None
        self.confidence_score: float | None = None
        self.checks_performed: list[dict[str, Any]] = []
        self.started_at: datetime = datetime.now(UTC)
        self.completed_at: datetime | None = None
        self.duration_ms: int | None = None

    def complete(self, output: dict[str, Any]) -> None:
        """Mark step as completed with output."""
        self.status = "COMPLETED"
        self.output_data = output
        self.completed_at = datetime.now(UTC)
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)
        if "confidence" in output:
            self.confidence_score = output["confidence"]
        if "checks" in output:
            self.checks_performed = output["checks"]

    def fail(self, error: str) -> None:
        """Mark step as failed."""
        self.status = "FAILED"
        self.error_message = error
        self.completed_at = datetime.now(UTC)
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def skip(self, reason: str = "") -> None:
        """Mark step as skipped."""
        self.status = "SKIPPED"
        self.error_message = reason or "Step skipped"
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        """Mark step as failed (alias for fail)."""
        self.fail(error)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "step_index": self.step_index,
            "step_name": self.step_name,
            "agent_name": self.agent_name,
            "status": self.status,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "confidence_score": self.confidence_score,
            "checks_performed": self.checks_performed,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }


class ProcessingTrace:
    """Tracks the full processing pipeline execution."""

    def __init__(self, claim_id: int) -> None:
        self.claim_id = claim_id
        self.steps: list[ProcessingStep] = []
        self.started_at: datetime = datetime.now(UTC)
        self.completed_at: datetime | None = None
        self.failed_components: list[str] = []
        self.degraded: bool = False
        self.total_llm_cost: float = 0.0
        self.total_llm_tokens: int = 0

    def add_step(self, step: ProcessingStep) -> None:
        """Add a processing step."""
        self.steps.append(step)

    def mark_degraded(self, component_name: str) -> None:
        """Mark the pipeline as degraded due to component failure."""
        self.degraded = True
        self.failed_components.append(component_name)

    @property
    def all_agents_failed(self) -> bool:
        """Check if ALL processing steps failed (deprecated — use all_steps_failed)."""
        return self.all_steps_failed

    @property
    def all_steps_failed(self) -> bool:
        """Check if all processing steps failed."""
        if not self.steps:
            return False
        return all(s.status == "FAILED" for s in self.steps)

    @property
    def any_agent_failed(self) -> bool:
        """Check if any processing step failed."""
        return any(s.status == "FAILED" for s in self.steps)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "claim_id": self.claim_id,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "failed_components": self.failed_components,
            "degraded": self.degraded,
            "all_agents_failed": self.all_agents_failed,
            "total_llm_cost": self.total_llm_cost,
            "total_llm_tokens": self.total_llm_tokens,
        }
