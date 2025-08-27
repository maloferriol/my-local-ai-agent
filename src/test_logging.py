#!/usr/bin/env python3
"""
Simple test script to verify OpenTelemetry logging is working.
"""

from loggers.logging_config import setup_opentelemetry, get_logger


def main():
    """Test OpenTelemetry logging setup."""
    # Set up OpenTelemetry logging
    setup_opentelemetry()

    # Get logger
    logger = get_logger(__name__)

    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Test with different modules
    test_logger = get_logger("test_module")
    test_logger.info("This is from test_module")

    print("Logging test completed. Check the console output above.")
    print("When you run the OpenTelemetry collector, these logs will be sent there.")


if __name__ == "__main__":
    main()
