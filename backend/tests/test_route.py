"""
Tests for the route.py module focusing on improving test coverage.

These tests target specific error paths and edge cases to improve
the overall test coverage from 67% to a higher percentage.
"""

import json
import os
import pytest
import anyio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


# Mock environment before importing
with patch.dict(os.environ, {"OLLAMA_URL": "http://localhost:11434"}):
    from src.agent.my_local_agent.route import app
    from src.utils.error_handling import print_trace


@pytest.fixture(scope="function")
def test_client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_test_database(tmp_path):
    """Use a temporary database file for each test."""
    test_db_file = tmp_path / "test_conversation.db"
    with patch("src.database.db.default_db_file", str(test_db_file)):
        yield str(test_db_file)


@pytest.fixture
def mock_conversation_manager():
    """Mock ConversationManager for testing."""
    with patch("src.agent.my_local_agent.route.ConversationManager") as mock:
        mock_instance = MagicMock()
        mock.create_new.return_value = mock_instance
        mock.load_existing.return_value = mock_instance

        # Create a more complete mock message
        mock_message = MagicMock()
        mock_message.role.value = "user"

        mock_conversation = MagicMock()
        mock_conversation.id = 1
        mock_conversation.model = "test-model"
        mock_conversation.messages = [mock_message]

        mock_instance.get_current_conversation.return_value = mock_conversation
        yield mock


def test_print_trace():
    """Test the print_trace function with an exception."""
    try:
        raise ValueError("Test exception")
    except Exception as e:
        # This should not raise an exception
        print_trace(e)


def test_ollama_client_initialization_error():
    """Test Ollama client initialization error path."""
    with patch.dict(os.environ, {}, clear=True):  # Remove OLLAMA_URL
        with pytest.raises(KeyError):
            # This should trigger the exception handling in the global initialization
            import importlib
            import src.agent.my_local_agent.route

            importlib.reload(src.agent.my_local_agent.route)


@patch("src.agent.my_local_agent.route.DatabaseManager")
def test_lifespan_startup_error(mock_db_manager, test_client):
    """Test lifespan startup database error."""
    mock_db_manager.side_effect = Exception("Database connection failed")

    # The error should be handled in the lifespan context
    with pytest.raises(Exception):
        with test_client:
            pass


def test_get_tools_endpoint(test_client):
    """Test /tools endpoint."""
    with patch("src.agent.my_local_agent.route.tool_registry") as mock_registry:
        mock_tool = MagicMock()
        mock_tool.to_dict.return_value = {"name": "test_tool", "version": "1.0"}
        mock_registry.get_active_tools.return_value = [mock_tool]

        response = test_client.get("/tools")
        assert response.status_code == 200
        assert response.json() == [{"name": "test_tool", "version": "1.0"}]


def test_get_tool_stats_endpoint(test_client):
    """Test /tools/stats endpoint."""
    with patch("src.agent.my_local_agent.route.tool_registry") as mock_registry:
        mock_registry.get_tool_stats.return_value = {
            "total_tools": 5,
            "active_tools": 3,
        }

        response = test_client.get("/tools/stats")
        assert response.status_code == 200
        assert response.json() == {"total_tools": 5, "active_tools": 3}


def test_get_enhanced_conversation_summary_not_found(test_client):
    """Test enhanced summary endpoint with non-existent conversation."""
    with patch(
        "src.agent.my_local_agent.route.ConversationManager.load_existing"
    ) as mock_load:
        mock_load.return_value = None

        response = test_client.get("/conversation/999/enhanced-summary")
        assert response.status_code == 404
        assert response.json()["detail"] == "Conversation not found"


def test_get_enhanced_conversation_summary_success(test_client):
    """Test enhanced summary endpoint success case."""
    with patch(
        "src.agent.my_local_agent.route.ConversationManager.load_existing"
    ) as mock_load:
        mock_manager = MagicMock()
        mock_manager.get_enhanced_summary.return_value = {"summary": "test summary"}
        mock_load.return_value = mock_manager

        response = test_client.get("/conversation/1/enhanced-summary")
        assert response.status_code == 200
        assert response.json() == {"summary": "test summary"}


# Test for streaming model response moved to test_services.py


# Test for Ollama error handling moved to test_services.py


# Test for tool execution moved to test_services.py


# Test for tool not found moved to test_services.py


# Test for tool execution error moved to test_services.py


# Test for successful tool execution moved to test_services.py


# Test for chat orchestration error moved to test_services.py


# Test for chat iteration error moved to test_services.py


def test_invoke_no_messages_error(test_client):
    """Test invoke endpoint with no messages."""
    payload = {"id": 0, "title": "Test", "model": "test-model", "messages": []}

    response = test_client.post("/invoke", json=payload)
    assert response.status_code == 400
    assert "Query contains no messages" in response.json()["detail"]


def test_invoke_conversation_not_found(test_client):
    """Test invoke endpoint with non-existent conversation ID."""
    with patch(
        "src.agent.my_local_agent.route.ConversationManager.load_existing"
    ) as mock_load:
        mock_load.return_value = None

        payload = {
            "id": 999,
            "title": "Test",
            "model": "test-model",
            "messages": [{"role": "user", "content": "test", "model": "test-model"}],
        }

        response = test_client.post("/invoke", json=payload)
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]


@patch(
    "src.agent.my_local_agent.route.chat_orchestration_service.stream_chat_with_tools"
)
def test_invoke_streaming_response_error(
    mock_stream, test_client, mock_conversation_manager
):
    """Test invoke endpoint streaming response creation error."""
    mock_stream.side_effect = Exception("Streaming error")

    payload = {
        "id": 0,
        "title": "Test",
        "model": "test-model",
        "messages": [{"role": "user", "content": "test", "model": "test-model"}],
    }

    response = test_client.post("/invoke", json=payload)
    assert response.status_code == 200

    # Should return error response in streaming format
    response_text = response.text
    assert "Response creation error" in response_text


def test_invoke_with_thinking_model(test_client, mock_conversation_manager):
    """Test invoke with thinking effort for specific model."""
    with patch(
        "src.agent.my_local_agent.route.chat_orchestration_service.stream_chat_with_tools"
    ) as mock_stream:

        async def mock_generator(*args, **kwargs):
            yield json.dumps({"stage": "metadata", "conversation_id": 1}) + "\n"
            yield json.dumps({"stage": "thinking", "response": "thinking..."}) + "\n"
            yield json.dumps({"stage": "content", "response": "response"}) + "\n"

        mock_stream.return_value = mock_generator()

        payload = {
            "id": 0,
            "title": "Test",
            "model": "gpt-oss:20b",  # Model that supports thinking
            "messages": [{"role": "user", "content": "test", "model": "gpt-oss:20b"}],
        }

        response = test_client.post("/invoke", json=payload)
        assert response.status_code == 200
        assert "thinking" in response.text


def test_app_lifespan_startup_and_shutdown():
    """Test application lifespan startup and shutdown."""
    with patch("src.agent.my_local_agent.route.DatabaseManager") as mock_db:
        mock_db_instance = MagicMock()
        mock_db.return_value.__enter__ = MagicMock(return_value=mock_db_instance)
        mock_db.return_value.__exit__ = MagicMock(return_value=None)

        # Test that we can create a test client (triggers lifespan)
        with TestClient(app):
            # Verify database initialization was called during lifespan
            mock_db.assert_called_once()
            mock_db_instance.create_init_tables.assert_called_once()
