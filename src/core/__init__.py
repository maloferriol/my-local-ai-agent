"""
Core package containing the main AI agent logic and conversation management.
"""

# import logging.config

# from loggers.logging_config import LOGGING_CONFIG

from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry._logs import set_logger_provider


provider = LoggerProvider()
processor = BatchLogRecordProcessor(ConsoleLogExporter())
provider.add_log_record_processor(processor)
# Sets the global default logger provider
set_logger_provider(provider)

# Apply the logging configuration
# logging.config.dictConfig(LOGGING_CONFIG)
