"""
Backward compatibility layer for tools.

This module provides compatibility functions that maintain the old API
while using the new tool system underneath.
"""

from typing import Optional
from .registry import ToolRegistry
from ..agent.my_local_agent.tools import create_configured_agent_registry

# Lazy initialization of the configured registry
_configured_registry: Optional[ToolRegistry] = None


def get_configured_registry() -> ToolRegistry:
    """
    Get or create the configured tool registry with all default tools.

    This uses lazy initialization to avoid side effects during imports.

    Returns:
        ToolRegistry: Configured registry with default tools
    """
    global _configured_registry
    if _configured_registry is None:
        _configured_registry = create_configured_agent_registry()
    return _configured_registry


def get_weather(city: str) -> str:
    """
    Get the current temperature for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current temperature
    """
    registry = get_configured_registry()
    return registry.execute_tool("get_weather", city)


def get_weather_conditions(city: str) -> str:
    """
    Get the weather conditions for a city.

    Args:
        city (str): The name of the city

    Returns:
        str: The current weather conditions
    """
    registry = get_configured_registry()
    return registry.execute_tool("get_weather_conditions", city)
