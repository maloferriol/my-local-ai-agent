import random
import logging
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace

# Get your logger instance for this module
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


class ToolRegistry:
    """Registry for managing tools with versioning."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.tool_categories: Dict[str, List[str]] = {}

    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self.tools[tool.name] = tool

        # Update category index
        if tool.category not in self.tool_categories:
            self.tool_categories[tool.category] = []
        if tool.name not in self.tool_categories[tool.category]:
            self.tool_categories[tool.category].append(tool.name)

        logger.info(f"Registered tool: {tool.name} v{tool.current_version}")

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")

        if tool.status == ToolStatus.DISABLED:
            raise ValueError(f"Tool '{name}' is disabled")

        return tool.execute(*args, **kwargs)

    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get all tools in a specific category."""
        return [
            tool
            for tool in self.tools.values()
            if tool.category == category and tool.status != ToolStatus.DISABLED
        ]

    def get_active_tools(self) -> List[Tool]:
        """Get all active tools."""
        return [
            tool for tool in self.tools.values() if tool.status == ToolStatus.ACTIVE
        ]

    def get_tool_stats(self) -> Dict[str, Any]:
        """Get statistics about registered tools."""
        total_tools = len(self.tools)
        active_tools = len(self.get_active_tools())
        total_calls = sum(tool.call_count for tool in self.tools.values())

        categories_stats = {}
        for category, tool_names in self.tool_categories.items():
            category_tools = [self.tools[name] for name in tool_names]
            categories_stats[category] = {
                "tool_count": len(category_tools),
                "total_calls": sum(tool.call_count for tool in category_tools),
                "average_execution_time_ms": (
                    sum(tool.average_execution_time_ms for tool in category_tools)
                    / len(category_tools)
                    if category_tools
                    else 0
                ),
            }

        return {
            "total_tools": total_tools,
            "active_tools": active_tools,
            "total_calls": total_calls,
            "categories": categories_stats,
            "last_updated": datetime.now().isoformat(),
        }


# Global tool registry
tool_registry = ToolRegistry()


def _get_weather_impl(city: str) -> str:
    """
    Implementation for getting the current temperature for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current temperature
    """
    # Get the current span from the context
    current_span = trace.get_current_span()

    # Add attributes to the span
    current_span.set_attribute("input.city", city)

    temperatures = list(range(-10, 35))
    temp = random.choice(temperatures)

    return f"The temperature in {city} is {temp}°C"


def _get_weather_conditions_impl(city: str) -> str:
    """
    Implementation for getting the weather conditions for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current weather conditions
    """
    # Get the current span from the context
    current_span = trace.get_current_span()

    # Add attributes to the span
    current_span.set_attribute("input.city", city)

    conditions = ["sunny", "cloudy", "rainy", "snowy", "foggy"]
    return random.choice(conditions)


# Register tools in the registry
weather_tool = Tool(
    name="get_weather",
    description="Get the current temperature for a city",
    function=_get_weather_impl,
    category="weather",
    tags=["weather", "temperature", "city"],
    author="LocalAgent Team",
    current_version="1.0.0",
)

weather_conditions_tool = Tool(
    name="get_weather_conditions",
    description="Get the weather conditions for a city",
    function=_get_weather_conditions_impl,
    category="weather",
    tags=["weather", "conditions", "city"],
    author="LocalAgent Team",
    current_version="1.0.0",
)

# Register the tools
tool_registry.register_tool(weather_tool)
tool_registry.register_tool(weather_conditions_tool)


# Backward compatibility functions that use the registry
def get_weather(city: str) -> str:
    """
    Get the current temperature for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current temperature
    """
    return tool_registry.execute_tool("get_weather", city)


def get_weather_conditions(city: str) -> str:
    """
    Get the weather conditions for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current weather conditions
    """
    return tool_registry.execute_tool("get_weather_conditions", city)
