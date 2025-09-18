from typing import List
from ...tools.models import Tool
from ...tools.registry import ToolRegistry
from ...tools.implementations.weather import (
    get_weather_impl,
    get_weather_conditions_impl,
)


class MyLocalAgentToolRegistry:
    """Tool registry manager for MyLocalAgent with a clean per-agent pattern."""

    @staticmethod
    def get_available_tools() -> List[Tool]:
        """Get all available tools for this agent."""
        return [
            Tool(
                name="get_weather",
                description="Get the current temperature for a city",
                function=get_weather_impl,
                category="weather",
                tags=["weather", "temperature", "city"],
                author="LocalAgent Team",
                current_version="1.0.0",
            ),
            Tool(
                name="get_weather_conditions",
                description="Get the weather conditions for a city",
                function=get_weather_conditions_impl,
                category="weather",
                tags=["weather", "conditions", "city"],
                author="LocalAgent Team",
                current_version="1.0.0",
            ),
        ]

    @classmethod
    def create_registry(cls) -> ToolRegistry:
        """Create a configured tool registry for this agent."""
        registry = ToolRegistry()
        for tool in cls.get_available_tools():
            registry.register_tool(tool)
        return registry
