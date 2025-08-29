"""
CLI package for the AI agent application.
"""

import logging.config
from loggers.logging_config import LOGGING_CONFIG

# Apply the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)
