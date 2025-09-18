"""
Tool models for the agent system.

This module provides models for tools with metadata, versioning, and execution tracking.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace

logger = logging.getLogger("tools_logger")
tracer = trace.get_tracer(__name__)


class ToolStatus(Enum):
    """Status of a tool."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    DISABLED = "disabled"
    EXPERIMENTAL = "experimental"


@dataclass
class ToolVersion:
    """Represents a version of a tool."""

    version: str
    release_date: datetime
    changes: List[str] = field(default_factory=list)
    breaking_changes: bool = False
    is_stable: bool = True


@dataclass
class Tool:
    """Represents a tool with metadata and versioning."""

    name: str
    description: str
    function: Callable

    # Versioning
    current_version: str = "1.0.0"
    versions: Dict[str, ToolVersion] = field(default_factory=dict)

    # Classification
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    status: ToolStatus = ToolStatus.ACTIVE

    # Usage tracking
    call_count: int = 0
    last_used: Optional[datetime] = None
    average_execution_time_ms: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    author: Optional[str] = None
    documentation_url: Optional[str] = None

    # Configuration
    max_execution_time_ms: int = 30000  # 30 seconds default
    retry_count: int = 3

    # Tool ID
    tool_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        """Initialize tool with default version."""
        if not self.versions:
            self.versions[self.current_version] = ToolVersion(
                version=self.current_version,
                release_date=datetime.now(),
                changes=["Initial version"],
                is_stable=True,
            )

    def add_version(
        self,
        version: str,
        changes: List[str],
        breaking_changes: bool = False,
        is_stable: bool = True,
    ) -> None:
        """Add a new version of the tool."""
        tool_version = ToolVersion(
            version=version,
            release_date=datetime.now(),
            changes=changes,
            breaking_changes=breaking_changes,
            is_stable=is_stable,
        )
        self.versions[version] = tool_version
        self.current_version = version
        self.updated_at = datetime.now()

    def get_version_info(self, version: Optional[str] = None) -> Optional[ToolVersion]:
        """Get information about a specific version."""
        return self.versions.get(version or self.current_version)

    def execute(self, *args, **kwargs) -> Any:
        """Execute the tool function with tracking."""
        start_time = datetime.now()

        try:
            # Update usage tracking
            self.call_count += 1
            self.last_used = start_time

            with tracer.start_as_current_span(
                name=f"tool_{self.name}",
                attributes={
                    SpanAttributes.OPENINFERENCE_SPAN_KIND: "TOOL",
                    "tool.name": self.name,
                    "tool.version": self.current_version,
                    "tool.category": self.category,
                    "tool.call_count": self.call_count,
                },
            ) as span:

                span.set_attribute("tool.id", self.tool_id)
                span.set_attribute("tool.status", self.status.value)

                # Execute the function
                result = self.function(*args, **kwargs)

                # Update execution time tracking
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds() * 1000

                # Update average execution time
                if self.call_count == 1:
                    self.average_execution_time_ms = execution_time
                else:
                    # Running average
                    self.average_execution_time_ms = (
                        self.average_execution_time_ms * (self.call_count - 1)
                        + execution_time
                    ) / self.call_count

                span.set_attribute("tool.execution_time_ms", execution_time)
                span.set_attribute(
                    "tool.average_execution_time_ms", self.average_execution_time_ms
                )

                logger.info(f"Tool {self.name} executed in {execution_time:.2f}ms")

                return result

        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {str(e)}")
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format."""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "description": self.description,
            "current_version": self.current_version,
            "category": self.category,
            "tags": self.tags,
            "status": self.status.value,
            "call_count": self.call_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "average_execution_time_ms": self.average_execution_time_ms,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "author": self.author,
            "documentation_url": self.documentation_url,
            "max_execution_time_ms": self.max_execution_time_ms,
            "retry_count": self.retry_count,
            "versions": {
                ver: {
                    "version": info.version,
                    "release_date": info.release_date.isoformat(),
                    "changes": info.changes,
                    "breaking_changes": info.breaking_changes,
                    "is_stable": info.is_stable,
                }
                for ver, info in self.versions.items()
            },
        }
