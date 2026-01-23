"""
Error Handling utilities for standardized error management and tracing.

This module provides utility functions and classes for consistent
error handling, formatting, and tracing across the application.
"""

import json
import logging
import traceback
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class ErrorCategory(Enum):
    """Categorization of different error types."""

    LLM_COMMUNICATION = "llm_communication"
    TOOL_EXECUTION = "tool_execution"
    CONVERSATION_MANAGEMENT = "conversation_management"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    NETWORK = "network"
    AUTHENTICATION = "authentication"


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """Context information for errors."""

    category: ErrorCategory
    severity: ErrorSeverity
    operation: str
    user_message: str
    technical_details: Optional[str] = None
    suggested_action: Optional[str] = None
    error_code: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ErrorHandler:
    """Centralized error handling and formatting."""

    @staticmethod
    def format_error_response(
        error: Exception,
        context: ErrorContext,
        include_traceback: bool = False,
    ) -> Dict[str, Any]:
        """
        Format an error into a standardized response structure.

        Args:
            error: The exception that occurred
            context: Error context information
            include_traceback: Whether to include technical traceback

        Returns:
            Formatted error response dictionary
        """
        response = {
            "stage": "error",
            "error_type": type(error).__name__,
            "category": context.category.value,
            "severity": context.severity.value,
            "operation": context.operation,
            "message": context.user_message,
            "timestamp": None,  # Could use datetime.now().isoformat() if needed
        }

        if context.error_code:
            response["error_code"] = context.error_code

        if context.suggested_action:
            response["suggested_action"] = context.suggested_action

        if context.technical_details:
            response["technical_details"] = context.technical_details

        if context.metadata:
            response["metadata"] = context.metadata

        if include_traceback:
            response["traceback"] = traceback.format_exception(
                type(error), error, error.__traceback__
            )

        return response

    @staticmethod
    def log_error(
        error: Exception,
        context: ErrorContext,
        span: Optional[Any] = None,
    ) -> None:
        """
        Log an error with appropriate level and tracing.

        Args:
            error: The exception that occurred
            context: Error context information
            span: Optional OpenTelemetry span for tracing
        """
        # Determine log level based on severity
        log_level_map = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }

        log_level = log_level_map.get(context.severity, logging.ERROR)

        # Create log message
        log_msg = (
            f"{context.category.value.upper()} ERROR in {context.operation}: "
            f"{context.user_message}"
        )

        if context.technical_details:
            log_msg += f" | Technical: {context.technical_details}"

        # Log with appropriate level
        logger.log(log_level, log_msg, exc_info=error)

        # Add to OpenTelemetry span if provided
        if span:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute("error.category", context.category.value)
            span.set_attribute("error.severity", context.severity.value)
            span.set_attribute("error.operation", context.operation)

            if context.error_code:
                span.set_attribute("error.code", context.error_code)

    @staticmethod
    def create_llm_error_context(
        operation: str,
        model: str,
        error: Exception,
    ) -> ErrorContext:
        """Create error context for LLM-related errors."""
        return ErrorContext(
            category=ErrorCategory.LLM_COMMUNICATION,
            severity=ErrorSeverity.HIGH,
            operation=operation,
            user_message=f"Communication error with model {model}",
            technical_details=str(error),
            suggested_action="Please try again or contact support if the issue persists",
            metadata={"model": model},
        )

    @staticmethod
    def create_tool_error_context(
        operation: str,
        tool_name: str,
        error: Exception,
    ) -> ErrorContext:
        """Create error context for tool execution errors."""
        return ErrorContext(
            category=ErrorCategory.TOOL_EXECUTION,
            severity=ErrorSeverity.MEDIUM,
            operation=operation,
            user_message=f"Error executing tool '{tool_name}'",
            technical_details=str(error),
            suggested_action="Please check tool parameters and try again",
            metadata={"tool_name": tool_name},
        )

    @staticmethod
    def create_validation_error_context(
        operation: str,
        validation_error: str,
    ) -> ErrorContext:
        """Create error context for validation errors."""
        return ErrorContext(
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            operation=operation,
            user_message="Invalid input provided",
            technical_details=validation_error,
            suggested_action="Please check your input and try again",
        )


def print_trace(ex: Exception) -> None:
    """
    Helper function to print exception traces.

    Args:
        ex: Exception to print trace for
    """
    print("".join(traceback.TracebackException.from_exception(ex).format()))


def handle_llm_error(
    error: Exception,
    operation: str,
    model: str,
    span: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Handle and format LLM-related errors.

    Args:
        error: The exception that occurred
        operation: The operation that failed
        model: The model being used
        span: Optional OpenTelemetry span

    Returns:
        Formatted error response
    """
    context = ErrorHandler.create_llm_error_context(operation, model, error)
    ErrorHandler.log_error(error, context, span)
    return ErrorHandler.format_error_response(error, context)


def handle_tool_error(
    error: Exception,
    operation: str,
    tool_name: str,
    span: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Handle and format tool execution errors.

    Args:
        error: The exception that occurred
        operation: The operation that failed
        tool_name: The tool that failed
        span: Optional OpenTelemetry span

    Returns:
        Formatted error response
    """
    context = ErrorHandler.create_tool_error_context(operation, tool_name, error)
    ErrorHandler.log_error(error, context, span)
    return ErrorHandler.format_error_response(error, context)


def handle_validation_error(
    validation_error: str,
    operation: str,
    span: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Handle and format validation errors.

    Args:
        validation_error: Description of the validation error
        operation: The operation that failed
        span: Optional OpenTelemetry span

    Returns:
        Formatted error response
    """
    error = ValueError(validation_error)
    context = ErrorHandler.create_validation_error_context(operation, validation_error)
    ErrorHandler.log_error(error, context, span)
    return ErrorHandler.format_error_response(error, context)


def safe_json_dumps(data: Any, default_value: str = "{}") -> str:
    """
    Safely serialize data to JSON string.

    Args:
        data: Data to serialize
        default_value: Default value if serialization fails

    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize data to JSON: {e}")
        return default_value


def create_error_stream_response(error_dict: Dict[str, Any]) -> str:
    """
    Create a streaming response format for errors.

    Args:
        error_dict: Error dictionary to format

    Returns:
        JSON string with newline for streaming
    """
    return safe_json_dumps(error_dict) + "\n"
