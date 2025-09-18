"""
Chat Orchestration Service module for coordinating LLM and tool interactions.

This module provides a centralized service for orchestrating multi-turn
conversations with tool execution and streaming responses.
"""

import json
import logging
from typing import Any, AsyncGenerator, Dict, List

from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.context import Context

from src.conversation import ConversationManager
from .llm_service import LLMService
from .tool_execution_service import ToolExecutionService

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def print_trace(ex: Exception):
    """Helper function to print exception traces."""
    import traceback

    print("".join(traceback.TracebackException.from_exception(ex).format()))


class ChatOrchestrationService:
    """
    Service for orchestrating streaming chat responses with tool execution.

    Coordinates LLM communication and tool execution in multi-turn conversations,
    handling the complete conversation flow from user input to final response.
    """

    def __init__(
        self,
        llm_service: LLMService,
        tool_execution_service: ToolExecutionService,
        model_config: Dict[str, Any] = None,
    ):
        """
        Initialize the chat orchestration service.

        Args:
            llm_service: Service for LLM communication
            tool_execution_service: Service for tool execution
            model_config: Optional model configuration override
        """
        self.llm_service = llm_service
        self.tool_execution_service = tool_execution_service
        self.model_config = model_config or {}

    async def stream_chat_with_tools(
        self,
        model: str,
        conv_manager: ConversationManager,
        parent_ctx: Context,
        max_turns: int = 10,
    ) -> AsyncGenerator[str, None]:
        """
        Orchestrates streaming chat responses with tool execution.

        This function coordinates the complete conversation flow including
        LLM streaming and tool execution across multiple turns.

        Args:
            model: The model name to use
            conv_manager: Conversation manager for state persistence
            parent_ctx: OpenTelemetry context for tracing
            max_turns: Maximum number of turns to prevent infinite loops

        Yields:
            JSON-formatted strings representing conversation events
        """
        with tracer.start_as_current_span(
            "streaming_chat_orchestration",
            attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
            context=parent_ctx,
        ) as span:
            try:
                # Get model configuration
                config = self._prepare_model_config(model)
                available_tools = config.get("available_tools")
                thinking_effort = config.get("thinking_effort")

                tools_count = len(available_tools) if available_tools else 0
                logger.info(
                    f"Starting chat stream with model: {model}, tools: {tools_count}"
                )

                # Yield initial metadata
                yield json.dumps(
                    {
                        "stage": "metadata",
                        "conversation_id": conv_manager.get_current_conversation().id,
                    }
                ) + "\n"

                # Main conversation loop
                turn_count = 0
                while turn_count < max_turns:
                    turn_count += 1
                    logger.debug(f"Starting turn: {turn_count}")

                    try:
                        # Process single turn and get completion status
                        turn_generator = self._process_single_turn(
                            model=model,
                            conv_manager=conv_manager,
                            available_tools=available_tools,
                            thinking_effort=thinking_effort,
                        )

                        conversation_complete = False
                        async for chunk_or_status in turn_generator:
                            if (
                                isinstance(chunk_or_status, dict)
                                and "_internal_complete" in chunk_or_status
                            ):
                                conversation_complete = chunk_or_status[
                                    "_internal_complete"
                                ]
                            else:
                                # Ensure we only yield strings, not dictionaries
                                if isinstance(chunk_or_status, str):
                                    yield chunk_or_status
                                else:
                                    # Convert dict to JSON string if needed
                                    yield json.dumps(chunk_or_status) + "\n"

                        # Check if conversation is complete
                        if conversation_complete:
                            break

                    except Exception as e:
                        print_trace(e)
                        error_msg = f"Error in chat loop iteration: {e}"
                        logger.error(error_msg)
                        span.record_exception(e)
                        span.set_status(Status(StatusCode.ERROR, str(e)))

                        error_response = {
                            "stage": "error",
                            "response": f"Chat loop error: {str(e)}",
                        }
                        yield json.dumps(error_response) + "\n"
                        raise

                if turn_count >= max_turns:
                    logger.warning(
                        f"Reached maximum turns ({max_turns}), stopping conversation"
                    )
                    yield json.dumps(
                        {
                            "stage": "warning",
                            "response": "Conversation reached maximum turn limit",
                        }
                    ) + "\n"

            except Exception as e:
                print_trace(e)
                logger.error(f"Critical error in chat orchestration: {e}")
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    async def _process_single_turn(
        self,
        model: str,
        conv_manager: ConversationManager,
        available_tools: List[Dict] = None,
        thinking_effort: str = None,
    ) -> AsyncGenerator[Any, None]:
        """
        Process a single conversation turn.

        Args:
            model: Model name
            conv_manager: Conversation manager
            available_tools: Available tools for the model
            thinking_effort: Thinking effort level

        Yields:
            JSON-formatted strings for turn events or completion status
        """
        tool_calls_this_turn = []
        full_thinking: List[str] = []
        full_content: List[str] = []

        # Prepare messages for LLM
        messages_for_llm = [
            m.to_dict() for m in conv_manager.get_current_conversation().messages
        ]

        # Stream model response and collect tool calls
        streamer = self.llm_service.stream_model_response(
            messages_for_llm,
            model,
            thinking_effort,
            available_tools,
        )

        try:
            async for chunk in streamer:
                stage = chunk.get("stage")
                if stage == "thinking":
                    full_thinking.append(chunk["response"])
                    yield json.dumps(chunk) + "\n"
                elif stage == "content":
                    full_content.append(chunk["response"])
                    yield json.dumps(chunk) + "\n"
                elif stage == "tool_call_chunk":
                    tool_calls_this_turn.append(chunk["tool_call"])
                elif stage == "error":
                    yield json.dumps(chunk) + "\n"
                    raise RuntimeError(
                        chunk.get(
                            "response", "Unknown error occurred during model streaming"
                        )
                    )

        except Exception as e:
            print_trace(e)
            logger.error(f"Error in model streaming: {e}")
            raise

        # Save assistant message
        assistant_content = "".join(full_content)
        assistant_thinking_content = "".join(full_thinking)

        conv_manager.add_assistant_message(
            content=assistant_content,
            thinking=assistant_thinking_content,
            tool_calls=tool_calls_this_turn,
            model=model,
        )

        # Check for tool calls and execute them
        if not tool_calls_this_turn:
            yield json.dumps({"stage": "finalize_answer"}) + "\n"
            yield {"_internal_complete": True}  # Signal conversation complete
            return

        logger.info(f"Executing {len(tool_calls_this_turn)} tool call(s)")

        # Execute tools and stream results
        tool_executor = self.tool_execution_service.execute_tools(
            tool_calls_this_turn,
            conv_manager,
        )

        async for tool_result in tool_executor:
            yield json.dumps(tool_result) + "\n"

        yield {"_internal_complete": False}  # Signal more turns needed

    def _prepare_model_config(self, model: str) -> Dict[str, Any]:
        """
        Prepare model-specific configuration.

        Args:
            model: Model name

        Returns:
            Configuration dictionary for the model
        """
        # Default configuration
        config = {
            "available_tools": None,
            "thinking_effort": None,
            "supports_tools": False,
        }

        # Model-specific configurations
        # Note: This could be moved to the model configuration module in the future
        if model in ["gpt-oss:20b"]:
            config.update(
                {
                    "available_tools": self.tool_execution_service.get_tool_capabilities(
                        model
                    ),
                    "thinking_effort": "low",
                    "supports_tools": True,
                }
            )

        # Apply any overrides from instance config
        config.update(self.model_config.get(model, {}))

        logger.debug(f"Model config for {model}: {config}")
        return config

    def get_conversation_metadata(
        self, conv_manager: ConversationManager
    ) -> Dict[str, Any]:
        """
        Get metadata about the current conversation state.

        Args:
            conv_manager: Conversation manager

        Returns:
            Dictionary containing conversation metadata
        """
        conversation = conv_manager.get_current_conversation()
        if not conversation:
            return {}

        return {
            "conversation_id": conversation.id,
            "message_count": conversation.get_message_count(),
            "model": conversation.model,
            "created_at": (
                conversation.created_at.isoformat() if conversation.created_at else None
            ),
            "title": conversation.title,
        }

    def validate_conversation_state(self, conv_manager: ConversationManager) -> bool:
        """
        Validate that the conversation is in a valid state for processing.

        Args:
            conv_manager: Conversation manager to validate

        Returns:
            True if valid, False otherwise
        """
        if not conv_manager:
            return False

        conversation = conv_manager.get_current_conversation()
        if not conversation:
            return False

        if not conversation.messages:
            return False

        # Check that the last message is from the user
        last_message = conversation.messages[-1]
        if last_message.role.value != "user":
            logger.warning(
                "Last message is not from user, cannot continue conversation"
            )
            return False

        return True
