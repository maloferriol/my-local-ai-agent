"""
Tool registry for managing tools with versioning and execution.

This module provides a centralized registry for managing tools,
including registration, execution, and statistics tracking.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import Tool, ToolStatus

logger = logging.getLogger("tools_logger")


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

    def get_tool_by_function_name(self, function_name: str) -> Optional[Tool]:
        """Get a tool by its function name."""
        for tool in self.tools.values():
            if tool.function.__name__ == function_name:
                return tool
        return None

    def execute_tool(self, name: str, *args, **kwargs) -> Any:
        """Execute a tool by name."""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found in registry")

        if tool.status == ToolStatus.DISABLED:
            raise ValueError(f"Tool '{name}' is disabled")

        return tool.execute(*args, **kwargs)

    def execute_tool_by_function_name(self, function_name: str, *args, **kwargs) -> Any:
        """Execute a tool by function name."""
        tool = self.get_tool_by_function_name(function_name)
        if not tool:
            raise ValueError(
                f"Tool with function '{function_name}' not found in registry"
            )

        if tool.status == ToolStatus.DISABLED:
            raise ValueError(f"Tool with function '{function_name}' is disabled")

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
