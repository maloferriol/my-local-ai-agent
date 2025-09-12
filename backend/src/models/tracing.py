"""
Execution tracing models for detailed performance analysis and debugging.

This module provides models for comprehensive tracing of agent executions,
integrating with OpenTelemetry for distributed tracing capabilities.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid


class SpanStatus(Enum):
    """Status of an execution span."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class SpanKind(Enum):
    """Type of span in distributed tracing."""

    INTERNAL = "internal"
    SERVER = "server"
    CLIENT = "client"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class ExecutionSpan:
    """Represents a single operation span in an execution trace."""

    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""

    # Timing information
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Span classification
    status: SpanStatus = SpanStatus.UNSET
    kind: SpanKind = SpanKind.INTERNAL

    # Operation details
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    # Resource usage
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None

    # Custom metadata
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize span with UUIDs if not provided."""
        if not self.span_id:
            self.span_id = str(uuid.uuid4())
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())

    def start(self) -> None:
        """Start the span execution."""
        self.start_time = datetime.now()

    def end(self, status: SpanStatus = SpanStatus.OK) -> None:
        """End the span execution."""
        self.end_time = datetime.now()
        self.status = status

        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.duration_ms = int(duration.total_seconds() * 1000)

    def set_error(self, error_message: str) -> None:
        """Mark span as error with message."""
        self.status = SpanStatus.ERROR
        self.error_message = error_message

        # Add error event
        self.add_event(
            "error", {"message": error_message, "timestamp": datetime.now().isoformat()}
        )

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        event = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "attributes": attributes or {},
        }
        self.events.append(event)

    def get_child_span(self, operation_name: str) -> "ExecutionSpan":
        """Create a child span."""
        return ExecutionSpan(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=self.span_id,
            operation_name=operation_name,
        )

    def is_root_span(self) -> bool:
        """Check if this is a root span."""
        return self.parent_span_id is None

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
        """Convert span to dictionary format."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "operation_name": self.operation_name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "status": self.status.value,
            "kind": self.kind.value,
            "attributes": self.attributes,
            "events": self.events,
            "error_message": self.error_message,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "metadata": self.metadata,
        }


