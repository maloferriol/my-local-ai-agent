"""
LLM Service module for handling model communication and streaming responses.

This module provides a centralized service for interacting with language models,
handling streaming responses, and managing model-specific configurations.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List

from ollama import AsyncClient
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import Status, StatusCode

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class LLMService:
    """
    Service for managing LLM communication and streaming responses.

    Handles direct interaction with language models, streaming responses,
    and model-specific configuration management.
    """

    def __init__(self, ollama_client: AsyncClient):
        """
        Initialize the LLM service.

        Args:
            ollama_client: Configured AsyncClient for Ollama communication
        """
        self.ollama_client = ollama_client

    async def stream_model_response(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        think: str | None = None,
        tools: List[Dict] | None = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streams the response from the Ollama model, yielding structured events.

        This function handles the direct interaction with the model's streaming API.

        Args:
            messages: The list of messages in the conversation history.
            model: The name of the model to use.
            think: The 'thinking' effort parameter for the model, if any.
            tools: A list of available tools for the model to use.

        Yields:
            A dictionary representing a single event from
            the stream (e.g., 'thinking', 'content', 'tool_call').
        """
        with tracer.start_as_current_span(
            "llm_stream",
            kind=SpanKind.INTERNAL,
            attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "LLM"},
        ) as span:
            self._setup_tracing(span, model, think, messages)

            try:
                logger.debug(f"Sending messages to model {model}: {messages}")
                response_stream = await self.ollama_client.chat(
                    model=model,
                    messages=messages,
                    think=think,
                    tools=tools,
                    stream=True,
                )

                thinking_chunks: List[str] = []
                content_chunks: List[str] = []
                tool_call_chunks: List[Dict[str, Any]] = []

                async for event in response_stream:
                    async for result in self._process_stream_event(
                        event, thinking_chunks, content_chunks, tool_call_chunks
                    ):
                        yield result

                if thinking_chunks:
                    print('llm thinking:', "".join(thinking_chunks))

                    span.set_attribute("llm.thinking", "".join(thinking_chunks))
                if content_chunks:
                    print('llm content:', "".join(content_chunks))
                    span.set_attribute("llm.content", "".join(content_chunks))
                if tool_call_chunks:
                    span.set_attribute("llm.tool_calls", json.dumps(tool_call_chunks))

            except Exception as e:
                error_msg = f"Ollama client chat error: {e}"
                logger.error(error_msg, exc_info=True)
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                yield {
                    "stage": "error",
                    "response": f"Model communication error: {str(e)}",
                }
                raise

    def _setup_tracing(
        self,
        span,
        model: str,
        think: str | None,
        messages: List[Dict[str, Any]],
    ) -> None:
        """Setup tracing attributes for the LLM call."""
        try:
            span.set_attribute("llm.model_name", model)
            span.set_attribute(
                "llm.invocation_parameters",
                json.dumps(
                    {
                        "model": model,
                        "think": think,
                        "stream": True,
                    }
                ),
            )
            span.set_attribute("llm.input_messages", json.dumps(messages))
        except Exception as e:
            logger.error(
                f"Tracing LLM invocation parameters error: {e}",
                exc_info=True,
            )
            span.record_exception(e)

    async def _process_stream_event(
        self,
        event: Dict[str, Any],
        thinking_chunks: List[str],
        content_chunks: List[str],
        tool_call_chunks: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a single event from the model stream."""
        msg = event.get("message", {})

        if not event.get("done"):
            if thinking_chunk := msg.get("thinking"):
                thinking_chunks.append(thinking_chunk)
                yield {"stage": "thinking", "response": thinking_chunk}

            if content_chunk := msg.get("content", ""):
                content_chunks.append(content_chunk)
                yield {"stage": "content", "response": content_chunk}

        if tool_calls := msg.get("tool_calls"):
            async for tool_result in self._process_tool_calls(
                tool_calls, tool_call_chunks
            ):
                yield tool_result

    async def _process_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        tool_call_chunks: List[Dict[str, Any]],
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process tool calls from the model response."""
        for tool_call in tool_calls:
            logger.debug(f"Received tool call: {tool_call}")

            if tool_call.get("function"):
                logger.debug(f"Tool call function: {tool_call.get('function')}")
                data = {
                    "function": {
                        "name": tool_call.get("function").get("name"),
                        "arguments": tool_call.get("function").get("arguments"),
                    }
                }
                tool_call_chunks.append(data)
                yield {"stage": "tool_call_chunk", "tool_call": data}

    def validate_model_config(
        self, model: str, tools: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Validate and prepare model configuration.

        Args:
            model: Model name to validate
            tools: Optional tools configuration

        Returns:
            Validated configuration dictionary

        Raises:
            ValueError: If model configuration is invalid
        """
        if not model:
            raise ValueError("Model name is required")

        config = {
            "model": model,
            "tools": tools or [],
            "supports_tools": bool(tools),
        }

        logger.debug(f"Validated model config: {config}")
        return config

    def format_messages_for_model(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Format conversation messages for the specific model.

        Args:
            messages: Raw conversation messages

        Returns:
            Formatted messages ready for model consumption
        """
        formatted_messages = []

        for message in messages:
            formatted_msg = {
                "role": message.get("role"),
                "content": message.get("content", ""),
            }

            # Add additional fields if present
            if "thinking" in message and message["thinking"]:
                formatted_msg["thinking"] = message["thinking"]

            if "tool_calls" in message and message["tool_calls"]:
                formatted_msg["tool_calls"] = message["tool_calls"]

            formatted_messages.append(formatted_msg)

        return formatted_messages
