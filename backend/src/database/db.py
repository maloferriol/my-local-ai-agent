import os
from pathlib import Path

import sqlite3
import logging
from opentelemetry import trace

from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor

SQLite3Instrumentor().instrument()

tracer = trace.get_tracer(__name__)
# Get your logger instance for this module
logger = logging.getLogger("db_sqlite_logger")

project_root = Path(__file__).resolve().parent.parent.parent
databases_dir = project_root / "data"
os.makedirs(databases_dir, exist_ok=True)
default_db_file = databases_dir / "conversation_data.db"

ERROR_CONNECTION_MESSAGE = "Not connected to database. Call connect() first."


class DatabaseManager:
    @tracer.start_as_current_span("database__init__", kind=trace.SpanKind.INTERNAL)
    def __init__(self, db_file=default_db_file):
        self.db_file = db_file
        self.conn = None  # Connection object
        self.cursor = None  # Cursor object

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @tracer.start_as_current_span("connect_to_db", kind=trace.SpanKind.INTERNAL)
    def connect(self):
        try:
            self.conn = sqlite3.connect(
                self.db_file,
                timeout=5.0,
                check_same_thread=False,
            )
            self.cursor = self.conn.cursor()
            try:
                # Improve concurrency and reliability
                self.cursor.execute("PRAGMA journal_mode=WAL;")
                self.cursor.execute("PRAGMA synchronous=NORMAL;")
                self.cursor.execute("PRAGMA busy_timeout=5000;")
                self.cursor.execute("PRAGMA foreign_keys=ON;")
            except Exception:
                # Best-effort PRAGMA setup; continue even if not supported
                pass
            logger.info("Connected to database: %s", self.db_file)
        except sqlite3.Error as e:
            logger.error("Error connecting to database: %s", e)

    @tracer.start_as_current_span("close_db_connection", kind=trace.SpanKind.INTERNAL)
    def close(self):
        if self.conn:
            self.conn.close()
            self.cursor = None  # Reset cursor to None
            logger.info("Database connection closed: %s", self.db_file)

    @tracer.start_as_current_span("create_table", kind=trace.SpanKind.INTERNAL)
    def create_table(self, table_name: str, schema: str):
        """Creates a table with the given schema."""
        try:
            if self.conn is None:
                raise sqlite3.Error(ERROR_CONNECTION_MESSAGE)
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
            logger.info("Table created: %s", table_name)
        except sqlite3.Error as e:
            logger.error("Error creating table %s: %s", table_name, e)

    @tracer.start_as_current_span("execute_query", kind=trace.SpanKind.INTERNAL)
    def execute_query(self, query, params=()):
        """Executes a SQL query with optional parameters."""
        logger.debug("Executing query: %s with params: %s", query, params)
        try:
            if self.conn is None:
                raise sqlite3.Error(ERROR_CONNECTION_MESSAGE)
            self.cursor.execute(query, params)
            self.conn.commit()  # Commit changes after executing
            return self.cursor.lastrowid  # Returns the ID of the last inserted row
        except sqlite3.Error as e:
            logger.error("Error executing query: %s", e)
            print("[DB] Error executing query:", e)
            raise
            return None
        except Exception as e2:
            print("[DB] Error executing query:", e2)
            raise

    @tracer.start_as_current_span("fetch_all", kind=trace.SpanKind.INTERNAL)
    def fetch_all(self, query, params=()):
        """Fetches all rows from a query."""
        try:
            if self.conn is None:
                raise sqlite3.Error()
            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            if rows:
                columns = [description[0] for description in self.cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            return []
        except sqlite3.Error as e:
            logger.error("Error fetching data: %s", e)
            return []

    @tracer.start_as_current_span("fetch_one", kind=trace.SpanKind.INTERNAL)
    def fetch_one(self, query, params=()):
        """Fetches a single row from a query."""
        try:
            if self.conn is None:
                raise sqlite3.Error(ERROR_CONNECTION_MESSAGE)
            self.cursor.execute(query, params)
            row = self.cursor.fetchone()
            if row:
                # Convert tuple to dictionary
                columns = [description[0] for description in self.cursor.description]
                return dict(zip(columns, row))
            return None
        except sqlite3.Error as e:
            logger.error("Error fetching data: %s", e)
            return None

    @tracer.start_as_current_span("create_init_tables", kind=trace.SpanKind.INTERNAL)
    def create_init_tables(self):
        try:
            self.create_table(
                "messages",
                """
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    step INTEGER,
                    role TEXT,
                    content TEXT,
                    thinking TEXT,
                    tool_name TEXT,
                    tool_calls TEXT,
                    tool_results TEXT,
                    model TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence_score REAL,
                    token_count INTEGER,
                    processing_time_ms INTEGER,
                    metadata TEXT,
                    parent_message_id INTEGER REFERENCES messages(id),
                    uuid TEXT
                """,
            )

            self.create_table(
                "conversations",
                """
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    model_name TEXT,
                    system_prompt TEXT,
                    temperature REAL DEFAULT 0.7,
                    max_tokens INTEGER,
                    metadata TEXT,
                    uuid TEXT
                """,
            )
            
            # Apply backward-compatible schema updates
            self.apply_schema_migrations()
        except Exception as e:
            logger.exception("Error creating initial tables: %s", e)

    @tracer.start_as_current_span("apply_schema_migrations", kind=trace.SpanKind.INTERNAL)
    def apply_schema_migrations(self):
        """Apply backward-compatible schema migrations for existing databases."""
        try:
            # Get existing columns for conversations table
            existing_conv_columns = self._get_table_columns("conversations")
            conv_columns = {col[1] for col in existing_conv_columns}
            
            # Add new conversation columns if they don't exist
            new_conv_columns = [
                ("model_name", "TEXT"),
                ("system_prompt", "TEXT"), 
                ("temperature", "REAL DEFAULT 0.7"),
                ("max_tokens", "INTEGER"),
                ("metadata", "TEXT"),
                ("uuid", "TEXT")
            ]
            
            for col_name, col_type in new_conv_columns:
                if col_name not in conv_columns:
                    self.cursor.execute(f"ALTER TABLE conversations ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column {col_name} to conversations table")

            # Get existing columns for messages table  
            existing_msg_columns = self._get_table_columns("messages")
            msg_columns = {col[1] for col in existing_msg_columns}
            
            # Add new message columns if they don't exist
            new_msg_columns = [
                ("confidence_score", "REAL"),
                ("token_count", "INTEGER"),
                ("processing_time_ms", "INTEGER"), 
                ("metadata", "TEXT"),
                ("parent_message_id", "INTEGER REFERENCES messages(id)"),
                ("uuid", "TEXT")
            ]
            
            for col_name, col_type in new_msg_columns:
                if col_name not in msg_columns:
                    self.cursor.execute(f"ALTER TABLE messages ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column {col_name} to messages table")
                    
            self.conn.commit()
            
        except sqlite3.Error as e:
            logger.warning(f"Schema migration error (may be expected for new databases): {e}")

    def _get_table_columns(self, table_name: str):
        """Get column information for a table."""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            return self.cursor.fetchall()
        except sqlite3.Error:
            return []

    @tracer.start_as_current_span("insert_message", kind=trace.SpanKind.INTERNAL)
    def insert_message(
        self,
        conversation_id: int,
        step: int,
        role: str,
        content: str,
        thinking: str = "",
        tool_calls: str = "",
        tool_results: str = "",
        model: str = "",
        tool_name: str = "",
        # New Phase 1 parameters
        confidence_score: float = None,
        token_count: int = None,
        processing_time_ms: int = None,
        metadata: str = "",
        parent_message_id: int = None,
        uuid: str = None,
    ):
        """Inserts a message into the messages table."""
        try:
            # Get the current span from the context
            current_span = trace.get_current_span()
            current_span.set_attribute("db.conversation_id", conversation_id)
            current_span.set_attribute("db.step", step)
            current_span.set_attribute("db.role", role)
            current_span.set_attribute("db.content", content)
            current_span.set_attribute("db.thinking", thinking)
            current_span.set_attribute("db.tool_name", tool_name)
            current_span.set_attribute("db.tool_calls", tool_calls)
            current_span.set_attribute("db.tool_results", tool_results)
            current_span.set_attribute("db.model", model)
            current_span.set_attribute("db.name", default_db_file)

            message_id = self.execute_query(
                """
                INSERT INTO messages (
                    conversation_id,
                    step,
                    role,
                    content,
                    thinking,
                    tool_name,
                    tool_calls,
                    tool_results,
                    model,
                    confidence_score,
                    token_count,
                    processing_time_ms,
                    metadata,
                    parent_message_id,
                    uuid
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    conversation_id,
                    step,
                    role,
                    content,
                    thinking,
                    tool_name,
                    tool_calls,
                    tool_results,
                    model,
                    confidence_score,
                    token_count,
                    processing_time_ms,
                    metadata,
                    parent_message_id,
                    uuid,
                ),
            )
            logger.info(
                "Inserted message for conversation_id %d at step %d",
                conversation_id,
                step,
            )
            return message_id
        except sqlite3.Error as e:
            logger.error("Error inserting message: %s", e)
            return None

    @tracer.start_as_current_span("get_messages", kind=trace.SpanKind.INTERNAL)
    def get_messages(self, conversation_id: int):
        """Fetches messages for a specific conversation."""
        try:
            return self.fetch_all(
                """
                SELECT *
                FROM messages
                WHERE conversation_id = ?
                ORDER BY step ASC
                """,
                (conversation_id,),
            )
        except sqlite3.Error as e:
            logger.error(
                "Error fetching messages for conversation_id %d: %s", conversation_id, e
            )
            return []

    @tracer.start_as_current_span("get_conversations", kind=trace.SpanKind.INTERNAL)
    def get_conversations(self, limit: int = 10, offset: int = 0):
        """Fetches conversations with pagination."""
        try:
            return self.fetch_all(
                "SELECT * FROM conversations ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            )
        except sqlite3.Error as e:
            logger.error("Error fetching conversations with pagination: %s", e)
            return []

    @tracer.start_as_current_span("get_conversation", kind=trace.SpanKind.INTERNAL)
    def get_conversation(self, conversation_id: int):
        """Fetches a single conversation by its ID."""
        try:
            return self.fetch_one(
                "SELECT * FROM conversations WHERE id = ?",
                (conversation_id,),
            )
        except sqlite3.Error as e:
            logger.error("Error fetching conversation %d: %s", conversation_id, e)
            return None

    @tracer.start_as_current_span("get_message_count", kind=trace.SpanKind.INTERNAL)
    def get_message_count(self, conversation_id: int) -> int:
        """Fetches the number of messages for a specific conversation."""
        try:
            self.cursor.execute(
                "SELECT COUNT(id) FROM messages WHERE conversation_id = ?",
                (conversation_id,),
            )
            count = self.cursor.fetchone()[0]
            return count
        except sqlite3.Error as e:
            logger.error(
                "Error fetching message count for conversation_id %d: %s",
                conversation_id,
                e,
            )
            return 0

    @tracer.start_as_current_span("drop_table", kind=trace.SpanKind.INTERNAL)
    def drop_table(self, table_name: str):
        """Drops the specified table."""
        try:
            if self.conn is None:
                raise sqlite3.Error(ERROR_CONNECTION_MESSAGE)
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.commit()
            logger.info("Dropped table: %s", table_name)
        except sqlite3.Error as e:
            logger.error("Error dropping table %s: %s", table_name, e)

    @tracer.start_as_current_span("create_conversation", kind=trace.SpanKind.INTERNAL)
    def create_conversation(
        self,
        title: str = "",
        model_name: str = None,
        system_prompt: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        metadata: str = "",
        uuid: str = None,
    ) -> int:
        """Creates a new conversation and returns its ID."""
        try:
            random_title = (
                title if title != "" else DatabaseUtils.generate_random_name(3)
            )
            conversation_id = self.execute_query(
                """INSERT INTO conversations 
                   (title, model_name, system_prompt, temperature, max_tokens, metadata, uuid) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                (random_title, model_name, system_prompt, temperature, max_tokens, metadata, uuid)
            )
            logger.info("Created new conversation with ID: %s", conversation_id)
            logger.info("Created new conversation with title: %s", random_title)
            print("random_title", random_title)
            print("[DB] conv id", conversation_id)
            return conversation_id
        except sqlite3.Error as e:
            logger.error("Error creating conversation: %s", e)
            print("[DB] Error creating conversation:", e)
            raise
        except Exception as e:
            print("[DB] Error creating conversation:", e)
            raise


class DatabaseUtils:
    @tracer.start_as_current_span("generate_random_name", kind=trace.SpanKind.INTERNAL)
    def generate_random_name(self, n: int = 3) -> str:
        """
        Generates a random name by sampling n words from the nltk words corpus.

        Args:
        n (int): Number of words to sample. Default is 3.

        Returns:
        str: A random name consisting of n words in lowercase joined by hyphens.
        """
        import nltk

        nltk.download("words")
        from nltk.corpus import words
        from random import sample

        return "-".join(sample(words.words(), n)).lower()
