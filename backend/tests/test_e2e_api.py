"""
End-to-end API tests using FastAPI TestClient.

These tests simulate real HTTP requests to the API endpoints while using
in-memory SQLite and mocked Ollama responses for isolation and speed.

Note: These tests may generate ResourceWarnings about unclosed database connections.
This is expected behavior when testing the full FastAPI application stack, as the
application manages its own database connection lifecycle. For production use,
connections are properly managed through context managers and application lifecycle.
"""

import json
import os
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

# Mock environment before importing the app to avoid OLLAMA_URL error
with patch.dict(os.environ, {"OLLAMA_URL": "http://localhost:11434"}):
    from src.app import app
    from src.database.db import DatabaseManager


@pytest.fixture(scope="function")
def test_client():
    """
    FastAPI TestClient fixture that provides HTTP testing capabilities.
    """
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_ollama_response():
    """
    Mock Ollama streaming response for consistent testing.
    """
    async def mock_chat(*args, **kwargs):
        # Simulate streaming response from Ollama
        yield {
            "message": {"content": "Hello! How can I help you?"},
            "done": False
        }
        yield {
            "message": {"content": ""},
            "done": True
        }
    
    return mock_chat


@pytest.fixture(scope="function", autouse=True)
def setup_test_database(tmp_path):
    """
    Use a temporary database file for each test to ensure proper cleanup.
    """
    # Create a unique test database file 
    test_db_file = tmp_path / "test_conversation.db"
    
    # Patch the default database file path
    with patch('src.database.db.default_db_file', str(test_db_file)):
        yield str(test_db_file)


def test_get_nonexistent_conversation(test_client):
    """
    Test GET /conversation/{id} with non-existent conversation returns 404.
    """
    response = test_client.get("/agent/my_local_agent/conversation/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found"


@patch('src.agent.my_local_agent.route.ollama_client')
def test_create_new_conversation_e2e(mock_ollama_client, test_client, mock_ollama_response):
    """
    Test creating a new conversation through the invoke endpoint.
    """
    # Mock the Ollama client
    mock_ollama_client.chat = AsyncMock(side_effect=mock_ollama_response)
    
    # Create new conversation (id=0 means new)
    payload = {
        "id": 0,
        "title": "Test Conversation",
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "user",
                "content": "Hello, this is a test message",
                "model": "gpt-oss:20b"
            }
        ]
    }
    
    response = test_client.post("/agent/my_local_agent/invoke", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"
    
    # Verify the streaming response contains expected stages
    response_text = response.text
    lines = [line for line in response_text.split('\n') if line.strip()]
    
    # Parse the JSON responses
    responses = [json.loads(line) for line in lines]
    
    # Should contain metadata with conversation_id
    metadata_responses = [r for r in responses if r.get("stage") == "metadata"]
    assert len(metadata_responses) == 1
    assert "conversation_id" in metadata_responses[0]
    
    # Should contain content responses
    content_responses = [r for r in responses if r.get("stage") == "content"]
    assert len(content_responses) > 0


@patch('src.agent.my_local_agent.route.ollama_client')
def test_conversation_with_tool_calls_e2e(mock_ollama_client, test_client):
    """
    Test conversation flow that includes tool calls.
    """
    # Track calls to provide different responses
    call_count = 0
    
    async def mock_chat_with_tools(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        
        if call_count == 1:
            # First response with tool call
            yield {
                "message": {
                    "content": "I'll check the weather for you.",
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_weather",
                                "arguments": {"city": "London"}
                            }
                        }
                    ]
                },
                "done": False
            }
            yield {
                "message": {"content": ""},
                "done": True
            }
        else:
            # Second response - final answer without tool calls
            yield {
                "message": {"content": "The weather in London is -8°C. It's quite cold!"},
                "done": False
            }
            yield {
                "message": {"content": ""},
                "done": True
            }
    
    mock_ollama_client.chat = AsyncMock(side_effect=mock_chat_with_tools)
    
    payload = {
        "id": 0,
        "title": "Weather Test",
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "user",
                "content": "What's the weather in London?",
                "model": "gpt-oss:20b"
            }
        ]
    }
    
    response = test_client.post("/agent/my_local_agent/invoke", json=payload)
    assert response.status_code == 200
    
    response_text = response.text
    lines = [line for line in response_text.split('\n') if line.strip()]
    responses = [json.loads(line) for line in lines]
    
    # Should contain tool results
    tool_result_responses = [r for r in responses if r.get("stage") == "tool_result"]
    assert len(tool_result_responses) > 0
    assert tool_result_responses[0]["tool"] == "get_weather"
    
    # Should contain content responses
    content_responses = [r for r in responses if r.get("stage") == "content"]
    assert len(content_responses) > 0
    
    # Should contain finalize_answer
    finalize_responses = [r for r in responses if r.get("stage") == "finalize_answer"]
    assert len(finalize_responses) > 0


@patch('src.agent.my_local_agent.route.ollama_client')
def test_continue_existing_conversation_e2e(mock_ollama_client, test_client, mock_ollama_response):
    """
    Test continuing an existing conversation.
    """
    mock_ollama_client.chat = AsyncMock(side_effect=mock_ollama_response)
    
    # First, create a conversation
    payload1 = {
        "id": 0,
        "title": "Test Conversation",
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "user",
                "content": "Hello",
                "model": "gpt-oss:20b"
            }
        ]
    }
    
    response1 = test_client.post("/agent/my_local_agent/invoke", json=payload1)
    assert response1.status_code == 200
    
    # Extract conversation_id from first response
    lines1 = [line for line in response1.text.split('\n') if line.strip()]
    responses1 = [json.loads(line) for line in lines1]
    metadata = [r for r in responses1 if r.get("stage") == "metadata"][0]
    conversation_id = metadata["conversation_id"]
    
    # Continue the conversation
    payload2 = {
        "id": conversation_id,
        "title": "Test Conversation",
        "model": "gpt-oss:20b",
        "messages": [
            {
                "role": "user",
                "content": "How are you?",
                "model": "gpt-oss:20b"
            }
        ]
    }
    
    response2 = test_client.post("/agent/my_local_agent/invoke", json=payload2)
    assert response2.status_code == 200
    
    # Verify we can fetch the conversation
    conv_response = test_client.get(f"/agent/my_local_agent/conversation/{conversation_id}")
    assert conv_response.status_code == 200
    
    conversation = conv_response.json()
    assert conversation["id"] == conversation_id
    assert len(conversation["messages"]) >= 2  # Should have multiple messages


def test_invalid_payload_e2e(test_client):
    """
    Test API with invalid payload returns proper error.
    """
    # Empty messages
    payload = {
        "id": 0,
        "title": "Test",
        "model": "gpt-oss:20b",
        "messages": []
    }
    
    response = test_client.post("/agent/my_local_agent/invoke", json=payload)
    assert response.status_code == 400
    assert "Query contains no messages" in response.json()["detail"]


def test_api_structure_e2e(test_client):
    """
    Test that the API structure is working properly for basic cases.
    """
    # Test that the endpoint exists and handles missing conversation correctly
    response = test_client.get("/agent/my_local_agent/conversation/999")
    assert response.status_code == 404
    
    # Test that invoke endpoint rejects invalid data
    response = test_client.post("/agent/my_local_agent/invoke", json={})
    assert response.status_code == 400  # Validation error for missing fields