@dataclass
class ExecutionTrace:
    """Represents a complete execution trace with multiple spans."""

    trace_id: str
    name: str
    description: str = ""
    spans: List[ExecutionSpan] = field(default_factory=list)

    # Trace timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration_ms: Optional[int] = None

    # Trace status
    success: bool = False
    error_count: int = 0

    # Context information
    conversation_id: Optional[str] = None
    plan_id: Optional[str] = None
    user_id: Optional[str] = None

    # Performance metrics
    total_memory_usage_mb: float = 0.0
    peak_memory_usage_mb: float = 0.0
    average_cpu_usage_percent: float = 0.0

    # Custom metadata
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize trace with UUID if not provided."""
        if not self.trace_id:
            self.trace_id = str(uuid.uuid4())

    def start(self) -> None:
        """Start the trace execution."""
        self.start_time = datetime.now()

    def end(self) -> None:
        """End the trace execution and calculate metrics."""
        self.end_time = datetime.now()

        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
            self.total_duration_ms = int(duration.total_seconds() * 1000)

        self._calculate_metrics()
        self.success = self.error_count == 0

    def add_span(self, span: ExecutionSpan) -> None:
        """Add a span to the trace."""
        # Ensure span belongs to this trace
        span.trace_id = self.trace_id
        self.spans.append(span)

    def create_root_span(self, operation_name: str) -> ExecutionSpan:
        """Create and add a root span."""
        span = ExecutionSpan(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            operation_name=operation_name,
            kind=SpanKind.SERVER,
        )
        self.add_span(span)
        return span

    def create_child_span(
        self, parent_span_id: str, operation_name: str
    ) -> ExecutionSpan:
        """Create and add a child span."""
        span = ExecutionSpan(
            trace_id=self.trace_id,
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            operation_name=operation_name,
        )
        self.add_span(span)
        return span

    def get_span(self, span_id: str) -> Optional[ExecutionSpan]:
        """Get a span by ID."""
        return next((span for span in self.spans if span.span_id == span_id), None)

    def get_root_spans(self) -> List[ExecutionSpan]:
        """Get all root spans in the trace."""
        return [span for span in self.spans if span.is_root_span()]

    def get_child_spans(self, parent_span_id: str) -> List[ExecutionSpan]:
        """Get all child spans of a parent."""
        return [span for span in self.spans if span.parent_span_id == parent_span_id]

    def get_error_spans(self) -> List[ExecutionSpan]:
        """Get all spans with errors."""
        return [span for span in self.spans if span.status == SpanStatus.ERROR]

    def _calculate_metrics(self) -> None:
        """Calculate performance metrics from spans."""
        self.error_count = len(self.get_error_spans())

        if not self.spans:
            return

        # Memory metrics
        memory_values = [
            span.memory_usage_mb
            for span in self.spans
            if span.memory_usage_mb is not None
        ]

        if memory_values:
            self.total_memory_usage_mb = sum(memory_values)
            self.peak_memory_usage_mb = max(memory_values)

        # CPU metrics
        cpu_values = [
            span.cpu_usage_percent
            for span in self.spans
            if span.cpu_usage_percent is not None
        ]

        if cpu_values:
            self.average_cpu_usage_percent = sum(cpu_values) / len(cpu_values)

    def get_trace_summary(self) -> Dict[str, Any]:
        """Get a summary of trace execution."""
        successful_spans = sum(1 for span in self.spans if span.status == SpanStatus.OK)

        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "success": self.success,
            "total_spans": len(self.spans),
            "successful_spans": successful_spans,
            "error_count": self.error_count,
            "total_duration_ms": self.total_duration_ms,
            "total_memory_usage_mb": self.total_memory_usage_mb,
            "peak_memory_usage_mb": self.peak_memory_usage_mb,
            "average_cpu_usage_percent": self.average_cpu_usage_percent,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "conversation_id": self.conversation_id,
            "plan_id": self.plan_id,
        }

    def get_span_tree(self) -> Dict[str, Any]:
        """Get hierarchical representation of spans."""

        def build_tree(parent_id: Optional[str] = None) -> List[Dict[str, Any]]:
            children = []
            for span in self.spans:
                if span.parent_span_id == parent_id:
                    span_dict = span.to_dict()
                    span_dict["children"] = build_tree(span.span_id)
                    children.append(span_dict)
            return children

        return {"trace_id": self.trace_id, "name": self.name, "spans": build_tree()}

    def get_critical_path(self) -> List[ExecutionSpan]:
        """Get the critical path (longest duration chain) through the trace."""
        if not self.spans:
            return []

        # Simple implementation: find the chain with maximum total duration
        # This is a simplified version - a full implementation would use
        # proper critical path analysis algorithms

        root_spans = self.get_root_spans()
        if not root_spans:
            return []

        def get_path_duration(
            span: ExecutionSpan, visited: Set[str]
        ) -> tuple[int, List[ExecutionSpan]]:
            if span.span_id in visited:
                return 0, []

            visited.add(span.span_id)
            span_duration = span.duration_ms or 0

            children = self.get_child_spans(span.span_id)
            if not children:
                return span_duration, [span]

            max_child_duration = 0
            max_child_path = []

            for child in children:
                child_duration, child_path = get_path_duration(child, visited.copy())
                if child_duration > max_child_duration:
                    max_child_duration = child_duration
                    max_child_path = child_path

            return span_duration + max_child_duration, [span] + max_child_path

        max_duration = 0
        critical_path = []

        for root in root_spans:
            duration, path = get_path_duration(root, set())
            if duration > max_duration:
                max_duration = duration
                critical_path = path

        return critical_path

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
        """Convert trace to dictionary format."""
        return {
            "trace_id": self.trace_id,
            "name": self.name,
            "description": self.description,
            "spans": [span.to_dict() for span in self.spans],
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "success": self.success,
            "error_count": self.error_count,
            "conversation_id": self.conversation_id,
            "plan_id": self.plan_id,
            "user_id": self.user_id,
            "total_memory_usage_mb": self.total_memory_usage_mb,
            "peak_memory_usage_mb": self.peak_memory_usage_mb,
            "average_cpu_usage_percent": self.average_cpu_usage_percent,
            "metadata": self.metadata,
        }
