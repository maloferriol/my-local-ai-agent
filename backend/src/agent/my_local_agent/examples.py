"""
Backward compatibility module for tool functions.

This module provides backward compatibility by re-exporting tools
from the new tools package. This allows existing code to continue
working without changes while using the new structured tools system.

DEPRECATED: This module is kept for backward compatibility only.
New code should import directly from src.tools.
"""

# Import everything from the new tools package for backward compatibility
from src.tools import (
    Tool,
    ToolStatus,
    ToolVersion,
    ToolRegistry,
    tool_registry,
    get_weather,
    get_weather_conditions,
    get_weather_impl,
    get_weather_conditions_impl,
)

# Re-export for backward compatibility
__all__ = [
    # Core models and registry
    "Tool",
    "ToolStatus",
    "ToolVersion",
    "ToolRegistry",
    "tool_registry",
    # Backward compatibility functions
    "get_weather",
    "get_weather_conditions",
    # Implementation functions (deprecated access)
    "get_weather_impl",
    "get_weather_conditions_impl",
]
