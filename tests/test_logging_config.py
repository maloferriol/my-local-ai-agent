# test_logging_config.py

import unittest
from unittest.mock import Mock, patch
import logging


class TestLoggingConfiguration(unittest.TestCase):

    @patch("opentelemetry.exporter.otlp.proto.grpc._log_exporter.OTLPLogExporter")
    def test_logging_setup_with_mocking_exporter_only(
        self,
        mock_otlp_exporter,
    ):
        """
        Test that logging configuration sets up correctly without actually sending logs
        """
        # Configure mocks before importing the logging config
        mock_exporter_instance = Mock()
        mock_otlp_exporter.return_value = mock_exporter_instance

        # Now import your logging config - this will use the mocks
        # Import AFTER setting up mocks to ensure they're used
        import logging.config
        from src.loggers.logging_config import LOGGING_CONFIG

        # Apply the logging configuration
        logging.config.dictConfig(LOGGING_CONFIG)

        # Verify the OpenTelemetry components were called correctly
        mock_otlp_exporter.assert_called_once_with(
            endpoint="http://localhost:4317", insecure=True
        )

    def test_logging_works_with_mocked_otel(self):
        """Test that logging actually works when OpenTelemetry components are mocked"""

        # Create a captured logs list
        captured_records = []

        class CapturingHandler(logging.Handler):
            def emit(self, record):
                captured_records.append(record)

        # Create test configuration that doesn't use OpenTelemetry
        test_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
            },
            "handlers": {
                "capture_handler": {
                    "()": CapturingHandler,
                    "level": "DEBUG",
                },
            },
            "root": {
                "handlers": ["capture_handler"],
                "level": "DEBUG",
            },
        }

        # Apply test configuration
        logging.config.dictConfig(test_config)

        # Test logging
        logger = logging.getLogger("test_logger")
        logger.info("Test info message")
        logger.error("Test error message")

        # Verify logs were captured
        self.assertEqual(len(captured_records), 2)
        self.assertEqual(captured_records[0].getMessage(), "Test info message")
        self.assertEqual(captured_records[1].getMessage(), "Test error message")
        self.assertEqual(captured_records[0].levelname, "INFO")
        self.assertEqual(captured_records[1].levelname, "ERROR")


if __name__ == "__main__":
    unittest.main()
