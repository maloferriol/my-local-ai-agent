import os
from pathlib import Path

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.resources import Resource

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
    OTLPLogExporter,
)
from opentelemetry.semconv.attributes import service_attributes

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# Get the path to the project root
# This ensures log files are created in a consistent location
project_root = Path(__file__).resolve().parent.parent

# Define the paths for your log files
log_dir = project_root / "logs"
os.makedirs(log_dir, exist_ok=True)
app_log_path = log_dir / "app.log"
conversations_log_path = log_dir / "conversations.log"
db_sqlite_log_path = log_dir / "db_sqlite.log"
tools_log_path = log_dir / "tools.log"


resource = Resource.create(
    {
        service_attributes.SERVICE_NAME: "my-local-ai-agent",
        service_attributes.SERVICE_VERSION: "1.0.0",
    }
)

# Set up logging
log_provider = LoggerProvider(resource=resource)
otlp_log_exporter = OTLPLogExporter(
    endpoint="http://otel-collector:4317", insecure=True
)
log_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
set_logger_provider(log_provider)


# Set up the OTLP exporter and tracer provider
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "opentelemetry_handler": {
            "class": "opentelemetry.sdk._logs.LoggingHandler",
            "level": "DEBUG",
            "logger_provider": log_provider,
        },
        "app_file_handler": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": app_log_path,
            "level": "DEBUG",
        },
        "conversations_file_handler": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": conversations_log_path,
            "level": "DEBUG",
        },
        "db_sqlite_file_handler": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": db_sqlite_log_path,
            "level": "DEBUG",
        },
        "tools_file_handler": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": tools_log_path,
            "level": "DEBUG",
        },
    },
    "root": {
        "handlers": ["app_file_handler", "opentelemetry_handler"],
        "level": "DEBUG",
    },
    "loggers": {
        "conversations_logger": {
            "handlers": ["conversations_file_handler"],
            "level": "DEBUG",
        },
        "db_sqlite_logger": {
            "handlers": ["db_sqlite_file_handler"],
            "level": "DEBUG",
        },
        "tools_logger": {
            "handlers": ["tools_file_handler"],
            "level": "DEBUG",
        },
    },
}
