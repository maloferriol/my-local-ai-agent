"""Module for handling Ollama chat interactions and tool execution."""

import json
import logging.config
import os
from typing import List, Optional

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
ollama_client = AsyncClient(host=os.environ["OLLAMA_URL"])


app = FastAPI()

available_tools_default = {
    "get_weather": get_weather,
    "get_weather_conditions": get_weather_conditions,
}


async def _stream_chat_with_tools(messages: List[ChatMessage], model: str):
    """Stream chat responses with tool execution capabilities.
    
    Args:
        messages: List of chat messages
        model: Name of the model to use
        
    Yields:
        JSON-encoded strings containing response chunks and tool execution results
    """
    
    try:
        available_tools = None
        thinking_effort = None
        if model in ["gpt-oss:20b"]:
            available_tools = list(available_tools_default.values())
            thinking_effort = 'low'
            
        while True:
            response = await ollama_client.chat(
                model=model,
                messages=messages,
                think=thinking_effort,
                tools=available_tools,
                stream=True,
            )
            
            logger.debug("Starting chat stream with model: %s", model)

            full_response = ""
            thinking = ""
            tool_calls = []

            async for event in response:
                try:
                    if event.get('message', {}).get('tool_calls'):
                        tool_calls.extend(event['message']['tool_calls'])
                except Exception as e:
                    logger.error("Error processing tool calls: %s", str(e))
                    res = {"stage": "error", "response": str(e)}
                    yield json.dumps(res) + "\n"
                    break

                if not event.get("done"):
                    msg = event.get("message", {})
                    thinking_chunk = msg.get("thinking")
                    if thinking_chunk:
                        yield json.dumps({
                            "stage": "thinking",
                            "response": thinking_chunk,
                        }) + "\n"
                        thinking += thinking_chunk

                    # Stream content
                    content_chunk = msg.get("content", "")
                    if content_chunk:
                        full_response += content_chunk
                        yield json.dumps({
                            "stage": "content",
                            "response": content_chunk,
                            "tool_calls": msg.get("tool_calls", []),
                        }) + "\n"

                    # Accumulate tool calls if any
                    tool_call = getattr(msg, "tool_calls", None) or msg.get("tool_calls")
                    if tool_call:
                        tool_calls.extend(tool_call)

            if tool_calls == []:
                # End of this model turn: emit a finalize marker once
                yield json.dumps({"stage": "finalize_answer"}) + "\n"

            # If there are tool calls, execute them, append results, continue loop
            if tool_calls:
                for tool_call in tool_calls:
                    try:
                        tool_name = tool_call.function.name

                        function_to_call = available_tools_default.get(tool_name)
                        if function_to_call:
                            try:
                                args = tool_call.function.arguments
                                result = function_to_call(**args)
                                # Stream tool result right away
                                yield json.dumps({
                                    "stage": "tool_result",
                                    "tool": tool_name,
                                    "args": args,
                                    "result": result,
                                }) + "\n"

                                # Append tool result to messages for next model turn
                                messages.append(
                                    {
                                        "role": "tool",
                                        "content": result,
                                        "tool_name": tool_name,
                                    }
                                )
                            except Exception as e:
                                logger.error("Tool execution error: %s", str(e))
                                yield json.dumps({
                                    "stage": "tool_error",
                                    "tool": tool_name,
                                    "error": str(e),
                                }) + "\n"
                    except Exception as tool_err:
                        logger.error("Tool invocation error: %s", str(tool_err))
                        yield json.dumps({
                            "stage": "tool_error",
                            "tool": tool_name if 'tool_name' in locals() else None,
                            "error": str(tool_err),
                        }) + "\n"

                # Continue loop to let the model respond using tool outputs
                continue
            else:
                # No more tool calls; finish
                break

    except Exception as e:
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

    try:
        model = query.messages[len(query.messages)-1].model
    except Exception as e:
        model = "gpt-oss:20b"
        print('FAIL model error:', e)

    try:
        msgs = [msg.to_dict() for msg in query.messages]
    except Exception as e:
        print('FAIL parsing messages error:', e)

    return StreamingResponse(
        _stream_chat_with_tools(msgs, model),
        media_type="text/plain"
    )
