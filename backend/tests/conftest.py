"""
Global test configuration and fixtures.
"""

import os
import pytest
from contextlib import contextmanager

# Keep OpenTelemetry disabled for tests to avoid interference
os.environ["OTEL_SDK_DISABLED"] = "true"
# Ensure tests use in-memory database
os.environ["TESTING"] = "true"


def pytest_sessionstart(session):
    """Called after the Session object has been created."""
    # Clean up any existing test database file
    test_db_file = os.environ.get("TEST_DB_FILE")
    if test_db_file and os.path.exists(test_db_file):
        os.unlink(test_db_file)
    # Clear the environment variable to force creation of a new temp file
    os.environ.pop("TEST_DB_FILE", None)


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished."""
    # Clean up the temporary database file
    test_db_file = os.environ.get("TEST_DB_FILE")
    if test_db_file and os.path.exists(test_db_file):
        os.unlink(test_db_file)
    os.environ.pop("TEST_DB_FILE", None)


@contextmanager
def managed_db_connection(db_file=None):
    """
    Context manager for properly managing database connections in tests.
    Ensures connections are always closed to prevent ResourceWarnings.
    """
    from src.database.db import DatabaseManager

    # Use the default test database file if none specified
    db_manager = DatabaseManager(db_file=db_file) if db_file else DatabaseManager()
    try:
        db_manager.connect()
        db_manager.create_init_tables()
        yield db_manager
    finally:
        if db_manager.conn:
            db_manager.close()


@pytest.fixture(scope="function")
def clean_db_manager():
    """
    Provides a clean database manager that properly closes connections.
    Uses the shared test database file for consistency.
    """
    with managed_db_connection() as db_manager:
        yield db_manager
