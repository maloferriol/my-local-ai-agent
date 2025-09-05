"""Simple module for direct Ollama chat interactions"""

import json
from typing import List, Optional
import os

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from ollama import AsyncClient


class Message(BaseModel):
    type: str
    content: str
    thinking: Optional[str] = None
    id: str


class ExtraInfo(BaseModel):
    reasoning_model: Optional[str] = "gemma:3b"


class UserQuery(BaseModel):
    messages: List[Message]
    extra_info: ExtraInfo


# Initialize Ollama client
ollama_client = AsyncClient(host=os.environ["OLLAMA_URL"])

app = FastAPI()


@app.post("/invoke")
async def invoke(query: UserQuery):
    """Handle user query directly with Ollama"""
    # Convert messages to Ollama format
    messages = [
        {"role": "user" if msg.type == "human" else "assistant", "content": msg.content}
        for msg in query.messages
    ]

    async def stream():
        try:
            response = await ollama_client.chat(
                model=query.extra_info.reasoning_model, messages=messages, stream=True
            )

            async for event in response:
                if not event["done"]:
                    # print('vent["message"', event["message"])
                    # Stream both thinking and content steps
                    if event["message"].get("thinking"):
                        res = {
                            "stage": "thinking",
                            "response": event["message"]["thinking"],
                        }
                        yield json.dumps(res) + "\n"

                    res = {
                        "stage": "finalize_answer",
                        "response": event["message"]["content"],
                    }
                    yield json.dumps(res) + "\n"

        except Exception as e:
            res = {"stage": "error", "response": str(e)}
            yield json.dumps(res) + "\n"

    return StreamingResponse(stream())
