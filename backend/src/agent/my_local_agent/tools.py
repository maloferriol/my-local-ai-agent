from typing import List
from ...tools.models import Tool
from ...tools.registry import ToolRegistry
from ...tools.implementations.weather import get_weather_impl, get_weather_conditions_impl


def create_weather_tools() -> List[Tool]:
    """
    Create weather-related tools.

    Returns:
        List[Tool]: List of weather tools
    """
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


def register_default_tools(registry: ToolRegistry) -> None:
    """
    Register default tools with the provided registry for the agent.

    Args:
        registry: The tool registry to register tools with
    """
    # Register weather tools
    for tool in create_weather_tools():
        registry.register_tool(tool)


def create_configured_agent_registry() -> ToolRegistry:
    """
    Create a fully configured tool registry with default tools for the agent.

    Returns:
        ToolRegistry: Configured registry with default tools
    """
    registry = ToolRegistry()
    register_default_tools(registry)
    return registry
