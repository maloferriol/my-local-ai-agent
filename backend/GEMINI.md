# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Code Quality
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum

2. Code Style
    - PEP 8 naming (snake_case for functions/variables)
    - Class names in PascalCase
    - Constants in UPPER_SNAKE_CASE
    - Document with docstrings
    - Use f-strings for formatting

## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organsiation**: Balance file organization with simplicity - use an appropriate number of files for the project scale

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

## Python Tools

## Code Formatting

### Bash commands

After making any code changes, you must run the following command to ensure your code is formatted correctly:

- `black .`: Python code formatter
