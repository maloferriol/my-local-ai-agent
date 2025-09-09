"""Module for handling Ollama chat interactions and tool execution."""

import json
import logging.config
from contextlib import asynccontextmanager
import os
from typing import Any, AsyncGenerator, Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from ollama import AsyncClient
from openinference.semconv.trace import SpanAttributes
from opentelemetry import trace
from opentelemetry.trace import SpanKind
from opentelemetry.trace.status import Status, StatusCode

from rich import print

from .examples import get_weather, get_weather_conditions
import traceback

from src.database.db import DatabaseManager
from src.models import Conversation
from src.logging_config import LOGGING_CONFIG
from src.conversation import ConversationManager


# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)

# Initialize tracer
tracer = trace.get_tracer(__name__)

# Initialize DatabaseManager
db_manager = DatabaseManager()


def print_trace(ex: BaseException):
    print("".join(traceback.TracebackException.from_exception(ex).format()))


# Initialize Ollama client
try:
    ollama_client = AsyncClient(host=os.environ["OLLAMA_URL"])
except Exception as e:
    print(f"FAIL Ollama client initialization error: {e}")
    logger.error(f"Failed to initialize Ollama client: {e}")
    raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle."""
    print("Initializing database connection...")
    db_manager.connect()
    db_manager.create_init_tables()
    logger.info("Database connected and tables created.")
    yield
    db_manager.close()
    logger.info("Database connection closed.")


app = FastAPI(lifespan=lifespan)

available_tools_default = {
    "get_weather": get_weather,
    "get_weather_conditions": get_weather_conditions,
}


@app.get("/conversation/{conversation_id}", response_model=Conversation)
@tracer.start_as_current_span(name="get_conversation", kind=SpanKind.INTERNAL)
async def get_conversation(conversation_id: int):
    """
    Fetch a conversation by its ID.

    Args:
        conversation_id: The ID of the conversation to fetch.

    Returns:
        The conversation object.
    """
    if db_manager.conn is None:
        db_manager.connect()
        db_manager.create_init_tables()

    print(
        "/conversation/"
    )
    print("==========================================================================")

    conv_manager = ConversationManager(db_manager)
    try:
        # The load_conversation method returns a Conversation object or None
        conversation = conv_manager.load_conversation(conversation_id)
        if conversation:
            # The response_model will handle the serialization
            return conversation
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _stream_model_response(  # noqa: C901
    messages: List[Dict[str, Any]],
    model: str,
    think: str | None,
    tools: List[Dict] | None,
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
            # Consider truncating or hashing messages if large/PII-sensitive
            span.set_attribute("llm.input_messages", messages)
        except Exception as e:
            logger.error(
                f"Tracing LLM invocation parameters error: {e}",
                exc_info=True,
            )
            print(
                f"Tracing LLM invocation parameters error: {e}",
                exc_info=True,
            )

        try:
            print("messages", messages)
            response_stream = await ollama_client.chat(
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
                msg = event.get("message", {})
                if not event.get("done"):
                    if thinking_chunk := msg.get("thinking"):
                        thinking_chunks.append(thinking_chunk)
                        yield {"stage": "thinking", "response": thinking_chunk}

                    if content_chunk := msg.get("content", ""):
                        content_chunks.append(content_chunk)
                        yield {"stage": "content", "response": content_chunk}

                if tool_calls := msg.get("tool_calls"):
                    for tool_call in tool_calls:
                        print("tool_call", tool_call)
                        tool_call_chunks.append(tool_call)
                        yield {"stage": "tool_call_chunk", "tool_call": tool_call}

            if thinking_chunks:
                span.set_attribute("llm.thinking", "".join(thinking_chunks))

        except Exception as e:
            print(f"FAIL Ollama client chat error: {e}")
            print_trace(e)
            logger.error(f"Ollama client chat error: {e}")
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            yield {"stage": "error", "response": f"Model communication error: {str(e)}"}
            raise


async def _execute_tools(
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
                        if not tool_name:
                            print(f"FAIL Tool call missing name: {tool_call}")
                            logger.warning(f"Tool call missing name: {tool_call}")
                            continue

                        tool_span.set_attribute("tool.name", tool_name)

                        function_to_call = available_tools_default.get(tool_name)
                        if not function_to_call:
                            error_msg = f"Tool '{tool_name}' not found."
                            print(f"FAIL {error_msg}")
                            logger.error(error_msg)
                            raise ValueError(error_msg)

                        args = tool_call.get("function", {}).get("arguments", {})
                        tool_span.set_attribute("tool.arguments", json.dumps(args))
                        print(f"Executing tool '{tool_name}' with args: {args}")
                        result = function_to_call(**args)
                        tool_span.set_attribute("tool.result", str(result))
                        # Save tool result using the conversation manager
                        conv_manager.add_tool_message(
                            content=str(result),
                            tool_name=tool_name,
                            model=conv_manager.get_current_conversation().model,
                        )

                        # Yield the result to the client
                        yield {
                            "stage": "tool_result",
                            "tool": tool_name,
                            "args": args,
                            "result": result,
                        }

                    except Exception as e:
                        tool_span.record_exception(e)
                        tool_span.set_status(Status(StatusCode.ERROR, str(e)))
                        error_msg = f"Tool execution error for '{tool_name}': {e}"
                        print(f"FAIL {error_msg}")
                        logger.error(error_msg)
                        yield {
                            "stage": "tool_error",
                            "tool": tool_name,
                            "error": str(e),
                        }
        except Exception as e:
            outer_span.record_exception(e)
            outer_span.set_status(Status(StatusCode.ERROR, str(e)))
            error_msg = f"Critical error in tool execution loop: {e}"
            print(f"FAIL {error_msg}")
            logger.error(error_msg)
            yield {
                "stage": "error",
                "response": f"Tool execution system error: {str(e)}",
            }


# @tracer.start_as_current_span(
#     name="_stream_chat_with_tools_refactored",
#     attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
# )
async def _stream_chat_with_tools_refactored(  # noqa: C901
    model: str,
    conv_manager: ConversationManager,
):
    """
    Orchestrates streaming chat responses with tool execution.

    This refactored function delegates streaming and tool logic to helper
    async generators, making the control flow clearer.
    """

    # This is the crucial change:
    # We create a new span that encapsulates the entire generator's lifetime.
    with tracer.start_as_current_span(
        "streaming_chat_orchestration",
        attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
    ) as span:

        # Model-specific setup
        # Todo extract this into a config file
        available_tools: List[Any] | None = None
        thinking_effort = None
        if model in ["gpt-oss:20b"]:
            available_tools = list(available_tools_default.values())
            thinking_effort = "low"

        tools_count = len(available_tools) if available_tools else 0
        print(f"Starting chat stream with model: {model}, tools: {tools_count}")
        logger.info(f"Starting chat stream with model: {model}")

        yield json.dumps(
            {
                "stage": "metadata",
                "conversation_id": conv_manager.get_current_conversation().id,
            }
        ) + "\n"

        count = 0
        while True:
            count += 1
            print("Turn:", count)
            try:
                tool_calls_this_turn = []
                full_thinking: List[str] = []
                full_content: List[str] = []

                messages_for_llm = [
                    m.to_dict()
                    for m in conv_manager.get_current_conversation().messages
                ]
                # === Part 1: Stream model response and collect tool calls ===
                streamer = _stream_model_response(
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
                except Exception as e:
                    print_trace(e)
                    print(f"FAIL Error in chat loop iteration: {e}")
                    raise

                assistant_content = "".join(full_content)
                assistant_thinking_content = "".join(full_thinking)

                conv_manager.add_assistant_message(
                    content=assistant_content,
                    thinking=assistant_thinking_content,
                    model=model,
                )

                # === Part 2: Check for tool calls and execute them ===
                if not tool_calls_this_turn:
                    yield json.dumps({"stage": "finalize_answer"}) + "\n"
                    break  # No tools to call, so we're done.

                print(f"Executing {len(tool_calls_this_turn)} tool call(s)")
                # We have tools to call, so execute them and stream results.
                tool_executor = _execute_tools(tool_calls_this_turn, conv_manager)

                async for tool_result in tool_executor:
                    yield json.dumps(tool_result) + "\n"

                # Loop continues to the next turn with the updated messages list...
            except Exception as e:
                print_trace(e)
                print("line 333")
                print(f"FAIL Error in chat loop iteration: {e}")
                logger.error(f"Error in chat loop iteration: {e}")
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                error_response = {
                    "stage": "error",
                    "response": f"Chat loop error: {str(e)}",
                }
                yield json.dumps(error_response) + "\n"
                raise
                break  # Exit the loop on critical error


@app.post("/invoke")
@tracer.start_as_current_span(
    name="invoke",
    attributes={SpanAttributes.OPENINFERENCE_SPAN_KIND: "CHAIN"},
)
async def invoke(conversation: Conversation):
    """
    Handle user queries by streaming responses from Ollama.

    Args:
        conversation: UserQuery object containing messages and model configuration

    Returns:
        StreamingResponse containing chat responses and tool execution results
    """
    current_span = trace.get_current_span()
    try:
        logger.info("Received chat")
        print("Received chat", conversation)

        msg_count = len(conversation.messages) if conversation.messages else 0
        print(f"Received chat request with {msg_count} messages")

        # current_span.set_attribute(
        #     "llm.input_messages",
        #     json.dumps([msg.to_dict() for msg in conversation.messages])
        # )

    except Exception as e:
        print_trace(e)
        print("Error e:", e)

    if db_manager.conn is None:
        db_manager.connect()
        db_manager.create_init_tables()

    conv_manager = ConversationManager(db_manager, conversation)

    user_message = conversation.messages[-1] if conversation.messages else None

    if not user_message:
        # Handle case with no messages
        error_response = {"stage": "error", "response": "Query contains no messages."}
        return StreamingResponse(
            iter([json.dumps(error_response) + "\n"]),
            media_type="text/plain",
        )

    model = user_message.model or "gpt-oss:20b"  # Default model
    current_span.set_attribute("llm.model_name", model)

    try:
        return StreamingResponse(
            _stream_chat_with_tools_refactored(model, conv_manager),
            media_type="text/plain",
        )
    except Exception as e:
        print_trace(e)
        print(f"FAIL StreamingResponse creation error: {e}")
        logger.error(f"Failed to create StreamingResponse: {e}")
        # Return error response
        error_response = {
            "stage": "error",
            "response": f"Response creation error: {str(e)}",
        }
        return StreamingResponse(
            iter([json.dumps(error_response) + "\n"]),
            media_type="text/plain",
        )
