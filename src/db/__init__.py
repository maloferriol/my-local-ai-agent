# import logging.config
# from ..loggers.logging_config import LOGGING_CONFIG # Note the relative import



import logging.config
from loggers.logging_config import LOGGING_CONFIG # Note the relative import

# Apply the logging configuration
logging.config.dictConfig(LOGGING_CONFIG)