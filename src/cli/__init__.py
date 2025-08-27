"""
CLI package for the AI agent application.
"""

import logging.config
from loggers.logging_config import LOGGING_CONFIG

# from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
# from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
# from opentelemetry._logs import set_logger_provider, get_logger


# provider = LoggerProvider()
# processor = BatchLogRecordProcessor(ConsoleLogExporter())
# provider.add_log_record_processor(processor)
# # Sets the global default logger provider
# set_logger_provider(provider)

# Apply the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)