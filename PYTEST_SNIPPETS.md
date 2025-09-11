# Pytest Snippets & Test Configuration Guide

This guide collects the most frequently used patterns, fixtures, and helper snippets that are employed throughout the test‑suite of **my‑local‑ai‑agent**. It is written with two audiences in mind:

- **LLM coding agents** – so they can generate new tests that follow the same conventions.
- **Human developers** – so they can copy‑paste the snippets, adapt them to new tests, and understand the underlying rationale.

---

## 1. Project‑wide configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependency list, and test runner configuration. |
| `backend/pytest.ini` | Pytest options that apply to the backend package. |
| `PYTEST_CONFIGURATION.md` | High‑level description of the test strategy (this file). |

### 1.1 `pyproject.toml`

```toml
[tool.pytest.ini_options]
addopts = "--cov=backend/ --cov-report=term-missing"
```

`addopts` tells pytest to collect coverage for the backend package and to display missing lines in the terminal.

### 1.2 `backend/pytest.ini`

```ini
[pytest]
# Discover tests in the `tests` directory only
testpaths = tests
# Use the `pytest_cov` plugin for coverage reporting
addopts = --cov=backend --cov-report=html
```

## 2. Common fixtures

The test‑suite relies heavily on fixtures to provide a clean, isolated environment for each test. The following are the core fixtures that every new test should use.

### 2.1 `conftest.py`

```python
import pytest
from src.database.db import DatabaseManager

# Global in‑memory database manager used by all tests
@pytest.fixture(scope="session")
def db_manager() -> DatabaseManager:
    """Return a shared, in‑memory `DatabaseManager` instance."""
    return DatabaseManager(":memory:")

# Clean up after each test function
@pytest.fixture(scope="function", autouse=True)
def clean_db_manager(db_manager: DatabaseManager):
    """Drop all tables before and after each test to keep the state pristine."""
    db_manager.drop_all_tables()
    yield db_manager
    db_manager.drop_all_tables()
```

### 2.2 `managed_db_connection`

Used in `test_conversation_manager.py` to create a temporary database connection that is automatically closed.

```python
from contextlib import contextmanager
from src.database.db import DatabaseManager

@contextmanager
def managed_db_connection() -> DatabaseManager:
    db = DatabaseManager(":memory:")
    try:
        yield db
    finally:
        db.close()
```

## 3. Testing async streaming responses with FastAPI

Many endpoints in my‑local‑ai‑agent return streamed JSON lines. The following snippet demonstrates how to:

- Mock the external Ollama client (or any async generator).
- Patch the client into the route module.
- Invoke the endpoint with TestClient.
- Parse the streamed lines and assert on the embedded stages (metadata, content, tool_result, etc.).

Reusable code block – copy‑paste this into any new test module or notebook that drives the LLM‑agent.

```python
# ---------- REUSED CODE BEGIN ----------
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import json
import pytest
import os

# Mock env to avoid missing OLLAMA_URL
with patch.dict("os.environ", {"OLLAMA_URL": "http://localhost:11434"}):
    from src.app import app          # your FastAPI app
    # any other imports that depend on the env can go here

@pytest.fixture
def client():
    return TestClient(app)

# Generic helper to turn a list of dicts into a streaming async generator
def _async_stream(records):
    async def _gen():
        for rec in records:
            # Yield a message chunk followed by a “done” marker
            yield {"message": rec, "done": False}
            yield {"message": {}, "done": True}
    return _gen

# Example test that uses the helper to mock a streaming response
def test_invoke_endpoint_with_mock(client):
    # 1️⃣ Arrange: create a fake stream that the LLM would return
    fake_stream = _async_stream([
        {"content": "Hello! How can I help you?", "tool_calls": []},
        {"content": "", "tool_calls": []}
    ])

    # 2️⃣ Patch the Ollama client in the route module
    with patch("src.agent.my_local_agent.route.ollama_client") as mock_client:
        mock_client.chat = AsyncMock(side_effect=fake_stream)

        # 3️⃣ Send a POST that would trigger the stream
        payload = {
            "id": 0,
            "title": "Test",
            "model": "gpt-oss:20b",
            "messages": [
                {"role": "user", "content": "Hi!", "model": "gpt-oss:20b"}
            ]
        }
        resp = client.post("/agent/my_local_agent/invoke", json=payload)

        # 4️⃣ Verify HTTP level
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/plain; charset=utf-8"

        # 5️⃣ Verify the streamed lines
        lines = [l for l in resp.text.split("\n") if l.strip()]
        parsed = [json.loads(l) for l in lines]

        # The first line should be metadata (the example test uses a
        # “metadata” stage; adjust if your implementation differs)
        metadata = [p for p in parsed if p.get("stage") == "metadata"]
        assert metadata, "Missing metadata stage"

        # All subsequent lines that are not the final empty line should be
        # content, tool_result, or finalize_answer etc.
        content_lines = [p for p in parsed if p.get("stage") in ("content", "tool_result")]
        assert content_lines, "No content produced by the mock stream"

# ---------- REUSED CODE END ----------
```

