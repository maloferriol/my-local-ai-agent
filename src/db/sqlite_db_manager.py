import sqlite3
import logging
from utils.database_utils import DatabaseUtils

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.semconv.attributes import service_attributes
from opentelemetry.sdk.resources import Resource

resource = Resource.create(
    {
        service_attributes.SERVICE_NAME: "my-local-ai-agent",
        service_attributes.SERVICE_VERSION: "1.0.0",
    }
)


# Set up the OTLP exporter and tracer provider
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

tracer = trace.get_tracer(__name__)
# Get your logger instance for this module
logger = logging.getLogger("db_sqlite_logger")

default_db_file = "data/conversation_data.db"


class DatabaseManager:
    def __init__(self, db_file=default_db_file):
        self.db_file = db_file
        self.conn = None  # Connection object
        self.cursor = None  # Cursor object

    @tracer.start_as_current_span("connect_to_db")
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.cursor = self.conn.cursor()
            logger.info("Connected to database: %s", self.db_file)
        except sqlite3.Error as e:
            logger.error("Error connecting to database: %s", e)

    @tracer.start_as_current_span("close_db_connection")
    def close(self):
        if self.conn:
            self.conn.close()
            self.cursor = None  # Reset cursor to None
            logger.info("Database connection closed: %s", self.db_file)

    @tracer.start_as_current_span("create_table")
    def create_table(self, table_name: str, schema: str):
        """Creates a table with the given schema."""
        try:
            if self.conn is None:
                raise sqlite3.Error("Not connected to database. Call connect() first.")
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({schema})")
            logger.info("Table created: %s", table_name)
        except sqlite3.Error as e:
            logger.error("Error creating table %s: %s", table_name, e)

    @tracer.start_as_current_span("execute_query")
    def execute_query(self, query, params=()):
        """Executes a SQL query with optional parameters."""
        logger.debug("Executing query: %s with params: %s", query, params)
        try:
            if self.conn is None:
                raise sqlite3.Error("Not connected to database. Call connect() first.")
            self.cursor.execute(query, params)
            self.conn.commit()  # Commit changes after executing
            return self.cursor.lastrowid  # Returns the ID of the last inserted row
        except sqlite3.Error as e:
            logger.error("Error executing query: %s", e)
            return None

    @tracer.start_as_current_span("fetch_all")
    def fetch_all(self, query, params=()):
        """Fetches all rows from a query."""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            logger.error("Error fetching data: %s", e)
            return []

    @tracer.start_as_current_span("create_init_tables")
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
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                """,
            )

            self.create_table(
                "conversations",
                """
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                """,
            )
        except Exception as e:
            logger.exception("Error creating initial tables: %s", e)

    @tracer.start_as_current_span("insert_message")
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
    ):
        """Inserts a message into the messages table."""
        try:
            self.execute_query(
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
                    model
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                ),
            )
            logger.info(
                "Inserted message for conversation_id %d at step %d",
                conversation_id,
                step,
            )
        except sqlite3.Error as e:
            logger.error("Error inserting message: %s", e)

    @tracer.start_as_current_span("get_messages")
    def get_messages(self, conversation_id: int, limit: int = 10):
        """Fetches messages for a specific conversation."""
        try:
            return self.fetch_all(
                """
                SELECT *
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (conversation_id, limit),
            )
        except sqlite3.Error as e:
            logger.error(
                "Error fetching messages for conversation_id %d: %s", conversation_id, e
            )
            return []

    @tracer.start_as_current_span("get_conversations")
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

    @tracer.start_as_current_span("drop_table")
    def drop_table(self, table_name: str):
        """Drops the specified table."""
        try:
            if self.conn is None:
                raise sqlite3.Error("Not connected to database. Call connect() first.")
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.commit()
            logger.info("Dropped table: %s", table_name)
        except sqlite3.Error as e:
            logger.error("Error dropping table %s: %s", table_name, e)

    @tracer.start_as_current_span("create_conversation")
    def create_conversation(
        self,
        title: str = "",
    ) -> int:
        """Creates a new conversation and returns its ID."""
        try:
            random_title = (
                title if title != "" else DatabaseUtils.generate_random_name(3)
            )
            conversation_id = self.execute_query(
                "INSERT INTO conversations (title) VALUES (?)", (random_title,)
            )
            logger.info("Created new conversation with ID: %s", conversation_id)
            logger.info("Created new conversation with title: %s", random_title)
            print(random_title)
            return conversation_id
        except sqlite3.Error as e:
            logger.error("Error creating conversation: %s", e)
            return None
