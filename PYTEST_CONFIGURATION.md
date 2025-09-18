# Pytest Configuration

This repository uses **pytest** as the test runner. The configuration is defined in `backend/tests/conftest.py` and is designed to:

1. **Disable OpenTelemetry** during tests to avoid noisy telemetry data.
2. **Use an in‑memory SQLite database** so tests run quickly and are isolated.
3. **Provide a clean database fixture** that automatically creates the required tables and closes the connection after each test.
4. **Clean up temporary database files** after the test session finishes.

## Environment Variables

| Variable | Purpose | Default / Notes |
|----------|---------|-----------------|
| `OTEL_SDK_DISABLED` | Disables the OpenTelemetry SDK. | Set to `"true"` in `conftest.py`. |
| `TESTING` | Signals that the code is running in a test environment. | Set to `"true"` in `conftest.py`. |
| `TEST_DB_FILE` | Path to a temporary SQLite file used by tests. | If unset, `DatabaseManager` creates an in‑memory database. |

## Key Fixtures

- **`clean_db_manager`** – A function‑scoped fixture that yields a `DatabaseManager` instance connected to a fresh test database. It uses the `managed_db_connection` context manager to ensure the connection is closed after the test.

## Lifecycle Hooks

- `pytest_sessionstart` – Runs before the test session starts. It removes any existing temporary database file and clears the `TEST_DB_FILE` environment variable to force a new file creation.
- `pytest_sessionfinish` – Runs after the test session ends. It cleans up the temporary database file and removes the environment variable.

## Usage

Simply run `pytest` from the repository root:

```bash
pytest --cov=backend/
```

The coverage report will be generated in the `htmlcov` directory.

## Extending the Configuration

If you need additional fixtures or hooks, add them to `conftest.py`. Pytest automatically discovers any `conftest.py` files in the test tree.

---

For more details on pytest configuration, see the [official documentation](https://docs.pytest.org/en/stable/).
