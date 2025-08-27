#!/usr/bin/env python3
"""
CLI entry point for the AI agent application.
Handles command-line argument parsing and delegates execution to the agent.
"""

import argparse
import sys
import logging
from core.agent import Agent
from loggers.logging_config import setup_opentelemetry, get_logger

# Set up OpenTelemetry logging and get logger
setup_opentelemetry()
logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="My Local AI Agent - A local AI assistant powered by Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.cli.main                    # Start with default model
  python -m src.cli.main -m llama2:7b      # Use specific model
  python -m src.cli.main --no-stream       # Disable streaming
        """,
    )

    parser.add_argument(
        "-m",
        "--model",
        type=str,
        default="gpt-oss:20b",
        help="The Ollama model to use for the chat (default: %(default)s)",
    )

    parser.add_argument(
        "-s",
        "--stream",
        action="store_true",
        default=True,
        help="Enable streaming responses (default: enabled)",
    )

    parser.add_argument(
        "--no-stream",
        dest="stream",
        action="store_false",
        help="Disable streaming responses",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    parser.add_argument("--version", action="version", version="%(prog)s 1.0.0")

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    logger.info("Start")

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        print("Verbose logging enabled.")

    # Log startup information
    logger.info(
        "Starting AI agent with model: %s, streaming: %s", args.model, args.stream
    )

    if args.stream:
        print("Streaming is enabled.")
    else:
        print("Streaming is disabled.")

    try:
        # Create and run the agent
        agent = Agent(model=args.model, stream=args.stream)
        agent.run()

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