What the snippet covers

- AsyncMock + side_effect = async streaming mock.
- patch targets the exact import path inside the route module.
- TestClient sends a real HTTP request.
- The response text is split by newlines, parsed as JSON, and inspected for the expected stage values.

## 4. Core test patterns

### 4.1 Creating a new conversation

```python
# Arrange
conversation_manager = ConversationManager.create_new(title="Test", model="test-model")

# Act
current = conversation_manager.get_current_conversation()

# Assert
assert current.title == "Test"
assert current.model == "test-model"
```

### 4.2 Adding messages

```python
# User message
msg = conversation_manager.add_user_message(content="Hello", model="test-model")
assert msg.role == Role.USER

# Assistant message with tool calls
assistant_msg = conversation_manager.add_assistant_message(
    content="Response",
    thinking="Thinking...",
    model="assistant-model",
    tool_calls=[{"function": {"name": "get_weather", "arguments": {"city": "London"}}}]
)
assert assistant_msg.role == Role.ASSISTANT
```

### 4.3 Database assertions

```python
# After adding a message
messages = db_manager.get_messages(conversation_id)
assert len(messages) == expected_count
assert messages[-1]["role"] == "assistant"
```

### 4.4 Parametrized tests

```python
@pytest.mark.parametrize(
    "add_message_method, args",
    [
        ("add_user_message", {"content": "test"}),
        ("add_assistant_message", {"content": "test"}),
        ("add_tool_message", {"content": "test", "tool_name": "tool"}),
    ],
)
def test_add_message_without_active_conversation(add_message_method, args):
    manager = ConversationManager.create_new(title="Test", model="test")
    manager.current_conversation = None
    method = getattr(manager, add_message_method)
    with pytest.raises(RuntimeError, match="No active conversation"):
        method(**args)
```

## 5. Assertions helpers

| Helper | Purpose |
|--------|---------|
| `assert_message_equals(db_message, expected_dict)` | Compare a DB row dict to an expected dict. |
| `assert_conversation_state(convo, expected_count, expected_last_role)` | Verify message count and last role. |

Implement these helpers in `tests/helpers.py` and import them in your test files.

## 6. Running tests

```bash
# Run all tests with coverage (HTML report)
pytest --cov=backend/ --cov-report=html

# Run a single test file
pytest backend/tests/test_conversation_manager.py
```

## 7. Tips for LLM‑generated tests

- Always use fixtures – rely on `db_manager` or `clean_db_manager` to avoid side effects.
- Keep tests isolated – each test should create its own `ConversationManager` instance.
- Assert both in‑memory and DB state – verify that the object state matches what is persisted.
- Parametrize edge cases – use `pytest.mark.parametrize` to cover multiple scenarios in one test.
- Document intent – add a short docstring explaining what the test verifies.

## 8. Reference

- Pytest documentation – [Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- Pytest documentation – [Parametrize](https://docs.pytest.org/en/stable/parametrize.html)
- Coverage.py

Feel free to copy and adapt these snippets when writing new tests for the project. Happy testing!