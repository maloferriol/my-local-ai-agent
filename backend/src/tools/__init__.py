"""
Tools package initialization.

This package provides a comprehensive tool management system with:
- Tool models with versioning and metadata
- Tool registry for centralized management
- Pre-built tool implementations
- Backward compatibility with existing code
"""

from .models import Tool, ToolStatus, ToolVersion
from .registry import ToolRegistry
from .implementations.weather import get_weather_impl, get_weather_conditions_impl
from .compatibility import get_weather, get_weather_conditions
from .builders import create_configured_registry, register_default_tools

# Create a global registry instance (empty by default)
tool_registry = ToolRegistry()

__all__ = [
    # Core models and registry
    "Tool",
    "ToolStatus",
    "ToolVersion",
    "ToolRegistry",
    "tool_registry",
    # Builder functions
    "create_configured_registry",
    "register_default_tools",
    # Backward compatibility functions
    "get_weather",
    "get_weather_conditions",
    # Implementation functions
    "get_weather_impl",
    "get_weather_conditions_impl",
]
