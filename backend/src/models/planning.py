"""
Planning models for multi-step task execution.

This module provides models for agent planning and execution tracking,
enabling complex task decomposition and dependency management.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid


class PlanStatus(Enum):
    """Status of a plan or plan step."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """Represents a single step in an agent plan."""

    id: str
    title: str
    description: str
    status: PlanStatus = PlanStatus.PENDING
    dependencies: Set[str] = field(default_factory=set)

    # Execution details
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    estimated_duration_ms: Optional[int] = None
    actual_duration_ms: Optional[int] = None

    # Results and context
    output: Optional[str] = None
    error_message: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    priority: int = 0  # Higher numbers = higher priority
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        """Initialize step with UUID if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())

    def can_execute(self, completed_steps: Set[str]) -> bool:
        """Check if this step can be executed based on dependencies."""
        return self.dependencies.issubset(completed_steps)

    def start_execution(self) -> None:
        """Mark step as in progress and record start time."""
        self.status = PlanStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete_execution(self, output: Optional[str] = None) -> None:
        """Mark step as completed and record completion time."""
        self.status = PlanStatus.COMPLETED
        self.end_time = datetime.now()
        self.output = output

        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.actual_duration_ms = int(duration.total_seconds() * 1000)

    def fail_execution(self, error_message: str) -> None:
        """Mark step as failed with error message."""
        self.status = PlanStatus.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message
        self.retry_count += 1

        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.actual_duration_ms = int(duration.total_seconds() * 1000)

    def should_retry(self) -> bool:
        """Check if this step should be retried."""
        return self.status == PlanStatus.FAILED and self.retry_count < self.max_retries

    def reset_for_retry(self) -> None:
        """Reset step state for retry."""
        self.status = PlanStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.actual_duration_ms = None
        self.error_message = None

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """Set a specific metadata value."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary format."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "dependencies": list(self.dependencies),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "estimated_duration_ms": self.estimated_duration_ms,
            "actual_duration_ms": self.actual_duration_ms,
            "output": self.output,
            "error_message": self.error_message,
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "metadata": self.metadata,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }


@dataclass
class AgentPlan:
    """Represents a complete multi-step execution plan."""

    id: str
    title: str
    description: str
    steps: List[PlanStep] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING

    # Execution tracking
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Configuration
    max_parallel_steps: int = 1
    auto_retry_failed_steps: bool = True

    # Results
    final_output: Optional[str] = None
    success_rate: float = 0.0

    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None

    def __post_init__(self):
        """Initialize plan with UUID and creation time if not provided."""
        if not self.id:
            self.id = str(uuid.uuid4())

        if self.created_at is None:
            self.created_at = datetime.now()

    def add_step(self, step: PlanStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)

    def add_dependency(self, step_id: str, depends_on: str) -> bool:
        """Add a dependency between steps."""
        step = self.get_step(step_id)
        if step and depends_on != step_id:  # Prevent self-dependency
            step.dependencies.add(depends_on)
            return True
        return False

    def get_step(self, step_id: str) -> Optional[PlanStep]:
        """Get a step by ID."""
        return next((step for step in self.steps if step.id == step_id), None)

    def get_executable_steps(self) -> List[PlanStep]:
        """Get steps that can be executed now."""
        completed_step_ids = {
            step.id for step in self.steps if step.status == PlanStatus.COMPLETED
        }

        return [
            step
            for step in self.steps
            if step.status == PlanStatus.PENDING
            and step.can_execute(completed_step_ids)
        ]

    def get_next_steps(self, max_steps: Optional[int] = None) -> List[PlanStep]:
        """Get the next steps to execute, respecting parallel limits."""
        executable_steps = self.get_executable_steps()

        # Sort by priority (higher first)
        executable_steps.sort(key=lambda x: x.priority, reverse=True)

        limit = min(max_steps or self.max_parallel_steps, self.max_parallel_steps)

        return executable_steps[:limit]

    def get_failed_steps(self) -> List[PlanStep]:
        """Get steps that have failed."""
        return [step for step in self.steps if step.status == PlanStatus.FAILED]

    def get_retry_candidates(self) -> List[PlanStep]:
        """Get failed steps that can be retried."""
        return [step for step in self.get_failed_steps() if step.should_retry()]

    def start_execution(self) -> None:
        """Start plan execution."""
        self.status = PlanStatus.IN_PROGRESS
        self.started_at = datetime.now()

    def complete_execution(self, final_output: Optional[str] = None) -> None:
        """Complete plan execution."""
        self.status = PlanStatus.COMPLETED
        self.completed_at = datetime.now()
        self.final_output = final_output
        self._calculate_success_rate()

    def fail_execution(self) -> None:
        """Fail plan execution."""
        self.status = PlanStatus.FAILED
        self.completed_at = datetime.now()
        self._calculate_success_rate()

    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(
            step.status in (PlanStatus.COMPLETED, PlanStatus.SKIPPED)
            for step in self.steps
        )

    def has_failed_steps(self) -> bool:
        """Check if any steps have failed."""
        return any(step.status == PlanStatus.FAILED for step in self.steps)

    def _calculate_success_rate(self) -> None:
        """Calculate the success rate of completed steps."""
        if not self.steps:
            self.success_rate = 0.0
            return

        completed_count = sum(
            1 for step in self.steps if step.status == PlanStatus.COMPLETED
        )

        self.success_rate = completed_count / len(self.steps)

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of plan execution."""
        status_counts = {}
        for status in PlanStatus:
            status_counts[status.value] = sum(
                1 for step in self.steps if step.status == status
            )

        total_estimated_ms = sum(step.estimated_duration_ms or 0 for step in self.steps)

        total_actual_ms = sum(
            step.actual_duration_ms or 0
            for step in self.steps
            if step.actual_duration_ms is not None
        )

        return {
            "plan_id": self.id,
            "title": self.title,
            "status": self.status.value,
            "total_steps": len(self.steps),
            "status_counts": status_counts,
            "success_rate": self.success_rate,
            "total_estimated_duration_ms": total_estimated_ms,
            "total_actual_duration_ms": total_actual_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
        }

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get a specific metadata value."""
        if self.metadata is None:
            return default
        return self.metadata.get(key, default)

    def set_metadata_value(self, key: str, value: Any) -> None:
        """Set a specific metadata value."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert plan to dictionary format."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "max_parallel_steps": self.max_parallel_steps,
            "auto_retry_failed_steps": self.auto_retry_failed_steps,
            "final_output": self.final_output,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "conversation_id": self.conversation_id,
        }
