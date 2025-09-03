"""Module for handling Ollama chat interactions and tool execution."""

import json
import logging.config
import os
from typing import List, Dict, Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from ollama import AsyncClient

from .examples import get_weather, get_weather_conditions
from .logging_config import LOGGING_CONFIG
from .models import Conversation, ChatMessage

# Configure logging
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# Initialize Ollama client
try:
    ollama_client = AsyncClient(host=os.environ["OLLAMA_URL"])
except Exception as e:
    print(f"FAIL Ollama client initialization error: {e}")
    logger.error(f"Failed to initialize Ollama client: {e}")
    raise


app = FastAPI()

available_tools_default = {
    "get_weather": get_weather,
    "get_weather_conditions": get_weather_conditions,
}


async def _stream_model_response(
    messages: List[ChatMessage],
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
    try:
        response_stream = await ollama_client.chat(
            model=model,
            messages=messages,
            think=think,
            tools=tools,
            stream=True,
        )

        async for event in response_stream:
            if not event.get("done"):
                msg = event.get("message", {})

                if thinking_chunk := msg.get("thinking"):
                    yield {"stage": "thinking", "response": thinking_chunk}

                if content_chunk := msg.get("content", ""):
                    yield {"stage": "content", "response": content_chunk}

                if tool_calls := msg.get("tool_calls"):
                    for tool_call in tool_calls:
                        yield {"stage": "tool_call_chunk", "tool_call": tool_call}
    except Exception as e:
        print(f"FAIL Ollama client chat error: {e}")
        logger.error(f"Ollama client chat error: {e}")
        yield {"stage": "error", "response": f"Model communication error: {str(e)}"}


async def _execute_tools(
    tool_calls: List[Dict[str, Any]],
    messages: List[ChatMessage],
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Executes a list of tool calls and yields their results.

    This function also appends the tool results to the messages list for the
    next iteration of the conversation.

    Args:
        tool_calls: A list of tool calls received from the model.
        messages: The conversation history, which will be mutated with tool results.

    Yields:
        A dictionary representing a tool result or an error.
    """
    try:
        for tool_call in tool_calls:
            try:
                tool_name = tool_call.get("function", {}).get("name")
                if not tool_name:
                    print(f"FAIL Tool call missing name: {tool_call}")
                    logger.warning(f"Tool call missing name: {tool_call}")
                    continue

                function_to_call = available_tools_default.get(tool_name)
                if not function_to_call:
                    error_msg = f"Tool '{tool_name}' not found."
                    print(f"FAIL {error_msg}")
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                args = tool_call.get("function", {}).get("arguments", {})
                print(f"Executing tool '{tool_name}' with args: {args}")
                result = function_to_call(**args)

                # Yield the result to the client
                yield {
                    "stage": "tool_result",
                    "tool": tool_name,
                    "args": args,
                    "result": result,
                }

                # Append the successful tool result for the model's context
                messages.append(
                    {
                        "role": "tool",
                        "content": result,
                        "tool_name": tool_name,
                    }
                )
            except Exception as e:
                error_msg = f"Tool execution error for '{tool_name}': {e}"
                print(f"FAIL {error_msg}")
                logger.error(error_msg)
                yield {
                    "stage": "tool_error",
                    "tool": tool_name,
                    "error": str(e),
                }
    except Exception as e:
        error_msg = f"Critical error in tool execution loop: {e}"
        print(f"FAIL {error_msg}")
        logger.error(error_msg)
        yield {
            "stage": "error",
            "response": f"Tool execution system error: {str(e)}",
        }


async def _stream_chat_with_tools_refactored(messages: List[ChatMessage], model: str):
    """
    Orchestrates streaming chat responses with tool execution.

    This refactored function delegates streaming and tool logic to helper
    async generators, making the control flow clearer.
    """
    try:
        # Model-specific setup
        # Todo extract this into a config file
        available_tools = None
        thinking_effort = None
        if model in ["gpt-oss:20b"]:
            available_tools = list(available_tools_default.values())
            thinking_effort = "low"

        tools_count = len(available_tools) if available_tools else 0
        print(f"Starting chat stream with model: {model}, tools: {tools_count}")
        logger.info(f"Starting chat stream with model: {model}")

        count = 0
        while True:
            count += 1
            print("count:", count)
            try:
                tool_calls_this_turn = []

                # === Part 1: Stream model response and collect tool calls ===
                streamer = _stream_model_response(
                    messages, model, thinking_effort, available_tools
                )
                async for chunk in streamer:
                    # If it's a tool_call chunk, collect it. Otherwise, stream it.
                    if chunk["stage"] == "tool_call_chunk":
                        tool_calls_this_turn.append(chunk["tool_call"])
                    else:
                        yield json.dumps(chunk) + "\n"

                # === Part 2: Check for tool calls and execute them ===
                if not tool_calls_this_turn:
                    yield json.dumps({"stage": "finalize_answer"}) + "\n"
                    break  # No tools to call, so we're done.

                print(f"Executing {len(tool_calls_this_turn)} tool calls")
                # We have tools to call, so execute them and stream results.
                # The 'messages' list is passed by reference and will be updated inside.
                tool_executor = _execute_tools(tool_calls_this_turn, messages)
                async for tool_result in tool_executor:
                    yield json.dumps(tool_result) + "\n"

                # Loop continues to the next turn with the updated messages list...
            except Exception as e:
                print(f"FAIL Error in chat loop iteration: {e}")
                logger.error(f"Error in chat loop iteration: {e}")
                error_response = {
                    "stage": "error",
                    "response": f"Chat loop error: {str(e)}",
                }
                yield json.dumps(error_response) + "\n"
                break  # Exit the loop on critical error

    except Exception as e:
        error_msg = f"An unexpected error occurred in the chat stream: {e}"
        print(f"FAIL {error_msg}")
        logger.error(error_msg)
        res = {"stage": "error", "response": str(e)}
        yield json.dumps(res) + "\n"


@app.post("/invoke")
async def invoke(query: Conversation):
    """
    Handle user queries by streaming responses from Ollama.

    Args:
        query: UserQuery object containing messages and model configuration

    Returns:
        StreamingResponse containing chat responses and tool execution results
    """
    logger.info("Received chat")
    msg_count = len(query.messages) if query.messages else 0
    print(f"Received chat request with {msg_count} messages")

    try:
        model = query.messages[len(query.messages) - 1].model
        print(f"Using model: {model}")
    except Exception as e:
        model = "gpt-oss:20b"
        print(f"FAIL model error: {e}, using default model: {model}")
        logger.warning(f"Model extraction failed: {e}, using default: {model}")

    try:
        msgs = [msg.to_dict() for msg in query.messages]
        print(f"Successfully parsed {len(msgs)} messages")
    except Exception as e:
        print(f"FAIL parsing messages error: {e}")
        logger.error(f"Failed to parse messages: {e}")
        # Return error response instead of continuing
        error_response = {
            "stage": "error",
            "response": f"Message parsing error: {str(e)}",
        }
        return StreamingResponse(
            iter([json.dumps(error_response) + "\n"]),
            media_type="text/plain",
        )

    try:
        return StreamingResponse(
            # _stream_chat_with_tools(msgs, model),
            _stream_chat_with_tools_refactored(msgs, model),
            media_type="text/plain",
        )
    except Exception as e:
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
