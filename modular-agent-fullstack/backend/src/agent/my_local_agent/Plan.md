# Plan.md

This document outlines the plan to create a unit test suite for the `ConversationManager` class.

## 1. Goals

The primary goal is to develop a comprehensive set of unit tests for the `ConversationManager` class located in `modular-agent-fullstack/backend/src/agent/my_local_agent/conversation.py`. This will ensure the class is reliable, and its behavior is well-documented through tests, making future refactoring safer.

## 2. Requirements

*   **Testing Framework:** All tests will be written using `pytest`.
*   **Test Client:** For future integration tests, FastAPI's `TestClient` will be used, not Flask's.
*   **Scope:** Testing will be strictly limited to the `ConversationManager` class.
*   **Test Isolation:** Tests must be independent. A test-specific in-memory SQLite database will be used for each test function to prevent side effects.
*   **Fixtures:** `pytest` fixtures will be used to provide a clean application context and database connection for tests.
*   **Deliverables:**
    1.  A new Python file containing the `pytest` tests for `ConversationManager`.
    2.  Suggestions for updating `GEMINI.md` to include guidelines on creating unit tests.

## 3. High-Level Tasks & Test Cases

This section breaks down the work into concrete tasks and lists the specific test cases we will implement for the `ConversationManager`.

### Task 1: Test Environment Setup

1.  **Create Test Directory:** Create a `tests/` directory in the `backend/` root.
2.  **Create Test File:** Inside `tests/`, create a new file named `test_conversation_manager.py`.
3.  **Configure Pytest:** Create a `pytest.ini` file in the `backend/` root to configure the Python path, ensuring that `pytest` can find the application modules.

### Task 2: Implement Pytest Fixtures

We will create the following fixtures in `test_conversation_manager.py` to ensure tests are isolated and easy to set up:

*   `db_manager_fixture`:
    *   Sets up an in-memory SQLite database (`:memory:`) for each test function.
    *   Creates the necessary `conversations` and `messages` tables.
    *   Yields a `DatabaseManager` instance.
    *   Cleans up the database connection after the test.
*   `conversation_manager_fixture`:
    *   Depends on the `db_manager_fixture`.
    *   Initializes and yields a `ConversationManager` instance for each test.

### Task 3: Write Unit Tests

We will write the following test functions to cover the public methods of `ConversationManager`:

| Method to Test              | Test Case Description                                                              |
| --------------------------- | ---------------------------------------------------------------------------------- |
| `start_new_conversation`    | Verify it creates a conversation in the DB and returns a valid ID.                 |
| `add_user_message`          | Verify it adds a user message to the current conversation and saves it to the DB.  |
| `add_assistant_message`     | Verify it adds an assistant message and saves it to the DB.                        |
| `add_tool_message`          | Verify it adds a tool message and saves it to the DB.                              |
| `load_conversation`         | Verify it correctly loads an existing conversation and all its messages from the DB. |
| `load_conversation`         | Verify it returns `None` when trying to load a non-existent conversation ID.       |
| `add_*_message` (any)       | Verify it raises a `RuntimeError` if no conversation has been started.             |
| `get_current_conversation`  | Verify it returns the correct `Conversation` object.                               |
| `export_conversation`       | Verify it returns a correct dictionary representation of the conversation.         |
| `update_conversation_title` | Verify it updates the title in the object.                                         |

## 4. Milestones

1.  **M1: Environment and Fixture Setup:** Complete Task 1 and Task 2. The test environment will be ready, and fixtures for the database and conversation manager will be implemented.
2.  **M2: Core Functionality Tests:** Implement tests for the primary methods: `start_new_conversation`, `add_*_message`, and `load_conversation`.
3.  **M3: Helper Method Tests:** Implement tests for the remaining helper methods like `get_current_conversation`, `export_conversation`, and `update_conversation_title`.
4.  **M4: Documentation Update:** Provide the final suggestions for updating `GEMINI.md`.

## 5. Dependencies

*   **`pytest`:** The testing framework used for writing and running tests.
*   **Application Modules:** The tests will depend on the existing `ConversationManager`, `DatabaseManager`, `Conversation`, and `ChatMessage` classes.

## 6. Risks and Mitigations

*   **Risk:** The `DatabaseManager` might have hidden state or dependencies that complicate isolated testing.
    *   **Mitigation:** The `db_manager_fixture` will use an in-memory SQLite database (`:memory:`) for each test function. This ensures a completely clean slate for every test, preventing interference.
*   **Risk:** Future changes to the `Conversation` or `ChatMessage` data classes could break tests.
    *   **Mitigation:** This is an expected outcome and a primary benefit of having tests. They will act as a safety net, immediately highlighting any breaking changes and ensuring that all related logic is updated accordingly.

## 7. Suggestions for GEMINI.md

To incorporate testing best practices into the project's development guidelines, the following section should be added to `GEMINI.md`.

---

### Unit & Integration Testing

Writing tests is a crucial part of maintaining code quality and ensuring stability.

#### General Principles

- **Framework**: All tests must be written using `pytest`.
- **Location**: Tests for a module located at `src/path/to/my_module.py` should be placed in `tests/path/to/test_my_module.py`.
- **Test Isolation**: Tests must be independent. Each test should run in a clean environment and not depend on the state left by a previous test.

#### Unit Testing

- **Fixtures**: Use `pytest` fixtures to manage setup and teardown of resources like database connections or class instances. For resources used across multiple test files, define fixtures in a central `tests/conftest.py`.
- **Mocking**: Isolate the unit under test by mocking external dependencies (e.g., API calls, database interactions) using `unittest.mock`.
- **Assertions**: Use clear and simple `assert` statements. A test should ideally test one specific behavior.

#### Integration Testing (FastAPI)

- **Test Client**: Use FastAPI's `TestClient` for testing API endpoints. The client simulates HTTP requests to your application.
- **Database**: Integration tests should run against a dedicated test database (in-memory or temporary file) to avoid polluting the development database. Use fixtures to manage the database lifecycle.

#### Example Fixture

```python
# In tests/conftest.py or a specific test file
import pytest
from agent.my_local_agent.db import DatabaseManager

@pytest.fixture(scope="function")
def test_db_manager():
    """
    Pytest fixture to set up an in-memory SQLite database for a single test function.
    """
    # Use :memory: for a clean, in-memory database for each test
    db_manager = DatabaseManager(db_file=":memory:")
    db_manager.connect()
    db_manager.create_init_tables()
    yield db_manager
    db_manager.close()
```
---
