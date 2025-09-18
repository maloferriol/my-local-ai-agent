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
    from src.agent.my_local_agent.route import (
        app,
        print_trace,
        _stream_model_response,
        _execute_tools,
        _stream_chat_with_tools_refactored,
    )


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
        mock_instance.get_current_conversation.return_value = MagicMock(
            id=1, model="test-model", messages=[]
        )
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


def test_stream_model_response_thinking_content():
    """Test streaming with thinking and content chunks."""

    async def run_test():
        with patch(
            "src.agent.my_local_agent.route.tracer.start_as_current_span"
        ) as mock_span:
            mock_span_instance = MagicMock()
            mock_span_instance.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span_instance.__exit__ = MagicMock(return_value=None)
            mock_span.return_value = mock_span_instance

            with patch("src.agent.my_local_agent.route.ollama_client") as mock_client:

                async def mock_chat_generator():
                    yield {
                        "message": {"thinking": "thinking...", "content": "part1"},
                        "done": False,
                    }
                    yield {"message": {"content": "part2"}, "done": False}
                    yield {"message": {}, "done": True}

                mock_client.chat = AsyncMock(return_value=mock_chat_generator())

                messages = [{"role": "user", "content": "test"}]
                generator = _stream_model_response(messages, "test-model", "low", None)

                results = []
                async for result in generator:
                    results.append(result)

                # Should have thinking and content chunks
                thinking_chunks = [r for r in results if r.get("stage") == "thinking"]
                content_chunks = [r for r in results if r.get("stage") == "content"]
                assert len(thinking_chunks) > 0
                assert len(content_chunks) > 0

    anyio.run(run_test)


def test_stream_model_response_ollama_error():
    """Test Ollama client error handling in streaming."""

    async def run_test():
        with patch(
            "src.agent.my_local_agent.route.tracer.start_as_current_span"
        ) as mock_span:
            mock_span_instance = MagicMock()
            mock_span_instance.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span_instance.__exit__ = MagicMock(return_value=None)
            mock_span.return_value = mock_span_instance

            with patch("src.agent.my_local_agent.route.ollama_client") as mock_client:
                mock_client.chat.side_effect = Exception("Ollama connection failed")

                messages = [{"role": "user", "content": "test"}]
                generator = _stream_model_response(messages, "test-model", None, None)

                with pytest.raises(Exception):
                    async for _ in generator:
                        pass

    anyio.run(run_test)


def test_execute_tools_missing_tool_name():
    """Test tool execution with missing tool name."""

    async def run_test():
        mock_conv_manager = MagicMock()
        tool_calls = [{"function": {}}]  # Missing 'name' field

        with patch(
            "src.agent.my_local_agent.route.tracer.start_as_current_span"
        ) as mock_span:
            mock_span_instance = MagicMock()
            mock_span_instance.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span_instance.__exit__ = MagicMock(return_value=None)
            mock_span.return_value = mock_span_instance

            generator = _execute_tools(tool_calls, mock_conv_manager)

            results = []
            async for result in generator:
                results.append(result)

            # Should handle missing tool name gracefully
            assert len(results) == 0

    anyio.run(run_test)


def test_execute_tools_tool_not_found():
    """Test tool execution when tool is not in registry."""

    async def run_test():
        mock_conv_manager = MagicMock()
        tool_calls = [{"function": {"name": "nonexistent_tool", "arguments": {}}}]

        with patch(
            "src.agent.my_local_agent.route.tracer.start_as_current_span"
        ) as mock_span:
            mock_span_instance = MagicMock()
            mock_span_instance.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span_instance.__exit__ = MagicMock(return_value=None)
            mock_span.return_value = mock_span_instance

            with patch("src.agent.my_local_agent.route.tool_registry") as mock_registry:
                mock_registry.get_tool_by_function_name.return_value = None

                generator = _execute_tools(tool_calls, mock_conv_manager)

                results = []
                async for result in generator:
                    results.append(result)

                # Should yield tool_error for nonexistent tool
                assert len(results) == 1
                assert results[0]["stage"] == "tool_error"
                assert "not found in registry" in results[0]["error"]

    anyio.run(run_test)


