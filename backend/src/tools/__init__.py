"""
Tools package initialization.

This package provides a comprehensive tool management system with:
- Tool models with versioning and metadata
- Tool registry for centralized management
- Pre-built tool implementations
- Enhanced tool management with versioning and statistics
"""

from .models import Tool, ToolStatus, ToolVersion
from .registry import ToolRegistry
from .implementations.weather import get_weather_impl, get_weather_conditions_impl

# Create a global registry instance (empty by default)
tool_registry = ToolRegistry()

__all__ = [
    # Core models and registry
    "Tool",
    "ToolStatus",
    "ToolVersion",
    "ToolRegistry",
    "tool_registry",
    # Implementation functions
    "get_weather_impl",
    "get_weather_conditions_impl",
]
