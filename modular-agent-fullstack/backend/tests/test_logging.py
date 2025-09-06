#!/usr/bin/env python3
"""
Simple test script to verify logging is working as expected.

Run with:
    python -m unittest tests/test_logging.py
"""

import logging
import unittest
from unittest import mock
from unittest.mock import Mock
import logging.config


class TestLogging(unittest.TestCase):

    @mock.patch("opentelemetry.exporter.otlp.proto.grpc._log_exporter.OTLPLogExporter")
    def test_root_logger_initialization(self, mock_otlp_exporter):

        mock_exporter_instance = Mock()
        mock_otlp_exporter.return_value = mock_exporter_instance

        # Now import your logging config - this will use the mocks
        # Import AFTER setting up mocks to ensure they're used

        from src.agent.my_local_agent.logging_config import LOGGING_CONFIG

        # Apply the logging configuration
        logging.config.dictConfig(LOGGING_CONFIG)

        # Instantiate the root logger
        # If calling getLogger with no arguments, it returns the root logger
        logger = logging.getLogger()

        root_handlers_names = ["app_file_handler", "opentelemetry_handler"]

        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, logging.Logger)

        # Assert that the logger is configured correctly
        assert logger.handlers is not None, "Logger is not configured correctly"
        assert logger.level == logging.DEBUG, "Logger level is not set to DEBUG"
        assert logger.name == "root", "Logger name is not 'root'"

        for handler in logger.handlers:
            assert (
                handler.name in root_handlers_names
            ), f"Unexpected handler: {handler.name}"

    @mock.patch("opentelemetry.exporter.otlp.proto.grpc._log_exporter.OTLPLogExporter")
    def test_conversations_logger_initialization(self, mock_otlp_exporter):

        mock_exporter_instance = Mock()
        mock_otlp_exporter.return_value = mock_exporter_instance

        # Now import your logging config - this will use the mocks
        # Import AFTER setting up mocks to ensure they're used
        import logging.config
        from src.agent.my_local_agent.logging_config import LOGGING_CONFIG

        # Apply the logging configuration
        logging.config.dictConfig(LOGGING_CONFIG)

        # Instantiate the conversations logger
        logger = logging.getLogger("conversations_logger")

        logger.debug("Testing conversations logger initialization")

        conversations_handlers_names = ["conversations_file_handler"]

        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, logging.Logger)

        # Assert that the logger is configured correctly
        assert logger.handlers is not None, "Logger is not configured correctly"
        assert logger.level == logging.DEBUG, "Logger level is not set to DEBUG"
        assert (
            logger.name == "conversations_logger"
        ), "Logger name is not 'conversations_logger'"

        for handler in logger.handlers:
            assert (
                handler.name in conversations_handlers_names
            ), f"Unexpected handler: {handler.name}"

    @mock.patch("opentelemetry.exporter.otlp.proto.grpc._log_exporter.OTLPLogExporter")
    def test_db_sqlite_logger_initialization(self, mock_otlp_exporter):

        mock_exporter_instance = Mock()
        mock_otlp_exporter.return_value = mock_exporter_instance

        # Now import your logging config - this will use the mocks
        # Import AFTER setting up mocks to ensure they're used
        import logging.config
        from src.agent.my_local_agent.logging_config import LOGGING_CONFIG

        # Apply the logging configuration
        logging.config.dictConfig(LOGGING_CONFIG)

        # Instantiate the conversations logger
        logger = logging.getLogger("db_sqlite_logger")

        logger.debug("Testing db_sqlite_logger initialization")

        conversations_handlers_names = ["db_sqlite_file_handler"]

        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, logging.Logger)

        # Assert that the logger is configured correctly
        assert logger.handlers is not None, "Logger is not configured correctly"
        assert logger.level == logging.DEBUG, "Logger level is not set to DEBUG"
        assert (
            logger.name == "db_sqlite_logger"
        ), "Logger name is not 'db_sqlite_logger'"

        for handler in logger.handlers:
            assert (
                handler.name in conversations_handlers_names
            ), f"Unexpected handler: {handler.name}"

    @mock.patch("opentelemetry.exporter.otlp.proto.grpc._log_exporter.OTLPLogExporter")
    def test_tools_logger_initialization(self, mock_otlp_exporter):

        mock_exporter_instance = Mock()
        mock_otlp_exporter.return_value = mock_exporter_instance

        # Now import your logging config - this will use the mocks
        # Import AFTER setting up mocks to ensure they're used
        import logging.config
        from src.agent.my_local_agent.logging_config import LOGGING_CONFIG

        # Apply the logging configuration
        logging.config.dictConfig(LOGGING_CONFIG)

        # Instantiate the conversations logger
        logger = logging.getLogger("tools_logger")

        logger.debug("Testing tools_logger initialization")

        conversations_handlers_names = ["tools_file_handler"]

        self.assertIsNotNone(logger)
        self.assertIsInstance(logger, logging.Logger)

        # Assert that the logger is configured correctly
        assert logger.handlers is not None, "Logger is not configured correctly"
        assert logger.level == logging.DEBUG, "Logger level is not set to DEBUG"
        assert logger.name == "tools_logger", "Logger name is not 'tools_logger'"

        for handler in logger.handlers:
            assert (
                handler.name in conversations_handlers_names
            ), f"Unexpected handler: {handler.name}"

    # Example of using mock to test logging calls
    @mock.patch("logging.Logger", autospec=True)
    def test_logging_messages(self, mock_logger):

        mock_logger.debug("This is a debug message")
        mock_logger.info("This is an info message")
        mock_logger.warning("This is a warning message")

        # Check if specific logging methods were called with expected arguments
        mock_logger.debug.assert_called_with("This is a debug message")
        mock_logger.info.assert_called_with("This is an info message")
        mock_logger.warning.assert_called_with("This is a warning message")

    @mock.patch("logging.Logger.debug")
    def test_debug_message(self, mock_debug):
        logger = logging.getLogger(__name__)
        logger.debug("Debug message")
        mock_debug.assert_called_once_with("Debug message")


if __name__ == "__main__":
    unittest.main()