def test_execute_tools_execution_error():
    """Test tool execution error handling."""

    async def run_test():
        mock_conv_manager = MagicMock()
        tool_calls = [{"function": {"name": "failing_tool", "arguments": {}}}]

        with patch(
            "src.agent.my_local_agent.route.tracer.start_as_current_span"
        ) as mock_span:
            mock_span_instance = MagicMock()
            mock_span_instance.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span_instance.__exit__ = MagicMock(return_value=None)
            mock_span.return_value = mock_span_instance

            with patch("src.agent.my_local_agent.route.tool_registry") as mock_registry:
                mock_tool = MagicMock()
                mock_tool.current_version = "1.0"
                mock_tool.category = "test"
                mock_tool.status.value = "active"
                mock_tool.call_count = 5
                mock_tool.average_execution_time_ms = 100
                mock_registry.get_tool_by_function_name.return_value = mock_tool
                mock_registry.execute_tool_by_function_name.side_effect = Exception(
                    "Tool execution failed"
                )

                generator = _execute_tools(tool_calls, mock_conv_manager)

                results = []
                async for result in generator:
                    results.append(result)

                # Should yield tool_error for execution failure
                assert len(results) == 1
                assert results[0]["stage"] == "tool_error"
                assert "Tool execution failed" in results[0]["error"]

    anyio.run(run_test)


def test_execute_tools_successful_execution():
    """Test successful tool execution path."""

    async def run_test():
        mock_conv_manager = MagicMock()
        tool_calls = [
            {"function": {"name": "working_tool", "arguments": {"param": "value"}}}
        ]

        with patch(
            "src.agent.my_local_agent.route.tracer.start_as_current_span"
        ) as mock_span:
            mock_span_instance = MagicMock()
            mock_span_instance.__enter__ = MagicMock(return_value=mock_span_instance)
            mock_span_instance.__exit__ = MagicMock(return_value=None)
            mock_span.return_value = mock_span_instance

            with patch("src.agent.my_local_agent.route.tool_registry") as mock_registry:
                mock_tool = MagicMock()
                mock_tool.current_version = "1.0"
                mock_tool.category = "test"
                mock_tool.status.value = "active"
                mock_tool.call_count = 5
                mock_tool.average_execution_time_ms = 100
                mock_registry.get_tool_by_function_name.return_value = mock_tool
                mock_registry.execute_tool_by_function_name.return_value = "tool result"

                generator = _execute_tools(tool_calls, mock_conv_manager)

                results = []
                async for result in generator:
                    results.append(result)

                # Should yield successful tool result
                assert len(results) == 1
                assert results[0]["stage"] == "tool_result"
                assert results[0]["tool"] == "working_tool"
                assert results[0]["result"] == "tool result"

    anyio.run(run_test)


def test_stream_chat_with_tools_model_error():
    """Test chat orchestration with model streaming error."""

    async def run_test():
        mock_conv_manager = MagicMock()
        mock_conv_manager.get_current_conversation.return_value = MagicMock(
            id=1, messages=[]
        )

        with patch(
            "src.agent.my_local_agent.route._stream_model_response"
        ) as mock_stream:
            mock_stream.side_effect = Exception("Model streaming error")

            parent_ctx = MagicMock()
            generator = _stream_chat_with_tools_refactored(
                "test-model", mock_conv_manager, parent_ctx
            )

            results = []
            with pytest.raises(Exception):
                async for result in generator:
                    results.append(result)

    anyio.run(run_test)


def test_stream_chat_with_tools_iteration_error():
    """Test error in chat loop iteration."""

    async def run_test():
        mock_conv_manager = MagicMock()
        mock_conv_manager.get_current_conversation.return_value = MagicMock(
            id=1, messages=[]
        )

        async def failing_stream():
            yield {"stage": "content", "response": "test"}
            raise Exception("Stream iteration error")

        with patch(
            "src.agent.my_local_agent.route._stream_model_response"
        ) as mock_stream:
            mock_stream.return_value = failing_stream()

            parent_ctx = MagicMock()
            generator = _stream_chat_with_tools_refactored(
                "test-model", mock_conv_manager, parent_ctx
            )

            results = []
            try:
                async for result in generator:
                    if isinstance(result, str):
                        parsed = json.loads(result.strip())
                        results.append(parsed)
            except Exception:
                pass

            # Should contain error response
            error_responses = [r for r in results if r.get("stage") == "error"]
            assert len(error_responses) > 0

    anyio.run(run_test)


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


@patch("src.agent.my_local_agent.route._stream_chat_with_tools_refactored")
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
        "src.agent.my_local_agent.route._stream_chat_with_tools_refactored"
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
