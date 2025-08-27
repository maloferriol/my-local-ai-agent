import logging
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import set_logger_provider

<<<<<<< Updated upstream
# Get the path to the project root
# This ensures log files are created in a consistent location
project_root = Path(__file__).resolve().parent.parent.parent
=======

def setup_opentelemetry():
    """
    Set up OpenTelemetry logging to send logs to the OpenTelemetry collector.
    """
    # # Create resource with service information
    resource = Resource.create(
        # {
        #     ResourceAttributes.SERVICE_NAME: "my-local-ai-agent",
        #     ResourceAttributes.SERVICE_VERSION: "1.0.0",
        #     ResourceAttributes.DEPLOYMENT_ENVIRONMENT: "development",
        # }
    )

    # Set up logging
    log_provider = LoggerProvider(resource=resource)
    otlp_log_exporter = OTLPLogExporter(endpoint="http://localhost:4317", insecure=True)
    log_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_log_exporter))
    set_logger_provider(log_provider)

    # Create OpenTelemetry logging handler
    otel_handler = LoggingHandler(level=logging.INFO, logger_provider=log_provider)

    # Configure root logger to use OpenTelemetry
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(otel_handler)

    # Also add a console handler for local development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    return log_provider


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger configured with OpenTelemetry.
>>>>>>> Stashed changes

    Args:
        name: The name of the logger (usually __name__)

<<<<<<< Updated upstream
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
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
        "handlers": ["app_file_handler"],
        "level": "DEBUG",
    },
    "loggers": {
        "conversations_logger": {
            "handlers": ["conversations_file_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
        "db_sqlite_logger": {
            "handlers": ["db_sqlite_file_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
        "tools_logger": {
            "handlers": ["tools_file_handler"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
=======
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
>>>>>>> Stashed changes
