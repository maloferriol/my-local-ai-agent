"""
Tool Execution Service module for handling tool calls and execution.

This module provides a centralized service for executing tools,
handling tool results, and managing tool-related errors.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List

from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import Status, StatusCode

from src.conversation import ConversationManager
from src.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ToolExecutionService:
    """
    Service for managing tool execution and results.

    Handles tool validation, execution, result formatting,
    and integration with conversation management.
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize the tool execution service.

        Args:
            tool_registry: Registry containing available tools
        """
        self.tool_registry = tool_registry

    async def execute_tools(
        self,
        tool_calls: List[Dict[str, Any]],
        conv_manager: ConversationManager,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes a list of tool calls and yields their results.

        This function uses the ConversationManager to persist tool results.

        Args:
            tool_calls: A list of tool calls received from the model.
            conv_manager: The conversation manager instance.

        Yields:
            A dictionary representing a tool result or an error.
        """
        with tracer.start_as_current_span(
            "tools_execution",
            kind=SpanKind.INTERNAL,
            attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
        ) as outer_span:
            try:
                for tool_call in tool_calls:
                    tool_name = tool_call.get("function", {}).get("name")
                    with tracer.start_as_current_span(
                        name=tool_name,
                        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "TOOL"},
                    ) as tool_span:
                        try:
                            result = await self._execute_single_tool(
                                tool_call, tool_span, conv_manager
                            )

                            # Yield the result to the client
                            yield result

                        except Exception as e:
                            tool_span.record_exception(e)
                            tool_span.set_status(Status(StatusCode.ERROR, str(e)))
                            error_result = self._format_tool_error(tool_name, e)
                            logger.error(f"Tool execution error for '{tool_name}': {e}")
                            yield error_result

            except Exception as e:
                outer_span.record_exception(e)
                outer_span.set_status(Status(StatusCode.ERROR, str(e)))
                error_msg = f"Critical error in tool execution loop: {e}"
                logger.error(error_msg)
                yield {
                    "stage": "error",
                    "response": f"Tool execution system error: {str(e)}",
                }

    async def _execute_single_tool(
        self,
        tool_call: Dict[str, Any],
        tool_span,
        conv_manager: ConversationManager,
    ) -> Dict[str, Any]:
        """
        Execute a single tool call and return the formatted result.

        Args:
            tool_call: The tool call to execute
            tool_span: OpenTelemetry span for tracing
            conv_manager: Conversation manager for persisting results

        Returns:
            Formatted tool result dictionary
        """
        tool_name = tool_call.get("function", {}).get("name")

        if not tool_name:
            logger.warning(f"Tool call missing name: {tool_call}")
            raise ValueError("Tool call missing name")

        tool_span.set_attribute("tool.name", tool_name)

        # Check if tool exists in registry first
        tool = self.tool_registry.get_tool_by_function_name(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found in registry."
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info(f"Found tool in registry: {tool_name}")

        # Enhanced tracing with tool metadata
        tool_span.set_attribute("tool.version", tool.current_version)
        tool_span.set_attribute("tool.category", tool.category)
        tool_span.set_attribute("tool.status", tool.status.value)
        tool_span.set_attribute("tool.call_count", tool.call_count)

        args = tool_call.get("function", {}).get("arguments", {})
        tool_span.set_attribute("tool.arguments", json.dumps(args))

        logger.info(
            f"Executing tool '{tool_name}' v{tool.current_version} with args: {args}"
        )

        # Execute through registry for enhanced tracking
        result = self.tool_registry.execute_tool_by_function_name(tool_name, **args)

        # Add enhanced metrics
        tool_span.set_attribute("tool.result", str(result))
        tool_span.set_attribute(
            "tool.average_execution_time_ms",
            tool.average_execution_time_ms,
        )

        # Save tool result using the conversation manager
        conv_manager.add_tool_message(
            content=str(result),
            tool_name=tool_name,
            model=conv_manager.get_current_conversation().model,
        )

        return {
            "stage": "tool_result",
            "tool": tool_name,
            "args": args,
            "result": result,
        }

    def _format_tool_error(self, tool_name: str, error: Exception) -> Dict[str, Any]:
        """
        Format a tool execution error into a standardized response.

        Args:
            tool_name: Name of the tool that failed
            error: The exception that occurred

        Returns:
            Formatted error response dictionary
        """
        return {
            "stage": "tool_error",
            "tool": tool_name,
            "error": str(error),
        }

    def validate_tool_call(self, tool_call: Dict[str, Any]) -> bool:
        """
        Validate a tool call structure.

        Args:
            tool_call: The tool call to validate

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(tool_call, dict):
            return False

        function = tool_call.get("function")
        if not isinstance(function, dict):
            return False

        if not function.get("name"):
            return False

        # Arguments should be a dict if present
        args = function.get("arguments")
        if args is not None and not isinstance(args, dict):
            return False

        return True

    def get_tool_capabilities(self, model: str) -> List[Dict[str, Any]]:
        """
        Get available tools for a specific model.

        Args:
            model: The model name to get tools for

        Returns:
            List of tool function definitions
        """
        # For now, return all active tools
        # This could be model-specific in the future
        active_tools = self.tool_registry.get_active_tools()
        return [tool.function for tool in active_tools]

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get tool execution statistics.

        Returns:
            Dictionary containing execution statistics
        """
        return self.tool_registry.get_tool_stats()
