"""
Unit tests for tools/registry.py - Tool registry management.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from src.tools.registry import ToolRegistry
from src.tools.models import Tool, ToolStatus


@pytest.fixture
def sample_tool():
    """Create a sample tool for testing."""

    def sample_function(x: int, y: int) -> int:
        return x + y

    tool = Tool(
        name="sample_tool",
        description="A sample tool for testing",
        function=sample_function,
        category="math",
        tags=["arithmetic", "basic"],
        status=ToolStatus.ACTIVE,
        author="test_author",
    )
    return tool


@pytest.fixture
def disabled_tool():
    """Create a disabled tool for testing."""

    def disabled_function() -> str:
        return "disabled"

    tool = Tool(
        name="disabled_tool",
        description="A disabled tool for testing",
        function=disabled_function,
        category="utility",
        status=ToolStatus.DISABLED,
    )
    return tool


@pytest.fixture
def experimental_tool():
    """Create an experimental tool for testing."""

    def experimental_function() -> str:
        return "experimental"

    tool = Tool(
        name="experimental_tool",
        description="An experimental tool for testing",
        function=experimental_function,
        category="experimental",
        status=ToolStatus.EXPERIMENTAL,
    )
    return tool


@pytest.fixture
def registry():
    """Create a fresh tool registry for testing."""
    return ToolRegistry()


class TestToolRegistry:
    """Test ToolRegistry functionality."""

    def test_init(self):
        """Test ToolRegistry initialization."""
        registry = ToolRegistry()
        assert registry.tools == {}
        assert registry.tool_categories == {}

    def test_register_tool(self, registry, sample_tool):
        """Test registering a tool."""
        registry.register_tool(sample_tool)

        assert sample_tool.name in registry.tools
        assert registry.tools[sample_tool.name] == sample_tool
        assert sample_tool.category in registry.tool_categories
        assert sample_tool.name in registry.tool_categories[sample_tool.category]

    def test_register_multiple_tools_same_category(self, registry, sample_tool):
        """Test registering multiple tools in the same category."""

        # Create another tool in the same category
        def another_function(x: int) -> int:
            return x * 2

        another_tool = Tool(
            name="another_tool",
            description="Another tool",
            function=another_function,
            category="math",  # Same category as sample_tool
        )

        registry.register_tool(sample_tool)
        registry.register_tool(another_tool)

        assert len(registry.tool_categories["math"]) == 2
        assert "sample_tool" in registry.tool_categories["math"]
        assert "another_tool" in registry.tool_categories["math"]

    def test_register_tool_prevents_duplicates_in_category(self, registry, sample_tool):
        """Test that registering the same tool twice doesn't create duplicates in category."""
        registry.register_tool(sample_tool)
        registry.register_tool(sample_tool)  # Register again

        assert len(registry.tool_categories[sample_tool.category]) == 1

    def test_get_tool_exists(self, registry, sample_tool):
        """Test getting an existing tool."""
        registry.register_tool(sample_tool)
        result = registry.get_tool(sample_tool.name)
        assert result == sample_tool

    def test_get_tool_not_exists(self, registry):
        """Test getting a non-existent tool returns None."""
        result = registry.get_tool("nonexistent_tool")
        assert result is None

    def test_get_tool_by_function_name_exists(self, registry, sample_tool):
        """Test getting a tool by its function name when it exists."""
        registry.register_tool(sample_tool)
        result = registry.get_tool_by_function_name("sample_function")
        assert result == sample_tool

    def test_get_tool_by_function_name_not_exists(self, registry, sample_tool):
        """Test getting a tool by function name when it doesn't exist."""
        registry.register_tool(sample_tool)
        result = registry.get_tool_by_function_name("nonexistent_function")
        assert result is None

    def test_execute_tool_success(self, registry, sample_tool):
        """Test successful tool execution."""
        registry.register_tool(sample_tool)
        result = registry.execute_tool("sample_tool", 3, 5)
        assert result == 8

    def test_execute_tool_not_found(self, registry):
        """Test executing a non-existent tool raises ValueError."""
        with pytest.raises(
            ValueError, match="Tool 'nonexistent_tool' not found in registry"
        ):
            registry.execute_tool("nonexistent_tool")

    def test_execute_tool_disabled(self, registry, disabled_tool):
        """Test executing a disabled tool raises ValueError."""
        registry.register_tool(disabled_tool)
        with pytest.raises(ValueError, match="Tool 'disabled_tool' is disabled"):
            registry.execute_tool("disabled_tool")

    def test_execute_tool_by_function_name_success(self, registry, sample_tool):
        """Test successful tool execution by function name."""
        registry.register_tool(sample_tool)
        result = registry.execute_tool_by_function_name("sample_function", 4, 6)
        assert result == 10

    def test_execute_tool_by_function_name_not_found(self, registry):
        """Test executing by function name when tool not found raises ValueError."""
        with pytest.raises(
            ValueError,
            match="Tool with function 'nonexistent_function' not found in registry",
        ):
            registry.execute_tool_by_function_name("nonexistent_function")

    def test_execute_tool_by_function_name_disabled(self, registry, disabled_tool):
        """Test executing disabled tool by function name raises ValueError."""
        registry.register_tool(disabled_tool)
        with pytest.raises(
            ValueError, match="Tool with function 'disabled_function' is disabled"
        ):
            registry.execute_tool_by_function_name("disabled_function")

    def test_get_tools_by_category(
        self, registry, sample_tool, experimental_tool, disabled_tool
    ):
        """Test getting tools by category."""

        # Create another math tool
        def multiply_function(x: int, y: int) -> int:
            return x * y

        math_tool = Tool(
            name="multiply_tool",
            description="Multiplication tool",
            function=multiply_function,
            category="math",
            status=ToolStatus.ACTIVE,
        )

        registry.register_tool(sample_tool)  # math category, active
        registry.register_tool(math_tool)  # math category, active
        registry.register_tool(experimental_tool)  # experimental category, experimental
        registry.register_tool(disabled_tool)  # utility category, disabled

        # Get math tools (should exclude disabled ones)
        math_tools = registry.get_tools_by_category("math")
        assert len(math_tools) == 2
        assert sample_tool in math_tools
        assert math_tool in math_tools

        # Get experimental tools
        experimental_tools = registry.get_tools_by_category("experimental")
        assert len(experimental_tools) == 1
        assert experimental_tool in experimental_tools

        # Get utility tools (should exclude disabled)
        utility_tools = registry.get_tools_by_category("utility")
        assert len(utility_tools) == 0  # disabled_tool should be excluded

        # Get non-existent category
        nonexistent_tools = registry.get_tools_by_category("nonexistent")
        assert len(nonexistent_tools) == 0

    def test_get_active_tools(
        self, registry, sample_tool, experimental_tool, disabled_tool
    ):
        """Test getting only active tools."""
        registry.register_tool(sample_tool)  # ACTIVE
        registry.register_tool(experimental_tool)  # EXPERIMENTAL
        registry.register_tool(disabled_tool)  # DISABLED

        active_tools = registry.get_active_tools()
        assert len(active_tools) == 1
        assert sample_tool in active_tools
        assert experimental_tool not in active_tools
        assert disabled_tool not in active_tools

    @patch("src.tools.registry.datetime")
    def test_get_tool_stats(
        self, mock_datetime, registry, sample_tool, experimental_tool, disabled_tool
    ):
        """Test getting comprehensive tool statistics."""
        # Mock datetime.now() to return a fixed time
        fixed_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time

        # Set up tools with different properties
        sample_tool.call_count = 5
        sample_tool.average_execution_time_ms = 100.0

        experimental_tool.call_count = 3
        experimental_tool.average_execution_time_ms = 50.0

        disabled_tool.call_count = 2
        disabled_tool.average_execution_time_ms = 200.0

        registry.register_tool(sample_tool)  # math category
        registry.register_tool(experimental_tool)  # experimental category
        registry.register_tool(disabled_tool)  # utility category

        stats = registry.get_tool_stats()

        # Check overall stats
        assert stats["total_tools"] == 3
        assert stats["active_tools"] == 1  # Only sample_tool is ACTIVE
        assert stats["total_calls"] == 10  # 5 + 3 + 2
        assert stats["last_updated"] == fixed_time.isoformat()

        # Check category stats
        assert "math" in stats["categories"]
        assert "experimental" in stats["categories"]
        assert "utility" in stats["categories"]

        # Math category (1 tool)
        math_stats = stats["categories"]["math"]
        assert math_stats["tool_count"] == 1
        assert math_stats["total_calls"] == 5
        assert math_stats["average_execution_time_ms"] == 100.0

        # Experimental category (1 tool)
        experimental_stats = stats["categories"]["experimental"]
        assert experimental_stats["tool_count"] == 1
        assert experimental_stats["total_calls"] == 3
        assert experimental_stats["average_execution_time_ms"] == 50.0

        # Utility category (1 tool)
        utility_stats = stats["categories"]["utility"]
        assert utility_stats["tool_count"] == 1
        assert utility_stats["total_calls"] == 2
        assert utility_stats["average_execution_time_ms"] == 200.0

    @patch("src.tools.registry.datetime")
    def test_get_tool_stats_empty_category(self, mock_datetime, registry):
        """Test getting tool statistics when a category has no tools."""
        # Mock datetime.now() to return a fixed time
        fixed_time = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = fixed_time

        # Register a tool and then simulate an empty category
        def test_function() -> str:
            return "test"

        tool = Tool(
            name="test_tool",
            description="Test tool",
            function=test_function,
            category="test_category",
        )

        registry.register_tool(tool)

        # Manually add an empty category to simulate edge case
        registry.tool_categories["empty_category"] = []

        stats = registry.get_tool_stats()

        # Check that empty category has correct stats
        assert "empty_category" in stats["categories"]
        empty_stats = stats["categories"]["empty_category"]
        assert empty_stats["tool_count"] == 0
        assert empty_stats["total_calls"] == 0
        assert empty_stats["average_execution_time_ms"] == 0

    def test_get_tool_stats_no_tools(self, registry):
        """Test getting tool statistics when no tools are registered."""
        stats = registry.get_tool_stats()

        assert stats["total_tools"] == 0
        assert stats["active_tools"] == 0
        assert stats["total_calls"] == 0
        assert stats["categories"] == {}
        assert "last_updated" in stats

    @patch("src.tools.registry.logger")
    def test_register_tool_logging(self, mock_logger, registry, sample_tool):
        """Test that tool registration is logged."""
        registry.register_tool(sample_tool)

        mock_logger.info.assert_called_once_with(
            f"Registered tool: {sample_tool.name} v{sample_tool.current_version}"
        )

    def test_integration_multiple_operations(self, registry):
        """Test integration scenario with multiple operations."""

        # Create multiple tools
        def add_func(x: int, y: int) -> int:
            return x + y

        def multiply_func(x: int, y: int) -> int:
            return x * y

        def concat_func(a: str, b: str) -> str:
            return a + b

        add_tool = Tool(
            name="add_tool",
            description="Addition tool",
            function=add_func,
            category="math",
            status=ToolStatus.ACTIVE,
        )

        multiply_tool = Tool(
            name="multiply_tool",
            description="Multiplication tool",
            function=multiply_func,
            category="math",
            status=ToolStatus.EXPERIMENTAL,
        )

        concat_tool = Tool(
            name="concat_tool",
            description="String concatenation tool",
            function=concat_func,
            category="string",
            status=ToolStatus.DISABLED,
        )

        # Register tools
        registry.register_tool(add_tool)
        registry.register_tool(multiply_tool)
        registry.register_tool(concat_tool)

        # Test various operations
        assert len(registry.tools) == 3
        assert len(registry.tool_categories) == 2  # math, string

        # Execute active tool
        result = registry.execute_tool("add_tool", 3, 7)
        assert result == 10

        # Get tools by category
        math_tools = registry.get_tools_by_category("math")
        assert len(math_tools) == 2  # add_tool and multiply_tool (not disabled)

        # Get active tools only
        active_tools = registry.get_active_tools()
        assert len(active_tools) == 1
        assert add_tool in active_tools

        # Test error scenarios
        with pytest.raises(ValueError):
            registry.execute_tool("concat_tool")  # disabled

        with pytest.raises(ValueError):
            registry.execute_tool("nonexistent_tool")  # doesn't exist
