import os
from pathlib import Path


# from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
# from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
# from opentelemetry._logs import set_logger_provider, get_logger


# Get the path to the project root
# This ensures log files are created in a consistent location
project_root = Path(__file__).resolve().parent.parent.parent

# Define the paths for your log files
log_dir = project_root / "logs"
os.makedirs(log_dir, exist_ok=True)
app_log_path = log_dir / "app.log"
conversations_log_path = log_dir / "conversations.log"
db_sqlite_log_path = log_dir / "db_sqlite.log"
tools_log_path = log_dir / "tools.log"

# handler = LoggingHandler(level=logging.INFO, logger_provider=provider)
# logging.basicConfig(handlers=[handler], level=logging.INFO)

# logging.info("This is an OpenTelemetry log record!")


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
    },
    "handlers": {
        "opentelemetry_handler":{
            "class": "opentelemetry.sdk._logs.LoggingHandler",
            "level": "DEBUG",
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
