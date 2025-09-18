"""
Unit tests for database/db.py module.

Tests database manager functionality including connection handling,
table operations, error handling, and environment configuration.
"""

import os
import pytest
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.database.db import (
    DatabaseManager,
    DatabaseUtils,
    get_default_db_file,
    default_db_file,
    ERROR_CONNECTION_MESSAGE,
)


class TestGetDefaultDbFile:
    """Test get_default_db_file function behavior under different conditions."""

    def test_get_default_db_file_testing_mode(self):
        """Test that testing mode returns temporary database file."""
        with patch.dict(os.environ, {"TESTING": "true"}):
            with patch.dict(os.environ, {}, clear=True):
                os.environ["TESTING"] = "true"
                # Clear any existing TEST_DB_FILE to force creation
                if "TEST_DB_FILE" in os.environ:
                    del os.environ["TEST_DB_FILE"]

                db_file = get_default_db_file()
                assert db_file.endswith(".db")
                assert "test_" in db_file

                # Should reuse the same file path
                db_file2 = get_default_db_file()
                assert db_file == db_file2

    def test_get_default_db_file_pytest_mode(self):
        """Test that pytest mode returns temporary database file."""
        with patch.dict(os.environ, {"PYTEST_CURRENT_TEST": "test_something"}):
            with patch.dict(os.environ, {}, clear=True):
                os.environ["PYTEST_CURRENT_TEST"] = "test_something"
                if "TEST_DB_FILE" in os.environ:
                    del os.environ["TEST_DB_FILE"]

                db_file = get_default_db_file()
                assert db_file.endswith(".db")

    def test_get_default_db_file_database_url_sqlite3(self):
        """Test DATABASE_URL with sqlite:/// prefix."""
        test_path = "/tmp/test.db"
        with patch.dict(
            os.environ, {"DATABASE_URL": f"sqlite:///{test_path}"}, clear=True
        ):
            db_file = get_default_db_file()
            assert db_file == test_path

    def test_get_default_db_file_database_url_sqlite2(self):
        """Test DATABASE_URL with sqlite:// prefix."""
        test_path = "/tmp/test.db"
        with patch.dict(
            os.environ, {"DATABASE_URL": f"sqlite://{test_path}"}, clear=True
        ):
            db_file = get_default_db_file()
            assert db_file == "tmp/test.db"  # sqlite:// prefix removes the first /

    def test_get_default_db_file_database_url_other(self):
        """Test DATABASE_URL with non-SQLite URL falls back to default."""
        with patch.dict(
            os.environ, {"DATABASE_URL": "postgresql://localhost/db"}, clear=True
        ):
            with patch("src.database.db.Path") as mock_path_class:
                with patch("src.database.db.os.makedirs") as mock_makedirs:
                    mock_path = MagicMock()
                    mock_path.resolve.return_value = Path("/fake/project/root")
                    mock_path_class.return_value = mock_path
                    mock_path_class.__file__ = "/fake/project/root/src/database/db.py"

                    db_file = get_default_db_file()
                    assert str(db_file).endswith("conversation_data.db")
                    mock_makedirs.assert_called_once()

    def test_get_default_db_file_default_path(self):
        """Test default path creation when no environment variables are set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("src.database.db.Path") as mock_path_class:
                with patch("src.database.db.os.makedirs") as mock_makedirs:
                    mock_path = MagicMock()
                    mock_path.resolve.return_value = Path("/fake/project/root")
                    mock_path_class.return_value = mock_path
                    mock_path_class.__file__ = "/fake/project/root/src/database/db.py"

                    db_file = get_default_db_file()
                    assert str(db_file).endswith("conversation_data.db")
                    mock_makedirs.assert_called_once()


class TestDatabaseManager:
    """Test DatabaseManager class functionality."""

    @pytest.fixture
    def temp_db_file(self):
        """Create a temporary database file for testing."""
        fd, temp_file = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield temp_file
        if os.path.exists(temp_file):
            os.unlink(temp_file)

    @pytest.fixture
    def db_manager(self, temp_db_file):
        """Create a DatabaseManager instance with temporary database."""
        return DatabaseManager(db_file=temp_db_file)

    def test_init(self, temp_db_file):
        """Test DatabaseManager initialization."""
        db_manager = DatabaseManager(db_file=temp_db_file)
        assert db_manager.db_file == temp_db_file
        assert db_manager.conn is None
        assert db_manager.cursor is None

    def test_context_manager_testing_mode(self, temp_db_file):
        """Test context manager in testing mode."""
        with patch.dict(os.environ, {"TESTING": "true"}):
            with DatabaseManager(db_file=temp_db_file) as db:
                assert db.conn is not None
                assert db.cursor is not None
        # Connection should be closed after exiting context

    def test_context_manager_normal_mode(self, temp_db_file):
        """Test context manager in normal mode."""
        with patch.dict(os.environ, {}, clear=True):
            with DatabaseManager(db_file=temp_db_file) as db:
                assert db.conn is not None
                assert db.cursor is not None

    def test_connect_success(self, db_manager):
        """Test successful database connection."""
        db_manager.connect()
        assert db_manager.conn is not None
        assert db_manager.cursor is not None
        db_manager.close()

    def test_connect_pragma_error(self, db_manager):
        """Test connect method handles PRAGMA errors gracefully."""
        with patch.object(db_manager, "cursor") as mock_cursor:
            mock_cursor.execute.side_effect = [
                None,  # First PRAGMA succeeds
                Exception("PRAGMA not supported"),  # Second PRAGMA fails
            ]
            # Should not raise exception
            db_manager.connect()

    def test_connect_sqlite_error(self, temp_db_file):
        """Test connect method handles SQLite errors."""
        # Use an invalid path to trigger sqlite3.Error
        db_manager = DatabaseManager(db_file="/invalid/path/to/database.db")

        # This should not raise an exception due to error handling
        db_manager.connect()
        assert db_manager.conn is None

    def test_close_connection(self, db_manager):
        """Test closing database connection."""
        db_manager.connect()
        assert db_manager.conn is not None

        db_manager.close()
        assert db_manager.cursor is None

    def test_close_no_connection(self, db_manager):
        """Test closing when no connection exists."""
        assert db_manager.conn is None
        db_manager.close()  # Should not raise exception

    def test_create_table_success(self, db_manager):
        """Test successful table creation."""
        db_manager.connect()
        table_name = "test_table"
        schema = "id INTEGER PRIMARY KEY, name TEXT"

        db_manager.create_table(table_name, schema)

        # Verify table was created
        result = db_manager.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        assert result is not None
        db_manager.close()

    def test_create_table_no_connection(self, db_manager):
        """Test create_table raises error when not connected."""
        table_name = "test_table"
        schema = "id INTEGER PRIMARY KEY"

        # Should handle the error gracefully (logged but not raised)
        db_manager.create_table(table_name, schema)

    def test_create_table_sqlite_error(self, db_manager):
        """Test create_table handles SQLite errors."""
        db_manager.connect()

        # Use invalid SQL to trigger error
        with patch.object(
            db_manager.cursor, "execute", side_effect=sqlite3.Error("Invalid SQL")
        ):
            db_manager.create_table("test", "invalid sql")

        db_manager.close()

    def test_execute_query_success(self, db_manager):
        """Test successful query execution."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY, value TEXT")

        row_id = db_manager.execute_query(
            "INSERT INTO test_table (value) VALUES (?)", ("test_value",)
        )

        assert row_id is not None
        db_manager.close()

    def test_execute_query_no_connection(self, db_manager):
        """Test execute_query raises error when not connected."""
        import re

        with pytest.raises(sqlite3.Error, match=re.escape(ERROR_CONNECTION_MESSAGE)):
            db_manager.execute_query("SELECT 1")

    def test_execute_query_sqlite_error(self, db_manager):
        """Test execute_query handles SQLite errors."""
        db_manager.connect()

        with pytest.raises(sqlite3.Error):
            db_manager.execute_query("INVALID SQL")

        db_manager.close()

    def test_execute_query_general_error(self, db_manager):
        """Test execute_query handles general exceptions."""
        db_manager.connect()

        with patch.object(
            db_manager.cursor, "execute", side_effect=ValueError("Test error")
        ):
            with pytest.raises(ValueError):
                db_manager.execute_query("SELECT 1")

        db_manager.close()

    def test_fetch_all_success(self, db_manager):
        """Test successful fetch_all operation."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY, value TEXT")
        db_manager.execute_query(
            "INSERT INTO test_table (value) VALUES (?)", ("test1",)
        )
        db_manager.execute_query(
            "INSERT INTO test_table (value) VALUES (?)", ("test2",)
        )

        results = db_manager.fetch_all("SELECT * FROM test_table ORDER BY id")

        assert len(results) == 2
        assert results[0]["value"] == "test1"
        assert results[1]["value"] == "test2"
        db_manager.close()

    def test_fetch_all_empty_result(self, db_manager):
        """Test fetch_all with no results."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY, value TEXT")

        results = db_manager.fetch_all("SELECT * FROM test_table")

        assert results == []
        db_manager.close()

    def test_fetch_all_no_connection(self, db_manager):
        """Test fetch_all with no connection."""
        results = db_manager.fetch_all("SELECT 1")
        assert results == []

    def test_fetch_all_sqlite_error(self, db_manager):
        """Test fetch_all handles SQLite errors."""
        db_manager.connect()

        results = db_manager.fetch_all("INVALID SQL")
        assert results == []

        db_manager.close()

    def test_fetch_one_success(self, db_manager):
        """Test successful fetch_one operation."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY, value TEXT")
        db_manager.execute_query(
            "INSERT INTO test_table (value) VALUES (?)", ("test_value",)
        )

        result = db_manager.fetch_one("SELECT * FROM test_table WHERE id = 1")

        assert result is not None
        assert result["value"] == "test_value"
        db_manager.close()

    def test_fetch_one_no_result(self, db_manager):
        """Test fetch_one with no result."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY, value TEXT")

        result = db_manager.fetch_one("SELECT * FROM test_table WHERE id = 999")

        assert result is None
        db_manager.close()

    def test_fetch_one_no_connection(self, db_manager):
        """Test fetch_one with no connection."""
        result = db_manager.fetch_one("SELECT 1")
        assert result is None

    def test_fetch_one_sqlite_error(self, db_manager):
        """Test fetch_one handles SQLite errors."""
        db_manager.connect()

        result = db_manager.fetch_one("INVALID SQL")
        assert result is None

        db_manager.close()

    def test_create_init_tables_success(self, db_manager):
        """Test successful creation of initial tables."""
        db_manager.connect()
        db_manager.create_init_tables()

        # Verify both tables were created
        messages_table = db_manager.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        )
        conversations_table = db_manager.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
        )

        assert messages_table is not None
        assert conversations_table is not None
        db_manager.close()

    def test_create_init_tables_error(self, db_manager):
        """Test create_init_tables handles errors gracefully."""
        db_manager.connect()

        with patch.object(
            db_manager, "create_table", side_effect=Exception("Test error")
        ):
            # Should not raise exception due to error handling
            db_manager.create_init_tables()

        db_manager.close()

    def test_apply_schema_migrations_new_database(self, db_manager):
        """Test schema migrations on a new database."""
        db_manager.connect()
        db_manager.create_init_tables()

        # Should complete without errors
        assert db_manager.conn is not None
        db_manager.close()

    def test_apply_schema_migrations_sqlite_error(self, db_manager):
        """Test schema migrations handle SQLite errors."""
        db_manager.connect()

        with patch.object(
            db_manager,
            "_get_table_columns",
            side_effect=sqlite3.Error("Table not found"),
        ):
            # Should handle error gracefully
            db_manager.apply_schema_migrations()

        db_manager.close()

    def test_get_table_columns_success(self, db_manager):
        """Test _get_table_columns returns column information."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY, name TEXT")

        columns = db_manager._get_table_columns("test_table")

        assert len(columns) >= 2
        column_names = [col[1] for col in columns]
        assert "id" in column_names
        assert "name" in column_names
        db_manager.close()

    def test_get_table_columns_error(self, db_manager):
        """Test _get_table_columns handles errors."""
        db_manager.connect()

        columns = db_manager._get_table_columns("nonexistent_table")
        assert columns == []

        db_manager.close()

    def test_insert_message_success(self, db_manager):
        """Test successful message insertion."""
        db_manager.connect()
        db_manager.create_init_tables()

        # Create a conversation first
        conv_id = db_manager.create_conversation(title="Test Conversation")

        message_id = db_manager.insert_message(
            conversation_id=conv_id,
            step=1,
            role="user",
            content="Test message",
            confidence_score=0.95,
            token_count=10,
            processing_time_ms=100,
            metadata='{"test": true}',
            uuid="test-uuid",
        )

        assert message_id is not None
        db_manager.close()

    def test_insert_message_error(self, db_manager):
        """Test insert_message handles errors."""
        db_manager.connect()

        # Try to insert without creating tables first
        with patch.object(
            db_manager, "execute_query", side_effect=sqlite3.Error("Table not found")
        ):
            message_id = db_manager.insert_message(
                conversation_id=1, step=1, role="user", content="Test message"
            )
            assert message_id is None

        db_manager.close()

    def test_get_messages_success(self, db_manager):
        """Test successful message retrieval."""
        db_manager.connect()
        db_manager.create_init_tables()

        conv_id = db_manager.create_conversation(title="Test")
        db_manager.insert_message(conv_id, 1, "user", "Hello")
        db_manager.insert_message(conv_id, 2, "assistant", "Hi there")

        messages = db_manager.get_messages(conv_id)

        assert len(messages) == 2
        assert messages[0]["step"] == 1
        assert messages[1]["step"] == 2
        db_manager.close()

    def test_get_messages_error(self, db_manager):
        """Test get_messages handles errors."""
        db_manager.connect()

        with patch.object(db_manager, "fetch_all", side_effect=sqlite3.Error("Error")):
            messages = db_manager.get_messages(1)
            assert messages == []

        db_manager.close()

    def test_get_conversations_success(self, db_manager):
        """Test successful conversations retrieval."""
        db_manager.connect()
        db_manager.create_init_tables()

        db_manager.create_conversation(title="Conv1")
        db_manager.create_conversation(title="Conv2")

        conversations = db_manager.get_conversations(limit=10, offset=0)

        assert len(conversations) == 2
        db_manager.close()

    def test_get_conversations_error(self, db_manager):
        """Test get_conversations handles errors."""
        db_manager.connect()

        with patch.object(db_manager, "fetch_all", side_effect=sqlite3.Error("Error")):
            conversations = db_manager.get_conversations()
            assert conversations == []

        db_manager.close()

    def test_get_conversation_success(self, db_manager):
        """Test successful single conversation retrieval."""
        db_manager.connect()
        db_manager.create_init_tables()

        conv_id = db_manager.create_conversation(title="Test Conv")
        conversation = db_manager.get_conversation(conv_id)

        assert conversation is not None
        assert conversation["title"] == "Test Conv"
        db_manager.close()

    def test_get_conversation_error(self, db_manager):
        """Test get_conversation handles errors."""
        db_manager.connect()

        with patch.object(db_manager, "fetch_one", side_effect=sqlite3.Error("Error")):
            conversation = db_manager.get_conversation(1)
            assert conversation is None

        db_manager.close()

    def test_get_message_count_success(self, db_manager):
        """Test successful message count retrieval."""
        db_manager.connect()
        db_manager.create_init_tables()

        conv_id = db_manager.create_conversation(title="Test")
        db_manager.insert_message(conv_id, 1, "user", "Hello")
        db_manager.insert_message(conv_id, 2, "assistant", "Hi")

        count = db_manager.get_message_count(conv_id)

        assert count == 2
        db_manager.close()

    def test_get_message_count_error(self, db_manager):
        """Test get_message_count handles errors."""
        db_manager.connect()

        with patch.object(
            db_manager.cursor, "execute", side_effect=sqlite3.Error("Error")
        ):
            count = db_manager.get_message_count(1)
            assert count == 0

        db_manager.close()

    def test_drop_table_success(self, db_manager):
        """Test successful table dropping."""
        db_manager.connect()
        db_manager.create_table("test_table", "id INTEGER PRIMARY KEY")

        db_manager.drop_table("test_table")

        # Verify table was dropped
        result = db_manager.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
        )
        assert result is None
        db_manager.close()

    def test_drop_table_no_connection(self, db_manager):
        """Test drop_table with no connection."""
        # Should handle error gracefully
        db_manager.drop_table("test_table")

    def test_drop_table_error(self, db_manager):
        """Test drop_table handles errors."""
        db_manager.connect()

        with patch.object(
            db_manager.cursor, "execute", side_effect=sqlite3.Error("Error")
        ):
            # Should handle error gracefully
            db_manager.drop_table("test_table")

        db_manager.close()

    def test_create_conversation_success(self, db_manager):
        """Test successful conversation creation."""
        db_manager.connect()
        db_manager.create_init_tables()

        conv_id = db_manager.create_conversation(
            title="Test Conversation",
            model_name="gpt-4",
            system_prompt="You are helpful",
            temperature=0.8,
            max_tokens=1000,
            metadata='{"test": true}',
            uuid="test-uuid",
        )

        assert conv_id is not None

        # Verify conversation was created
        conv = db_manager.get_conversation(conv_id)
        assert conv["title"] == "Test Conversation"
        assert conv["model_name"] == "gpt-4"
        db_manager.close()

    def test_create_conversation_empty_title(self, db_manager):
        """Test conversation creation with empty title generates random title."""
        db_manager.connect()
        db_manager.create_init_tables()

        with patch.object(
            DatabaseUtils, "generate_random_name", return_value="random-title"
        ):
            conv_id = db_manager.create_conversation(title="")

            conv = db_manager.get_conversation(conv_id)
            assert conv["title"] == "random-title"

        db_manager.close()

    def test_create_conversation_sqlite_error(self, db_manager):
        """Test create_conversation handles SQLite errors."""
        db_manager.connect()

        with patch.object(
            db_manager, "execute_query", side_effect=sqlite3.Error("Error")
        ):
            with pytest.raises(sqlite3.Error):
                db_manager.create_conversation(title="Test")

        db_manager.close()

    def test_create_conversation_general_error(self, db_manager):
        """Test create_conversation handles general exceptions."""
        db_manager.connect()

        with patch.object(db_manager, "execute_query", side_effect=ValueError("Error")):
            with pytest.raises(ValueError):
                db_manager.create_conversation(title="Test")

        db_manager.close()


class TestDatabaseUtils:
    """Test DatabaseUtils class functionality."""

    def test_generate_random_name_default(self):
        """Test generate_random_name with default parameters."""
        utils = DatabaseUtils()

        with patch("nltk.download"):
            with patch(
                "nltk.corpus.words.words",
                return_value=["apple", "banana", "cherry", "date", "elderberry"],
            ):
                with patch("random.sample", return_value=["apple", "banana", "cherry"]):
                    name = utils.generate_random_name()
                    assert name == "apple-banana-cherry"

    def test_generate_random_name_custom_length(self):
        """Test generate_random_name with custom length."""
        utils = DatabaseUtils()

        with patch("nltk.download"):
            with patch(
                "nltk.corpus.words.words",
                return_value=["apple", "banana", "cherry", "date"],
            ):
                with patch("random.sample", return_value=["apple", "banana"]):
                    name = utils.generate_random_name(n=2)
                    assert name == "apple-banana"

    def test_generate_random_name_nltk_error(self):
        """Test generate_random_name handles NLTK errors."""
        utils = DatabaseUtils()

        with patch("nltk.download", side_effect=Exception("NLTK Error")):
            with pytest.raises(Exception):
                utils.generate_random_name()
